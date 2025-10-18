"""
Quora System Implementation
Question and answer platform with reputation system
"""

import time
import threading
import uuid
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
import json
import redis
from enum import Enum
import statistics
import heapq

class ContentType(Enum):
    QUESTION = "question"
    ANSWER = "answer"
    COMMENT = "comment"

class VoteType(Enum):
    UP = "up"
    DOWN = "down"

class UserRole(Enum):
    USER = "user"
    MODERATOR = "moderator"
    ADMIN = "admin"

@dataclass
class User:
    """User data structure"""
    user_id: str
    username: str
    email: str
    created_at: datetime
    reputation: int = 0
    role: UserRole = UserRole.USER
    bio: str = ""
    location: str = ""
    website: str = ""
    is_active: bool = True
    last_activity: Optional[datetime] = None
    followers: Set[str] = field(default_factory=set)
    following: Set[str] = field(default_factory=set)
    interests: List[str] = field(default_factory=list)

@dataclass
class Question:
    """Question data structure"""
    question_id: str
    user_id: str
    title: str
    content: str
    created_at: datetime
    modified_at: datetime
    views: int = 0
    upvotes: int = 0
    downvotes: int = 0
    answer_count: int = 0
    tags: List[str] = field(default_factory=list)
    is_answered: bool = False
    is_closed: bool = False
    best_answer_id: Optional[str] = None
    followers: Set[str] = field(default_factory=set)

@dataclass
class Answer:
    """Answer data structure"""
    answer_id: str
    question_id: str
    user_id: str
    content: str
    created_at: datetime
    modified_at: datetime
    upvotes: int = 0
    downvotes: int = 0
    comment_count: int = 0
    is_accepted: bool = False
    is_helpful: bool = False

@dataclass
class Comment:
    """Comment data structure"""
    comment_id: str
    content_id: str  # question_id or answer_id
    content_type: ContentType
    user_id: str
    content: str
    created_at: datetime
    upvotes: int = 0
    downvotes: int = 0
    parent_comment_id: Optional[str] = None

@dataclass
class Vote:
    """Vote data structure"""
    vote_id: str
    content_id: str
    content_type: ContentType
    user_id: str
    vote_type: VoteType
    created_at: datetime

@dataclass
class Topic:
    """Topic data structure"""
    topic_id: str
    name: str
    description: str
    created_at: datetime
    follower_count: int = 0
    question_count: int = 0
    is_featured: bool = False

class QuoraSystem:
    """Question and answer platform system"""
    
    def __init__(self, redis_host='localhost', redis_port=6379, redis_db=0):
        self.redis_client = redis.Redis(host=redis_host, port=redis_port, db=redis_db, decode_responses=True)
        
        # Core data structures
        self.users = {}  # user_id -> User
        self.questions = {}  # question_id -> Question
        self.answers = {}  # answer_id -> Answer
        self.comments = {}  # comment_id -> Comment
        self.votes = {}  # vote_id -> Vote
        self.topics = {}  # topic_id -> Topic
        
        # Indexes for fast lookup
        self.questions_by_user = defaultdict(list)  # user_id -> List[question_id]
        self.answers_by_user = defaultdict(list)  # user_id -> List[answer_id]
        self.answers_by_question = defaultdict(list)  # question_id -> List[answer_id]
        self.comments_by_content = defaultdict(list)  # content_id -> List[comment_id]
        self.votes_by_content = defaultdict(list)  # content_id -> List[vote_id]
        self.questions_by_topic = defaultdict(set)  # topic_id -> Set[question_id]
        self.user_votes = defaultdict(dict)  # user_id -> {content_id -> vote_type}
        
        # Trending and recommendations
        self.trending_questions = []  # Heap of trending questions
        self.trending_topics = []  # Heap of trending topics
        self.user_recommendations = defaultdict(list)  # user_id -> List[question_id]
        
        # Threading
        self.lock = threading.RLock()
        self.trending_updater = threading.Thread(target=self._update_trending_content, daemon=True)
        self.trending_updater.start()
        
        # Configuration
        self.reputation_gains = {
            'question_upvote': 5,
            'answer_upvote': 10,
            'answer_accepted': 15,
            'answer_helpful': 5,
            'comment_upvote': 2
        }
        self.trending_window = 3600  # 1 hour
        self.update_interval = 300  # 5 minutes
    
    def create_user(self, user_id: str, username: str, email: str, bio: str = "", 
                   location: str = "", website: str = "", interests: List[str] = None) -> User:
        """Create a new user"""
        with self.lock:
            user = User(
                user_id=user_id,
                username=username,
                email=email,
                created_at=datetime.now(),
                bio=bio,
                location=location,
                website=website,
                interests=interests or []
            )
            self.users[user_id] = user
            self._persist_user(user)
            return user
    
    def follow_user(self, follower_id: str, followee_id: str) -> bool:
        """Follow a user"""
        with self.lock:
            if follower_id not in self.users or followee_id not in self.users:
                return False
            
            self.users[follower_id].following.add(followee_id)
            self.users[followee_id].followers.add(follower_id)
            
            # Update recommendations
            self._update_user_recommendations(follower_id)
            
            self._persist_user(self.users[follower_id])
            self._persist_user(self.users[followee_id])
            return True
    
    def unfollow_user(self, follower_id: str, followee_id: str) -> bool:
        """Unfollow a user"""
        with self.lock:
            if follower_id not in self.users or followee_id not in self.users:
                return False
            
            self.users[follower_id].following.discard(followee_id)
            self.users[followee_id].followers.discard(follower_id)
            
            self._persist_user(self.users[follower_id])
            self._persist_user(self.users[followee_id])
            return True
    
    def create_question(self, user_id: str, title: str, content: str, tags: List[str] = None) -> Question:
        """Create a new question"""
        with self.lock:
            question = Question(
                question_id=str(uuid.uuid4()),
                user_id=user_id,
                title=title,
                content=content,
                created_at=datetime.now(),
                modified_at=datetime.now(),
                tags=tags or []
            )
            
            self.questions[question.question_id] = question
            self.questions_by_user[user_id].append(question.question_id)
            
            # Add to topic indexes
            for tag in question.tags:
                if tag not in self.topics:
                    self._create_topic(tag)
                self.questions_by_topic[tag].add(question.question_id)
                self.topics[tag].question_count += 1
            
            # Update trending
            self._update_trending_questions(question)
            
            self._persist_question(question)
            return question
    
    def create_answer(self, user_id: str, question_id: str, content: str) -> Answer:
        """Create a new answer"""
        with self.lock:
            if question_id not in self.questions:
                raise ValueError("Question not found")
            
            answer = Answer(
                answer_id=str(uuid.uuid4()),
                question_id=question_id,
                user_id=user_id,
                content=content,
                created_at=datetime.now(),
                modified_at=datetime.now()
            )
            
            self.answers[answer.answer_id] = answer
            self.answers_by_user[user_id].append(answer.answer_id)
            self.answers_by_question[question_id].append(answer.answer_id)
            
            # Update question answer count
            self.questions[question_id].answer_count += 1
            
            self._persist_answer(answer)
            self._persist_question(self.questions[question_id])
            return answer
    
    def create_comment(self, user_id: str, content_id: str, content_type: ContentType, 
                      content: str, parent_comment_id: str = None) -> Comment:
        """Create a new comment"""
        with self.lock:
            comment = Comment(
                comment_id=str(uuid.uuid4()),
                content_id=content_id,
                content_type=content_type,
                user_id=user_id,
                content=content,
                created_at=datetime.now(),
                parent_comment_id=parent_comment_id
            )
            
            self.comments[comment.comment_id] = comment
            self.comments_by_content[content_id].append(comment.comment_id)
            
            # Update content comment count
            if content_type == ContentType.QUESTION and content_id in self.questions:
                pass  # Questions don't track comment count directly
            elif content_type == ContentType.ANSWER and content_id in self.answers:
                self.answers[content_id].comment_count += 1
                self._persist_answer(self.answers[content_id])
            
            self._persist_comment(comment)
            return comment
    
    def vote_content(self, user_id: str, content_id: str, content_type: ContentType, 
                    vote_type: VoteType) -> bool:
        """Vote on content"""
        with self.lock:
            # Check if user already voted
            if content_id in self.user_votes[user_id]:
                existing_vote = self.user_votes[user_id][content_id]
                if existing_vote == vote_type:
                    return False  # Already voted the same way
                
                # Remove existing vote
                self._remove_vote(user_id, content_id, existing_vote)
            
            # Create new vote
            vote = Vote(
                vote_id=str(uuid.uuid4()),
                content_id=content_id,
                content_type=content_type,
                user_id=user_id,
                vote_type=vote_type,
                created_at=datetime.now()
            )
            
            self.votes[vote.vote_id] = vote
            self.votes_by_content[content_id].append(vote.vote_id)
            self.user_votes[user_id][content_id] = vote_type
            
            # Update content vote counts
            self._update_content_votes(content_id, content_type, vote_type, 1)
            
            # Update user reputation
            self._update_user_reputation(user_id, content_type, vote_type)
            
            self._persist_vote(vote)
            return True
    
    def _remove_vote(self, user_id: str, content_id: str, vote_type: VoteType):
        """Remove a vote"""
        # Find and remove vote
        for vote_id, vote in self.votes.items():
            if (vote.user_id == user_id and 
                vote.content_id == content_id and 
                vote.vote_type == vote_type):
                del self.votes[vote_id]
                self.votes_by_content[content_id].remove(vote_id)
                break
        
        # Update content vote counts
        self._update_content_votes(content_id, ContentType.QUESTION, vote_type, -1)
        
        # Remove from user votes
        if content_id in self.user_votes[user_id]:
            del self.user_votes[user_id][content_id]
    
    def _update_content_votes(self, content_id: str, content_type: ContentType, 
                             vote_type: VoteType, delta: int):
        """Update content vote counts"""
        if content_type == ContentType.QUESTION and content_id in self.questions:
            question = self.questions[content_id]
            if vote_type == VoteType.UP:
                question.upvotes += delta
            else:
                question.downvotes += delta
            self._persist_question(question)
            
        elif content_type == ContentType.ANSWER and content_id in self.answers:
            answer = self.answers[content_id]
            if vote_type == VoteType.UP:
                answer.upvotes += delta
            else:
                answer.downvotes += delta
            self._persist_answer(answer)
            
        elif content_type == ContentType.COMMENT and content_id in self.comments:
            comment = self.comments[content_id]
            if vote_type == VoteType.UP:
                comment.upvotes += delta
            else:
                comment.downvotes += delta
            self._persist_comment(comment)
    
    def _update_user_reputation(self, user_id: str, content_type: ContentType, vote_type: VoteType):
        """Update user reputation based on votes"""
        if user_id not in self.users:
            return
        
        user = self.users[user_id]
        
        if vote_type == VoteType.UP:
            if content_type == ContentType.QUESTION:
                user.reputation += self.reputation_gains['question_upvote']
            elif content_type == ContentType.ANSWER:
                user.reputation += self.reputation_gains['answer_upvote']
            elif content_type == ContentType.COMMENT:
                user.reputation += self.reputation_gains['comment_upvote']
        
        self._persist_user(user)
    
    def accept_answer(self, question_id: str, answer_id: str, user_id: str) -> bool:
        """Accept an answer as the best answer"""
        with self.lock:
            if question_id not in self.questions or answer_id not in self.answers:
                return False
            
            question = self.questions[question_id]
            answer = self.answers[answer_id]
            
            # Check if user owns the question
            if question.user_id != user_id:
                return False
            
            # Mark answer as accepted
            answer.is_accepted = True
            question.is_answered = True
            question.best_answer_id = answer_id
            
            # Update answer author's reputation
            if answer.user_id in self.users:
                self.users[answer.user_id].reputation += self.reputation_gains['answer_accepted']
                self._persist_user(self.users[answer.user_id])
            
            self._persist_question(question)
            self._persist_answer(answer)
            return True
    
    def mark_answer_helpful(self, answer_id: str, user_id: str) -> bool:
        """Mark an answer as helpful"""
        with self.lock:
            if answer_id not in self.answers:
                return False
            
            answer = self.answers[answer_id]
            answer.is_helpful = True
            
            # Update answer author's reputation
            if answer.user_id in self.users:
                self.users[answer.user_id].reputation += self.reputation_gains['answer_helpful']
                self._persist_user(self.users[answer.user_id])
            
            self._persist_answer(answer)
            return True
    
    def follow_question(self, question_id: str, user_id: str) -> bool:
        """Follow a question for updates"""
        with self.lock:
            if question_id not in self.questions:
                return False
            
            self.questions[question_id].followers.add(user_id)
            self._persist_question(self.questions[question_id])
            return True
    
    def unfollow_question(self, question_id: str, user_id: str) -> bool:
        """Unfollow a question"""
        with self.lock:
            if question_id not in self.questions:
                return False
            
            self.questions[question_id].followers.discard(user_id)
            self._persist_question(self.questions[question_id])
            return True
    
    def get_question(self, question_id: str) -> Optional[Question]:
        """Get a question by ID"""
        return self.questions.get(question_id)
    
    def get_question_answers(self, question_id: str, sort_by: str = "votes") -> List[Answer]:
        """Get answers for a question"""
        if question_id not in self.answers_by_question:
            return []
        
        answer_ids = self.answers_by_question[question_id]
        answers = [self.answers[aid] for aid in answer_ids if aid in self.answers]
        
        if sort_by == "votes":
            answers.sort(key=lambda x: x.upvotes - x.downvotes, reverse=True)
        elif sort_by == "newest":
            answers.sort(key=lambda x: x.created_at, reverse=True)
        elif sort_by == "oldest":
            answers.sort(key=lambda x: x.created_at)
        
        return answers
    
    def get_question_comments(self, question_id: str) -> List[Comment]:
        """Get comments for a question"""
        if question_id not in self.comments_by_content:
            return []
        
        comment_ids = self.comments_by_content[question_id]
        comments = [self.comments[cid] for cid in comment_ids if cid in self.comments]
        comments.sort(key=lambda x: x.created_at)
        return comments
    
    def search_questions(self, query: str, tags: List[str] = None, limit: int = 50) -> List[Question]:
        """Search questions by query and tags"""
        with self.lock:
            results = []
            query_lower = query.lower()
            
            for question in self.questions.values():
                # Check if question matches query
                if (query_lower in question.title.lower() or 
                    query_lower in question.content.lower()):
                    
                    # Check if question matches tags
                    if tags is None or any(tag in question.tags for tag in tags):
                        results.append(question)
            
            # Sort by relevance (simplified)
            results.sort(key=lambda x: x.upvotes - x.downvotes, reverse=True)
            return results[:limit]
    
    def get_trending_questions(self, limit: int = 20) -> List[Question]:
        """Get trending questions"""
        with self.lock:
            # Filter recent questions
            cutoff_time = datetime.now() - timedelta(seconds=self.trending_window)
            trending = [q for q in self.trending_questions 
                       if q.created_at > cutoff_time]
            
            # Sort by trending score
            trending.sort(key=lambda x: self._calculate_trending_score(x), reverse=True)
            return trending[:limit]
    
    def get_trending_topics(self, limit: int = 20) -> List[Topic]:
        """Get trending topics"""
        with self.lock:
            # Filter recent topics
            cutoff_time = datetime.now() - timedelta(seconds=self.trending_window)
            trending = [t for t in self.trending_topics 
                       if t.created_at > cutoff_time]
            
            # Sort by follower count and question count
            trending.sort(key=lambda x: x.follower_count + x.question_count, reverse=True)
            return trending[:limit]
    
    def get_user_recommendations(self, user_id: str, limit: int = 20) -> List[Question]:
        """Get personalized question recommendations for user"""
        if user_id not in self.user_recommendations:
            return []
        
        question_ids = self.user_recommendations[user_id]
        questions = [self.questions[qid] for qid in question_ids if qid in self.questions]
        return questions[:limit]
    
    def _calculate_trending_score(self, question: Question) -> float:
        """Calculate trending score for a question"""
        # Simple trending algorithm based on votes, views, and recency
        age_hours = (datetime.now() - question.created_at).total_seconds() / 3600
        vote_score = question.upvotes - question.downvotes
        view_score = question.views * 0.1
        
        # Decay factor for recency
        recency_factor = max(0, 1 - age_hours / 24)
        
        return (vote_score + view_score) * recency_factor
    
    def _update_trending_questions(self, question: Question):
        """Update trending questions list"""
        self.trending_questions.append(question)
        
        # Keep only recent questions
        cutoff_time = datetime.now() - timedelta(seconds=self.trending_window)
        self.trending_questions = [q for q in self.trending_questions 
                                 if q.created_at > cutoff_time]
        
        # Sort by trending score
        self.trending_questions.sort(key=lambda x: self._calculate_trending_score(x), reverse=True)
        
        # Keep only top questions
        self.trending_questions = self.trending_questions[:100]
    
    def _update_user_recommendations(self, user_id: str):
        """Update user recommendations based on following and interests"""
        if user_id not in self.users:
            return
        
        user = self.users[user_id]
        recommendations = []
        
        # Get questions from followed users
        for followee_id in user.following:
            if followee_id in self.questions_by_user:
                for question_id in self.questions_by_user[followee_id]:
                    if question_id in self.questions:
                        recommendations.append(question_id)
        
        # Get questions matching user interests
        for interest in user.interests:
            if interest in self.questions_by_topic:
                for question_id in self.questions_by_topic[interest]:
                    if question_id in self.questions:
                        recommendations.append(question_id)
        
        # Remove duplicates and limit
        recommendations = list(set(recommendations))[:50]
        self.user_recommendations[user_id] = recommendations
    
    def _create_topic(self, topic_name: str):
        """Create a new topic"""
        topic = Topic(
            topic_id=topic_name,
            name=topic_name,
            description=f"Questions about {topic_name}",
            created_at=datetime.now()
        )
        self.topics[topic_name] = topic
        self._persist_topic(topic)
    
    def _update_trending_content(self):
        """Update trending content in background"""
        while True:
            try:
                time.sleep(self.update_interval)
                
                with self.lock:
                    # Update trending questions
                    for question in self.questions.values():
                        self._update_trending_questions(question)
                    
                    # Update trending topics
                    for topic in self.topics.values():
                        self._update_trending_topics(topic)
                    
                    # Update user recommendations
                    for user_id in self.users:
                        self._update_user_recommendations(user_id)
                
            except Exception as e:
                print(f"Error in trending updater: {e}")
    
    def _update_trending_topics(self, topic: Topic):
        """Update trending topics list"""
        self.trending_topics.append(topic)
        
        # Keep only recent topics
        cutoff_time = datetime.now() - timedelta(seconds=self.trending_window)
        self.trending_topics = [t for t in self.trending_topics 
                              if t.created_at > cutoff_time]
        
        # Sort by popularity
        self.trending_topics.sort(key=lambda x: x.follower_count + x.question_count, reverse=True)
        
        # Keep only top topics
        self.trending_topics = self.trending_topics[:50]
    
    def _persist_user(self, user: User):
        """Persist user to Redis"""
        user_data = {
            'user_id': user.user_id,
            'username': user.username,
            'email': user.email,
            'created_at': user.created_at.isoformat(),
            'reputation': str(user.reputation),
            'role': user.role.value,
            'bio': user.bio,
            'location': user.location,
            'website': user.website,
            'is_active': str(user.is_active),
            'last_activity': user.last_activity.isoformat() if user.last_activity else None,
            'followers': json.dumps(list(user.followers)),
            'following': json.dumps(list(user.following)),
            'interests': json.dumps(user.interests)
        }
        self.redis_client.hset(f"user:{user.user_id}", mapping=user_data)
    
    def _persist_question(self, question: Question):
        """Persist question to Redis"""
        question_data = {
            'question_id': question.question_id,
            'user_id': question.user_id,
            'title': question.title,
            'content': question.content,
            'created_at': question.created_at.isoformat(),
            'modified_at': question.modified_at.isoformat(),
            'views': str(question.views),
            'upvotes': str(question.upvotes),
            'downvotes': str(question.downvotes),
            'answer_count': str(question.answer_count),
            'tags': json.dumps(question.tags),
            'is_answered': str(question.is_answered),
            'is_closed': str(question.is_closed),
            'best_answer_id': question.best_answer_id or '',
            'followers': json.dumps(list(question.followers))
        }
        self.redis_client.hset(f"question:{question.question_id}", mapping=question_data)
    
    def _persist_answer(self, answer: Answer):
        """Persist answer to Redis"""
        answer_data = {
            'answer_id': answer.answer_id,
            'question_id': answer.question_id,
            'user_id': answer.user_id,
            'content': answer.content,
            'created_at': answer.created_at.isoformat(),
            'modified_at': answer.modified_at.isoformat(),
            'upvotes': str(answer.upvotes),
            'downvotes': str(answer.downvotes),
            'comment_count': str(answer.comment_count),
            'is_accepted': str(answer.is_accepted),
            'is_helpful': str(answer.is_helpful)
        }
        self.redis_client.hset(f"answer:{answer.answer_id}", mapping=answer_data)
    
    def _persist_comment(self, comment: Comment):
        """Persist comment to Redis"""
        comment_data = {
            'comment_id': comment.comment_id,
            'content_id': comment.content_id,
            'content_type': comment.content_type.value,
            'user_id': comment.user_id,
            'content': comment.content,
            'created_at': comment.created_at.isoformat(),
            'upvotes': str(comment.upvotes),
            'downvotes': str(comment.downvotes),
            'parent_comment_id': comment.parent_comment_id or ''
        }
        self.redis_client.hset(f"comment:{comment.comment_id}", mapping=comment_data)
    
    def _persist_vote(self, vote: Vote):
        """Persist vote to Redis"""
        vote_data = {
            'vote_id': vote.vote_id,
            'content_id': vote.content_id,
            'content_type': vote.content_type.value,
            'user_id': vote.user_id,
            'vote_type': vote.vote_type.value,
            'created_at': vote.created_at.isoformat()
        }
        self.redis_client.hset(f"vote:{vote.vote_id}", mapping=vote_data)
    
    def _persist_topic(self, topic: Topic):
        """Persist topic to Redis"""
        topic_data = {
            'topic_id': topic.topic_id,
            'name': topic.name,
            'description': topic.description,
            'created_at': topic.created_at.isoformat(),
            'follower_count': str(topic.follower_count),
            'question_count': str(topic.question_count),
            'is_featured': str(topic.is_featured)
        }
        self.redis_client.hset(f"topic:{topic.topic_id}", mapping=topic_data)
    
    def get_system_stats(self) -> Dict:
        """Get system statistics"""
        with self.lock:
            total_votes = sum(len(votes) for votes in self.votes_by_content.values())
            total_comments = sum(len(comments) for comments in self.comments_by_content.values())
            
            return {
                'total_users': len(self.users),
                'total_questions': len(self.questions),
                'total_answers': len(self.answers),
                'total_comments': len(self.comments),
                'total_votes': total_votes,
                'total_topics': len(self.topics),
                'average_reputation': statistics.mean([user.reputation for user in self.users.values()]) if self.users else 0,
                'questions_with_answers': len([q for q in self.questions.values() if q.answer_count > 0]),
                'answered_questions': len([q for q in self.questions.values() if q.is_answered])
            }


# Example usage and testing
if __name__ == "__main__":
    # Initialize system
    quora = QuoraSystem()
    
    # Create users
    user1 = quora.create_user("user1", "alice", "alice@example.com", "Software Engineer", "San Francisco", interests=["programming", "tech"])
    user2 = quora.create_user("user2", "bob", "bob@example.com", "Data Scientist", "New York", interests=["data", "ai"])
    
    # Follow users
    quora.follow_user("user1", "user2")
    
    # Create question
    question = quora.create_question("user1", "How to learn Python?", "I want to learn Python programming. What's the best way to start?", ["python", "programming"])
    
    # Create answer
    answer = quora.create_answer("user2", question.question_id, "Start with Python basics and practice regularly.")
    
    # Vote on content
    quora.vote_content("user1", question.question_id, ContentType.QUESTION, VoteType.UP)
    quora.vote_content("user1", answer.answer_id, ContentType.ANSWER, VoteType.UP)
    
    # Accept answer
    quora.accept_answer(question.question_id, answer.answer_id, "user1")
    
    # Get question and answers
    question_answers = quora.get_question_answers(question.question_id)
    print(f"Question: {question.title}")
    print(f"Answers: {len(question_answers)}")
    
    # Get trending questions
    trending = quora.get_trending_questions()
    print(f"Trending questions: {len(trending)}")
    
    # Get system stats
    stats = quora.get_system_stats()
    print(f"System stats: {stats}")

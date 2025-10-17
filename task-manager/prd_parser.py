#!/usr/bin/env python3
"""
PRD Parser - Extracts tasks and metadata from Product Requirements Documents.

This module parses markdown-formatted PRD files and extracts:
- Project metadata
- Implementation phases
- Tasks with priorities and dependencies
- Feature checklists
"""

import re
import json
import yaml
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum


class Priority(Enum):
    """Task priority levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


@dataclass
class Task:
    """Represents a single task extracted from the PRD."""
    id: str
    title: str
    phase: str
    priority: str
    status: str = TaskStatus.PENDING.value
    dependencies: List[str] = None
    section: str = ""
    line_number: int = 0

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary."""
        return asdict(self)


@dataclass
class Phase:
    """Represents an implementation phase."""
    name: str
    priority: str
    tasks: List[Task]

    def to_dict(self) -> Dict[str, Any]:
        """Convert phase to dictionary."""
        return {
            'name': self.name,
            'priority': self.priority,
            'tasks': [task.to_dict() for task in self.tasks]
        }


@dataclass
class PRDMetadata:
    """Metadata extracted from the PRD."""
    title: str
    sections: List[str]
    total_tasks: int
    total_phases: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary."""
        return asdict(self)


class PRDParser:
    """Parser for Product Requirements Documents in Markdown format."""

    def __init__(self, prd_file_path: str):
        """
        Initialize the PRD parser.

        Args:
            prd_file_path: Path to the PRD markdown file
        """
        self.prd_file_path = prd_file_path
        self.content = ""
        self.lines = []
        self.tasks = []
        self.phases = []
        self.metadata = None

    def load(self) -> None:
        """Load the PRD file content."""
        with open(self.prd_file_path, 'r', encoding='utf-8') as f:
            self.content = f.read()
            self.lines = self.content.split('\n')

    def parse(self) -> Dict[str, Any]:
        """
        Parse the PRD and extract all information.

        Returns:
            Dictionary containing metadata, phases, and tasks
        """
        self.load()
        self._extract_metadata()
        self._extract_phases()
        self._extract_feature_tasks()

        return {
            'metadata': self.metadata.to_dict() if self.metadata else {},
            'phases': [phase.to_dict() for phase in self.phases],
            'tasks': [task.to_dict() for task in self.tasks]
        }

    def _extract_metadata(self) -> None:
        """Extract metadata from the PRD."""
        title = ""
        sections = []

        # Extract title (first H1 heading)
        for line in self.lines:
            if line.startswith('# '):
                title = line[2:].strip()
                break

        # Extract section headings
        for line in self.lines:
            if re.match(r'^##\s+\d+\.', line):
                sections.append(line.strip())

        self.metadata = PRDMetadata(
            title=title,
            sections=sections,
            total_tasks=0,  # Will be updated after parsing
            total_phases=0   # Will be updated after parsing
        )

    def _extract_phases(self) -> None:
        """Extract implementation phases and their tasks."""
        current_phase = None
        current_priority = Priority.MEDIUM.value
        phase_tasks = []
        task_counter = 0

        in_phase_section = False

        for line_num, line in enumerate(self.lines, 1):
            # Detect phase section - match any section with "Implementation Phases"
            if re.match(r'^##\s+\d+\.\s+Implementation Phases', line):
                in_phase_section = True
                continue

            # Exit phase section
            if in_phase_section and re.match(r'^##\s+\d+\.', line) and 'Implementation Phases' not in line:
                # Save last phase
                if current_phase:
                    self.phases.append(Phase(
                        name=current_phase,
                        priority=current_priority,
                        tasks=phase_tasks.copy()
                    ))
                break

            if not in_phase_section:
                continue

            # Detect phase heading (### Phase X: Name (Priority: Level))
            phase_match = re.match(r'^###\s+Phase\s+\d+:\s+(.+?)\s*\(Priority:\s*(\w+)\)', line)
            if phase_match:
                # Save previous phase
                if current_phase:
                    self.phases.append(Phase(
                        name=current_phase,
                        priority=current_priority,
                        tasks=phase_tasks.copy()
                    ))
                    phase_tasks = []

                current_phase = phase_match.group(1).strip()
                current_priority = phase_match.group(2).lower()
                continue

            # Extract tasks from checklist items
            task_match = re.match(r'^-\s+\[\s*\]\s+(.+)$', line)
            if task_match and current_phase:
                task_counter += 1
                task_title = task_match.group(1).strip()

                task = Task(
                    id=f"phase_{len(self.phases) + 1}_task_{len(phase_tasks) + 1}",
                    title=task_title,
                    phase=current_phase,
                    priority=current_priority,
                    status=TaskStatus.PENDING.value,
                    section=f"Phase {len(self.phases) + 1}",
                    line_number=line_num
                )
                phase_tasks.append(task)
                self.tasks.append(task)

        # Save last phase
        if current_phase:
            self.phases.append(Phase(
                name=current_phase,
                priority=current_priority,
                tasks=phase_tasks.copy()
            ))

        # Update metadata
        if self.metadata:
            self.metadata.total_phases = len(self.phases)
            self.metadata.total_tasks = len(self.tasks)

    def _extract_feature_tasks(self) -> None:
        """Extract feature requirement tasks."""
        in_features_section = False
        current_feature = ""
        task_counter = len(self.tasks)

        for line_num, line in enumerate(self.lines, 1):
            # Detect feature requirements section
            if '## 4. Feature Requirements' in line:
                in_features_section = True
                continue

            # Exit feature section
            if in_features_section and re.match(r'^##\s+\d+\.', line) and 'Feature Requirements' not in line:
                break

            if not in_features_section:
                continue

            # Detect feature subsection
            if line.startswith('### 4.'):
                current_feature = line.split(' ', 2)[2].strip() if len(line.split(' ', 2)) > 2 else ""
                continue

            # Extract feature tasks
            task_match = re.match(r'^-\s+\[\s*\]\s+(.+)$', line)
            if task_match and current_feature:
                task_counter += 1
                task_title = task_match.group(1).strip()

                task = Task(
                    id=f"feature_task_{task_counter}",
                    title=task_title,
                    phase="Feature Implementation",
                    priority=Priority.HIGH.value,
                    status=TaskStatus.PENDING.value,
                    section=current_feature,
                    line_number=line_num
                )
                self.tasks.append(task)

        # Update total tasks
        if self.metadata:
            self.metadata.total_tasks = len(self.tasks)

    def save_to_json(self, output_file: str) -> None:
        """
        Save parsed data to JSON file.

        Args:
            output_file: Path to output JSON file
        """
        data = self.parse() if not self.tasks else {
            'metadata': self.metadata.to_dict() if self.metadata else {},
            'phases': [phase.to_dict() for phase in self.phases],
            'tasks': [task.to_dict() for task in self.tasks]
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

    def save_to_yaml(self, output_file: str) -> None:
        """
        Save parsed data to YAML file.

        Args:
            output_file: Path to output YAML file
        """
        data = self.parse() if not self.tasks else {
            'metadata': self.metadata.to_dict() if self.metadata else {},
            'phases': [phase.to_dict() for phase in self.phases],
            'tasks': [task.to_dict() for task in self.tasks]
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)


def parse_prd(prd_file_path: str) -> Dict[str, Any]:
    """
    Convenience function to parse a PRD file.

    Args:
        prd_file_path: Path to PRD markdown file

    Returns:
        Dictionary containing metadata, phases, and tasks
    """
    parser = PRDParser(prd_file_path)
    return parser.parse()


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Parse PRD markdown file and extract tasks')
    parser.add_argument('prd_file', help='Path to PRD markdown file')
    parser.add_argument('--output', '-o', help='Output file (JSON or YAML)')
    parser.add_argument('--format', '-f', choices=['json', 'yaml'], default='json',
                       help='Output format (default: json)')

    args = parser.parse_args()

    prd_parser = PRDParser(args.prd_file)
    result = prd_parser.parse()

    if args.output:
        if args.format == 'json':
            prd_parser.save_to_json(args.output)
        else:
            prd_parser.save_to_yaml(args.output)
        print(f"Parsed PRD saved to {args.output}")
    else:
        # Print to stdout
        print(json.dumps(result, indent=2))

    print(f"\nSummary:")
    print(f"  Title: {result['metadata']['title']}")
    print(f"  Total Phases: {result['metadata']['total_phases']}")
    print(f"  Total Tasks: {result['metadata']['total_tasks']}")

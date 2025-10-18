"""
Performance Benchmarking for All Algorithms
Comprehensive performance testing and optimization
"""

import unittest
import time
import psutil
import gc
import threading
import concurrent.futures
from unittest.mock import Mock, patch
from pathlib import Path
import sys
import statistics
import json
from datetime import datetime

# Add project paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "task-manager"))
sys.path.insert(0, str(project_root / "task-master"))

from prd_parser import PRDParser, Task, Phase, TaskStatus, Priority, PRDMetadata
from task_manager import TaskManager
from task_master import TaskMaster, TaskExecutor

class PerformanceBenchmark:
    """Performance benchmarking utility"""
    
    def __init__(self):
        self.results = {}
        self.start_time = None
        self.start_memory = None
        self.start_cpu = None
    
    def start_benchmark(self):
        """Start performance benchmark"""
        self.start_time = time.time()
        self.start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        self.start_cpu = psutil.Process().cpu_percent()
    
    def end_benchmark(self, test_name):
        """End performance benchmark"""
        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        end_cpu = psutil.Process().cpu_percent()
        
        execution_time = end_time - self.start_time
        memory_usage = end_memory - self.start_memory
        cpu_usage = end_cpu - self.start_cpu
        
        self.results[test_name] = {
            'execution_time': execution_time,
            'memory_usage': memory_usage,
            'cpu_usage': cpu_usage,
            'timestamp': datetime.now().isoformat()
        }
        
        return self.results[test_name]
    
    def get_summary(self):
        """Get performance summary"""
        if not self.results:
            return {}
        
        total_time = sum(result['execution_time'] for result in self.results.values())
        total_memory = sum(result['memory_usage'] for result in self.results.values())
        total_cpu = sum(result['cpu_usage'] for result in self.results.values())
        
        return {
            'total_tests': len(self.results),
            'total_execution_time': total_time,
            'total_memory_usage': total_memory,
            'total_cpu_usage': total_cpu,
            'average_execution_time': total_time / len(self.results),
            'average_memory_usage': total_memory / len(self.results),
            'average_cpu_usage': total_cpu / len(self.results),
            'results': self.results
        }

class TestPRDParserPerformance(unittest.TestCase):
    """Performance tests for PRD Parser"""
    
    def setUp(self):
        self.parser = PRDParser()
        self.benchmark = PerformanceBenchmark()
        
        # Create large PRD content for performance testing
        self.large_prd_content = """# Large Performance Test PRD

## 1. Executive Summary
This is a large PRD for performance testing.

## 2. System Architecture
- Component 1
- Component 2
- Component 3

## 3. Feature Requirements

### 3.1 Feature Group 1
- [ ] Feature 1.1
- [ ] Feature 1.2
- [ ] Feature 1.3
- [ ] Feature 1.4
- [ ] Feature 1.5

### 3.2 Feature Group 2
- [ ] Feature 2.1
- [ ] Feature 2.2
- [ ] Feature 2.3
- [ ] Feature 2.4
- [ ] Feature 2.5

### 3.3 Feature Group 3
- [ ] Feature 3.1
- [ ] Feature 3.2
- [ ] Feature 3.3
- [ ] Feature 3.4
- [ ] Feature 3.5

## 4. Implementation Phases

### Phase 1: Setup
- [ ] Task 1.1
- [ ] Task 1.2
- [ ] Task 1.3
- [ ] Task 1.4
- [ ] Task 1.5

### Phase 2: Development
- [ ] Task 2.1
- [ ] Task 2.2
- [ ] Task 2.3
- [ ] Task 2.4
- [ ] Task 2.5

### Phase 3: Testing
- [ ] Task 3.1
- [ ] Task 3.2
- [ ] Task 3.3
- [ ] Task 3.4
- [ ] Task 3.5

### Phase 4: Deployment
- [ ] Task 4.1
- [ ] Task 4.2
- [ ] Task 4.3
- [ ] Task 4.4
- [ ] Task 4.5

### Phase 5: Maintenance
- [ ] Task 5.1
- [ ] Task 5.2
- [ ] Task 5.3
- [ ] Task 5.4
- [ ] Task 5.5
"""
        
        # Create very large PRD content
        self.very_large_prd_content = self.large_prd_content * 100
    
    def test_parsing_performance_small(self):
        """Test parsing performance with small content"""
        self.benchmark.start_benchmark()
        
        result = self.parser.parse_prd_content(self.large_prd_content)
        
        benchmark_result = self.benchmark.end_benchmark("parsing_small")
        
        self.assertIsNotNone(result)
        self.assertLess(benchmark_result['execution_time'], 0.1)  # Less than 100ms
        self.assertLess(benchmark_result['memory_usage'], 10)  # Less than 10MB
    
    def test_parsing_performance_large(self):
        """Test parsing performance with large content"""
        self.benchmark.start_benchmark()
        
        result = self.parser.parse_prd_content(self.very_large_prd_content)
        
        benchmark_result = self.benchmark.end_benchmark("parsing_large")
        
        self.assertIsNotNone(result)
        self.assertLess(benchmark_result['execution_time'], 1.0)  # Less than 1 second
        self.assertLess(benchmark_result['memory_usage'], 100)  # Less than 100MB
    
    def test_metadata_extraction_performance(self):
        """Test metadata extraction performance"""
        self.benchmark.start_benchmark()
        
        metadata = self.parser.extract_metadata(self.very_large_prd_content)
        
        benchmark_result = self.benchmark.end_benchmark("metadata_extraction")
        
        self.assertIsInstance(metadata, PRDMetadata)
        self.assertLess(benchmark_result['execution_time'], 0.5)  # Less than 500ms
    
    def test_task_extraction_performance(self):
        """Test task extraction performance"""
        self.benchmark.start_benchmark()
        
        tasks = self.parser.extract_tasks(self.very_large_prd_content)
        
        benchmark_result = self.benchmark.end_benchmark("task_extraction")
        
        self.assertIsInstance(tasks, list)
        self.assertGreater(len(tasks), 0)
        self.assertLess(benchmark_result['execution_time'], 0.5)  # Less than 500ms
    
    def test_phase_extraction_performance(self):
        """Test phase extraction performance"""
        self.benchmark.start_benchmark()
        
        phases = self.parser.extract_phases(self.very_large_prd_content)
        
        benchmark_result = self.benchmark.end_benchmark("phase_extraction")
        
        self.assertIsInstance(phases, list)
        self.assertGreater(len(phases), 0)
        self.assertLess(benchmark_result['execution_time'], 0.5)  # Less than 500ms
    
    def test_concurrent_parsing_performance(self):
        """Test concurrent parsing performance"""
        def parse_content():
            return self.parser.parse_prd_content(self.large_prd_content)
        
        self.benchmark.start_benchmark()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(parse_content) for _ in range(100)]
            results = [future.result() for future in futures]
        
        benchmark_result = self.benchmark.end_benchmark("concurrent_parsing")
        
        self.assertEqual(len(results), 100)
        for result in results:
            self.assertIsNotNone(result)
        
        self.assertLess(benchmark_result['execution_time'], 2.0)  # Less than 2 seconds
    
    def test_memory_efficiency(self):
        """Test memory efficiency during parsing"""
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        # Parse large content multiple times
        for _ in range(100):
            result = self.parser.parse_prd_content(self.very_large_prd_content)
            del result
        
        gc.collect()
        
        final_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable
        self.assertLess(memory_increase, 50)  # Less than 50MB increase


class TestTaskManagerPerformance(unittest.TestCase):
    """Performance tests for Task Manager"""
    
    def setUp(self):
        self.manager = TaskManager()
        self.benchmark = PerformanceBenchmark()
    
    def test_task_creation_performance(self):
        """Test task creation performance"""
        self.benchmark.start_benchmark()
        
        # Create many tasks
        for i in range(10000):
            task = Task(
                id=f"perf-{i}",
                title=f"Performance Task {i}",
                description=f"Description {i}",
                priority=Priority.MEDIUM,
                status=TaskStatus.PENDING
            )
            self.manager.add_task(task)
        
        benchmark_result = self.benchmark.end_benchmark("task_creation")
        
        self.assertEqual(len(self.manager.tasks), 10000)
        self.assertLess(benchmark_result['execution_time'], 2.0)  # Less than 2 seconds
        self.assertLess(benchmark_result['memory_usage'], 100)  # Less than 100MB
    
    def test_task_filtering_performance(self):
        """Test task filtering performance"""
        # Create many tasks
        for i in range(10000):
            priority = Priority.HIGH if i % 3 == 0 else Priority.MEDIUM if i % 3 == 1 else Priority.LOW
            status = TaskStatus.PENDING if i % 2 == 0 else TaskStatus.IN_PROGRESS
            
            task = Task(
                id=f"filter-{i}",
                title=f"Filter Task {i}",
                description=f"Description {i}",
                priority=priority,
                status=status
            )
            self.manager.add_task(task)
        
        self.benchmark.start_benchmark()
        
        # Test filtering operations
        high_priority_tasks = self.manager.get_tasks_by_priority(Priority.HIGH)
        pending_tasks = self.manager.get_tasks_by_status(TaskStatus.PENDING)
        all_tasks = self.manager.get_all_tasks()
        
        benchmark_result = self.benchmark.end_benchmark("task_filtering")
        
        self.assertGreater(len(high_priority_tasks), 0)
        self.assertGreater(len(pending_tasks), 0)
        self.assertEqual(len(all_tasks), 10000)
        self.assertLess(benchmark_result['execution_time'], 1.0)  # Less than 1 second
    
    def test_task_status_update_performance(self):
        """Test task status update performance"""
        # Create many tasks
        for i in range(10000):
            task = Task(
                id=f"status-{i}",
                title=f"Status Task {i}",
                description=f"Description {i}",
                priority=Priority.MEDIUM,
                status=TaskStatus.PENDING
            )
            self.manager.add_task(task)
        
        self.benchmark.start_benchmark()
        
        # Update status of all tasks
        for task in self.manager.tasks.values():
            self.manager.update_task_status(task.id, TaskStatus.IN_PROGRESS)
        
        benchmark_result = self.benchmark.end_benchmark("task_status_update")
        
        in_progress_tasks = self.manager.get_tasks_by_status(TaskStatus.IN_PROGRESS)
        self.assertEqual(len(in_progress_tasks), 10000)
        self.assertLess(benchmark_result['execution_time'], 1.0)  # Less than 1 second
    
    def test_dependency_management_performance(self):
        """Test dependency management performance"""
        # Create many tasks
        for i in range(1000):
            task = Task(
                id=f"dep-{i}",
                title=f"Dependency Task {i}",
                description=f"Description {i}",
                priority=Priority.MEDIUM,
                status=TaskStatus.PENDING
            )
            self.manager.add_task(task)
        
        self.benchmark.start_benchmark()
        
        # Add dependencies
        for i in range(1, 1000):
            self.manager.add_dependency(f"dep-{i}", f"dep-{i-1}")
        
        # Test dependency queries
        for i in range(100):
            deps = self.manager.get_task_dependencies(f"dep-{i}")
            dependents = self.manager.get_dependents(f"dep-{i}")
        
        benchmark_result = self.benchmark.end_benchmark("dependency_management")
        
        self.assertLess(benchmark_result['execution_time'], 1.0)  # Less than 1 second
    
    def test_progress_reporting_performance(self):
        """Test progress reporting performance"""
        # Create many tasks with different statuses
        for i in range(10000):
            status = TaskStatus.PENDING if i % 3 == 0 else TaskStatus.IN_PROGRESS if i % 3 == 1 else TaskStatus.COMPLETED
            
            task = Task(
                id=f"progress-{i}",
                title=f"Progress Task {i}",
                description=f"Description {i}",
                priority=Priority.MEDIUM,
                status=status
            )
            self.manager.add_task(task)
        
        self.benchmark.start_benchmark()
        
        # Generate progress reports
        for _ in range(100):
            progress = self.manager.get_progress_report()
        
        benchmark_result = self.benchmark.end_benchmark("progress_reporting")
        
        self.assertLess(benchmark_result['execution_time'], 1.0)  # Less than 1 second
    
    def test_data_persistence_performance(self):
        """Test data persistence performance"""
        # Create many tasks
        for i in range(10000):
            task = Task(
                id=f"persist-{i}",
                title=f"Persistence Task {i}",
                description=f"Description {i}",
                priority=Priority.MEDIUM,
                status=TaskStatus.PENDING
            )
            self.manager.add_task(task)
        
        self.benchmark.start_benchmark()
        
        # Save and load tasks
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            try:
                self.manager.save_tasks(f.name)
                
                new_manager = TaskManager()
                new_manager.load_tasks(f.name)
                
                self.assertEqual(len(new_manager.tasks), 10000)
            finally:
                import os
                os.unlink(f.name)
        
        benchmark_result = self.benchmark.end_benchmark("data_persistence")
        
        self.assertLess(benchmark_result['execution_time'], 2.0)  # Less than 2 seconds
    
    def test_concurrent_operations_performance(self):
        """Test concurrent operations performance"""
        def add_tasks(start, count):
            for i in range(start, start + count):
                task = Task(
                    id=f"concurrent-{i}",
                    title=f"Concurrent Task {i}",
                    description=f"Description {i}",
                    priority=Priority.MEDIUM,
                    status=TaskStatus.PENDING
                )
                self.manager.add_task(task)
        
        self.benchmark.start_benchmark()
        
        # Run concurrent operations
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            for i in range(10):
                future = executor.submit(add_tasks, i * 1000, 1000)
                futures.append(future)
            
            concurrent.futures.wait(futures)
        
        benchmark_result = self.benchmark.end_benchmark("concurrent_operations")
        
        self.assertEqual(len(self.manager.tasks), 10000)
        self.assertLess(benchmark_result['execution_time'], 2.0)  # Less than 2 seconds
    
    def test_memory_efficiency(self):
        """Test memory efficiency"""
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        # Create many managers and tasks
        managers = []
        for i in range(100):
            manager = TaskManager()
            for j in range(1000):
                task = Task(
                    id=f"mem-{i}-{j}",
                    title=f"Memory Task {i}-{j}",
                    description=f"Description {i}-{j}",
                    priority=Priority.MEDIUM,
                    status=TaskStatus.PENDING
                )
                manager.add_task(task)
            managers.append(manager)
        
        # Clean up
        del managers
        gc.collect()
        
        final_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable
        self.assertLess(memory_increase, 200)  # Less than 200MB increase


class TestTaskMasterPerformance(unittest.TestCase):
    """Performance tests for Task Master"""
    
    def setUp(self):
        self.executor = TaskExecutor()
        self.master = TaskMaster(self.executor)
        self.benchmark = PerformanceBenchmark()
    
    def test_task_execution_performance(self):
        """Test task execution performance"""
        # Create many tasks
        tasks = [
            Task(
                id=f"exec-{i}",
                title=f"Execution Task {i}",
                description=f"Description {i}",
                priority=Priority.MEDIUM,
                status=TaskStatus.PENDING
            )
            for i in range(1000)
        ]
        
        self.benchmark.start_benchmark()
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout=b'Success', stderr=b'')
            
            for task in tasks:
                result = self.master.execute_task(task, {})
                self.assertTrue(result.success)
        
        benchmark_result = self.benchmark.end_benchmark("task_execution")
        
        self.assertLess(benchmark_result['execution_time'], 2.0)  # Less than 2 seconds
    
    def test_phase_execution_performance(self):
        """Test phase execution performance"""
        # Create phase with many tasks
        tasks = [
            Task(
                id=f"phase-{i}",
                title=f"Phase Task {i}",
                description=f"Description {i}",
                priority=Priority.MEDIUM,
                status=TaskStatus.PENDING
            )
            for i in range(1000)
        ]
        
        phase = Phase("perf-phase", "Performance Phase", "Phase for performance testing", tasks)
        
        self.benchmark.start_benchmark()
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout=b'Success', stderr=b'')
            
            result = self.master.execute_phase(phase, {})
            self.assertTrue(result.success)
        
        benchmark_result = self.benchmark.end_benchmark("phase_execution")
        
        self.assertLess(benchmark_result['execution_time'], 3.0)  # Less than 3 seconds
    
    def test_concurrent_execution_performance(self):
        """Test concurrent execution performance"""
        def execute_task(task):
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = Mock(returncode=0, stdout=b'Success', stderr=b'')
                return self.master.execute_task(task, {})
        
        # Create many tasks
        tasks = [
            Task(
                id=f"concurrent-exec-{i}",
                title=f"Concurrent Execution Task {i}",
                description=f"Description {i}",
                priority=Priority.MEDIUM,
                status=TaskStatus.PENDING
            )
            for i in range(1000)
        ]
        
        self.benchmark.start_benchmark()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(execute_task, task) for task in tasks]
            results = [future.result() for future in futures]
        
        benchmark_result = self.benchmark.end_benchmark("concurrent_execution")
        
        self.assertEqual(len(results), 1000)
        for result in results:
            self.assertTrue(result.success)
        
        self.assertLess(benchmark_result['execution_time'], 5.0)  # Less than 5 seconds
    
    def test_memory_efficiency(self):
        """Test memory efficiency during execution"""
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        # Execute many tasks
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout=b'Success', stderr=b'')
            
            for i in range(10000):
                task = Task(
                    id=f"mem-exec-{i}",
                    title=f"Memory Execution Task {i}",
                    description=f"Description {i}",
                    priority=Priority.MEDIUM,
                    status=TaskStatus.PENDING
                )
                result = self.master.execute_task(task, {})
                del result
        
        gc.collect()
        
        final_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable
        self.assertLess(memory_increase, 100)  # Less than 100MB increase


class TestSystemPerformance(unittest.TestCase):
    """System-wide performance tests"""
    
    def setUp(self):
        self.parser = PRDParser()
        self.manager = TaskManager()
        self.executor = TaskExecutor()
        self.master = TaskMaster(self.executor)
        self.benchmark = PerformanceBenchmark()
        
        # Create large PRD content
        self.large_prd_content = """# Large System Performance Test PRD

## 1. Executive Summary
This is a large PRD for system performance testing.

## 2. System Architecture
- Component 1
- Component 2
- Component 3

## 3. Feature Requirements

### 3.1 Feature Group 1
- [ ] Feature 1.1
- [ ] Feature 1.2
- [ ] Feature 1.3
- [ ] Feature 1.4
- [ ] Feature 1.5

### 3.2 Feature Group 2
- [ ] Feature 2.1
- [ ] Feature 2.2
- [ ] Feature 2.3
- [ ] Feature 2.4
- [ ] Feature 2.5

### 3.3 Feature Group 3
- [ ] Feature 3.1
- [ ] Feature 3.2
- [ ] Feature 3.3
- [ ] Feature 3.4
- [ ] Feature 3.5

## 4. Implementation Phases

### Phase 1: Setup
- [ ] Task 1.1
- [ ] Task 1.2
- [ ] Task 1.3
- [ ] Task 1.4
- [ ] Task 1.5

### Phase 2: Development
- [ ] Task 2.1
- [ ] Task 2.2
- [ ] Task 2.3
- [ ] Task 2.4
- [ ] Task 2.5

### Phase 3: Testing
- [ ] Task 3.1
- [ ] Task 3.2
- [ ] Task 3.3
- [ ] Task 3.4
- [ ] Task 3.5

### Phase 4: Deployment
- [ ] Task 4.1
- [ ] Task 4.2
- [ ] Task 4.3
- [ ] Task 4.4
- [ ] Task 4.5

### Phase 5: Maintenance
- [ ] Task 5.1
- [ ] Task 5.2
- [ ] Task 5.3
- [ ] Task 5.4
- [ ] Task 5.5
"""
    
    def test_end_to_end_performance(self):
        """Test end-to-end system performance"""
        self.benchmark.start_benchmark()
        
        # Parse PRD
        prd_data = self.parser.parse_prd_content(self.large_prd_content)
        tasks = self.parser.extract_tasks(self.large_prd_content)
        phases = self.parser.extract_phases(self.large_prd_content)
        
        # Add tasks to manager
        for task in tasks:
            self.manager.add_task(task)
        
        # Execute tasks
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout=b'Success', stderr=b'')
            
            for task in self.manager.tasks.values():
                result = self.master.execute_task(task, {})
                if result.success:
                    self.manager.update_task_status(task.id, TaskStatus.COMPLETED)
        
        # Generate progress report
        progress = self.manager.get_progress_report()
        
        benchmark_result = self.benchmark.end_benchmark("end_to_end_performance")
        
        self.assertGreater(progress['total_tasks'], 0)
        self.assertLess(benchmark_result['execution_time'], 5.0)  # Less than 5 seconds
        self.assertLess(benchmark_result['memory_usage'], 100)  # Less than 100MB
    
    def test_scalability_performance(self):
        """Test scalability performance"""
        # Test with different scales
        scales = [100, 500, 1000, 5000, 10000]
        results = {}
        
        for scale in scales:
            self.benchmark.start_benchmark()
            
            # Create tasks at scale
            for i in range(scale):
                task = Task(
                    id=f"scale-{scale}-{i}",
                    title=f"Scale Task {scale}-{i}",
                    description=f"Description {scale}-{i}",
                    priority=Priority.MEDIUM,
                    status=TaskStatus.PENDING
                )
                self.manager.add_task(task)
            
            # Execute tasks
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = Mock(returncode=0, stdout=b'Success', stderr=b'')
                
                for task in self.manager.tasks.values():
                    result = self.master.execute_task(task, {})
                    if result.success:
                        self.manager.update_task_status(task.id, TaskStatus.COMPLETED)
            
            benchmark_result = self.benchmark.end_benchmark(f"scalability_{scale}")
            results[scale] = benchmark_result
            
            # Clear manager for next scale
            self.manager = TaskManager()
        
        # Verify scalability
        for scale, result in results.items():
            self.assertLess(result['execution_time'], scale * 0.001)  # Linear scaling
    
    def test_memory_scalability(self):
        """Test memory scalability"""
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        # Create many tasks
        for i in range(50000):
            task = Task(
                id=f"mem-scale-{i}",
                title=f"Memory Scale Task {i}",
                description=f"Description {i}",
                priority=Priority.MEDIUM,
                status=TaskStatus.PENDING
            )
            self.manager.add_task(task)
        
        peak_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        memory_increase = peak_memory - initial_memory
        
        # Memory increase should be reasonable
        self.assertLess(memory_increase, 500)  # Less than 500MB increase
        
        # Clean up
        del self.manager
        gc.collect()
    
    def test_concurrent_system_performance(self):
        """Test concurrent system performance"""
        def system_operation(operation_id):
            # Parse PRD
            prd_data = self.parser.parse_prd_content(self.large_prd_content)
            tasks = self.parser.extract_tasks(self.large_prd_content)
            
            # Create manager
            manager = TaskManager()
            for task in tasks:
                manager.add_task(task)
            
            # Execute tasks
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = Mock(returncode=0, stdout=b'Success', stderr=b'')
                
                for task in manager.tasks.values():
                    result = self.master.execute_task(task, {})
                    if result.success:
                        manager.update_task_status(task.id, TaskStatus.COMPLETED)
            
            return len(manager.tasks)
        
        self.benchmark.start_benchmark()
        
        # Run concurrent system operations
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(system_operation, i) for i in range(100)]
            results = [future.result() for future in futures]
        
        benchmark_result = self.benchmark.end_benchmark("concurrent_system_performance")
        
        self.assertEqual(len(results), 100)
        for result in results:
            self.assertGreater(result, 0)
        
        self.assertLess(benchmark_result['execution_time'], 10.0)  # Less than 10 seconds


if __name__ == '__main__':
    # Run performance benchmarks
    unittest.main(verbosity=2)

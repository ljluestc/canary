#!/usr/bin/env python3
"""
Start Task Master Execution

This script starts the automated execution of all 602 tasks from the master-tasks.json file.
It provides a safe way to execute deployment tasks with proper error handling and logging.
"""

import sys
import os
from pathlib import Path

# Add directories to path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'task-manager'))
sys.path.insert(0, str(project_root / 'task-master'))

from task_manager import TaskManager
from task_master import TaskMaster

def main():
    """Main execution entry point."""

    # Initialize task manager with master tasks
    master_tasks_file = project_root / 'task-manager' / 'master-tasks.json'
    print(f"Loading tasks from: {master_tasks_file}")

    task_manager = TaskManager(str(master_tasks_file))

    # Display initial progress
    print("\n" + "="*60)
    print("TASK MASTER EXECUTION INITIALIZED")
    print("="*60)
    progress = task_manager.get_progress_report()
    print(f"Project: {progress['title']}")
    print(f"Total Tasks: {progress['total_tasks']}")
    print(f"Total Phases: {len(progress['phases'])}")
    print("="*60 + "\n")

    # Set up execution context
    context = {
        'terraform_dir': str(project_root / 'terraform'),
        'k8s_dir': str(project_root / 'k8s'),
        'argocd_dir': str(project_root / 'argocd'),
        'working_dir': str(project_root),
        'stop_on_failure': False,  # Continue even if some tasks fail
        'env': {
            'KUBECONFIG': os.environ.get('KUBECONFIG', '~/.kube/config')
        }
    }

    # Initialize task master
    task_master = TaskMaster(task_manager, context)

    # Get list of all phases
    phases = []
    for phase_data in progress['phases']:
        phases.append(phase_data['name'])

    print(f"Found {len(phases)} phases to execute\n")

    # Identify critical phases to execute first
    critical_phases = [p for p in phases if 'critical' in str(task_manager.get_tasks({'phase': p})[0].get('priority', '')).lower()]

    print("CRITICAL PHASES (to be executed first):")
    for i, phase in enumerate(critical_phases[:10], 1):  # Show first 10 critical phases
        print(f"  {i}. {phase}")

    if len(critical_phases) > 10:
        print(f"  ... and {len(critical_phases) - 10} more critical phases")

    print("\nALL PHASES:")
    for i, phase in enumerate(phases[:15], 1):  # Show first 15 phases
        phase_tasks = task_manager.get_tasks({'phase': phase})
        priority = phase_tasks[0].get('priority', 'unknown') if phase_tasks else 'unknown'
        print(f"  {i}. {phase} ({len(phase_tasks)} tasks, priority: {priority})")

    if len(phases) > 15:
        print(f"  ... and {len(phases) - 15} more phases")

    print("\n" + "="*60)
    print("EXECUTION STRATEGY")
    print("="*60)
    print("The task master will execute tasks in the following order:")
    print("1. Development Environment Setup")
    print("2. Task Management System Setup")
    print("3. Task Master Execution Engine")
    print("4. Infrastructure Provisioning")
    print("5. Application Service Deployments")
    print("6. Blue-Green and Canary Deployment Setups")
    print("7. Monitoring and Observability")
    print("8. CI/CD Pipeline Implementation")
    print("9. Comprehensive Testing")
    print("10. Production Readiness Validation")
    print("="*60 + "\n")

    # Ask for confirmation
    response = input("Ready to start execution? This will execute 602 tasks. (yes/no/dry-run): ").strip().lower()

    if response == 'dry-run':
        print("\nDRY-RUN MODE: Showing what would be executed...")
        print("\nFirst phase tasks preview:")
        first_phase = phases[0] if phases else None
        if first_phase:
            first_phase_tasks = task_manager.get_tasks({'phase': first_phase})
            for i, task in enumerate(first_phase_tasks[:5], 1):
                print(f"  {i}. {task['title']}")
            if len(first_phase_tasks) > 5:
                print(f"  ... and {len(first_phase_tasks) - 5} more tasks in this phase")
        print("\nTo execute, run: python3 start_execution.py")
        return

    elif response != 'yes':
        print("Execution cancelled.")
        return

    print("\n" + "="*60)
    print("STARTING EXECUTION")
    print("="*60 + "\n")

    # Execute phases sequentially
    total_completed = 0
    total_failed = 0

    for i, phase in enumerate(phases, 1):
        print(f"\n[{i}/{len(phases)}] Executing Phase: {phase}")
        print("-" * 60)

        phase_result = task_master.execute_phase(phase, context)

        total_completed += phase_result.tasks_completed
        total_failed += phase_result.tasks_failed

        print(f"Phase Result: {'SUCCESS' if phase_result.success else 'FAILED'}")
        print(f"  Completed: {phase_result.tasks_completed}")
        print(f"  Failed: {phase_result.tasks_failed}")
        print(f"  Duration: {phase_result.duration:.2f}s")

        # Show current overall progress
        current_progress = task_manager.get_progress_report()
        print(f"\nOverall Progress: {current_progress['completed_tasks']}/{current_progress['total_tasks']} " +
              f"({current_progress['completed_percentage']:.1f}%)")

        # If phase failed and stop_on_failure is True, ask to continue
        if not phase_result.success and context.get('stop_on_failure', False):
            cont = input("\nPhase failed. Continue to next phase? (yes/no): ").strip().lower()
            if cont != 'yes':
                print("Execution stopped by user.")
                break

    # Final summary
    print("\n" + "="*60)
    print("EXECUTION COMPLETE")
    print("="*60)
    print(f"Total Tasks Completed: {total_completed}")
    print(f"Total Tasks Failed: {total_failed}")

    final_progress = task_manager.get_progress_report()
    print(f"Final Progress: {final_progress['completed_percentage']:.1f}%")
    print(f"Status Breakdown:")
    print(f"  Completed: {final_progress['completed_tasks']}")
    print(f"  In Progress: {final_progress['in_progress_tasks']}")
    print(f"  Pending: {final_progress['pending_tasks']}")
    print(f"  Failed: {final_progress['failed_tasks']}")
    print(f"  Blocked: {final_progress['blocked_tasks']}")
    print("="*60)

    # Save execution log
    log_file = project_root / 'execution-log.json'
    task_master.save_execution_log(str(log_file), 'json')
    print(f"\nExecution log saved to: {log_file}")

    # Save updated task status
    task_manager.save()
    print(f"Task status saved to: {master_tasks_file}")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nExecution interrupted by user (Ctrl+C)")
        print("Task progress has been saved.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

#!/usr/bin/env python3
import json

# Load all task files
tasks_files = [
    'prd-tasks.json',
    'setup-tasks.json',
    'blue-green-tasks.json',
    'canary-tasks.json',
    'troubleshooting-tasks.json',
    'readme-tasks.json'
]

all_tasks = []
all_phases = []
titles = []

for file in tasks_files:
    with open(file, 'r') as f:
        data = json.load(f)
        titles.append(data['metadata']['title'])
        all_phases.extend(data['phases'])
        all_tasks.extend(data['tasks'])

master = {
    'metadata': {
        'title': 'Master PRD: Complete Deployment System',
        'sources': titles,
        'total_tasks': len(all_tasks),
        'total_phases': len(all_phases)
    },
    'phases': all_phases,
    'tasks': all_tasks
}

with open('master-tasks.json', 'w') as f:
    json.dump(master, f, indent=2)

print(f"Master tasks file created:")
print(f"  Total PRDs combined: {len(titles)}")
print(f"  Total Phases: {len(all_phases)}")
print(f"  Total Tasks: {len(all_tasks)}")

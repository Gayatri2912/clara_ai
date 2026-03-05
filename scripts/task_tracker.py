"""
Task Tracker for Clara AI Automation Pipeline

Tracks the status of each account through the pipeline:
- demo_call_processed
- v1_agent_created
- onboarding_processed
- v2_agent_created
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from utils import get_timestamp

TRACKER_FILE = Path("outputs/task_tracker.json")


def load_tracker() -> Dict:
    """Load existing task tracker or create new one"""
    if TRACKER_FILE.exists():
        with open(TRACKER_FILE, 'r') as f:
            return json.load(f)
    return {
        "created_at": get_timestamp(),
        "last_updated": get_timestamp(),
        "accounts": {}
    }


def save_tracker(tracker: Dict):
    """Save task tracker to file"""
    tracker['last_updated'] = get_timestamp()
    TRACKER_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(TRACKER_FILE, 'w') as f:
        json.dump(tracker, f, indent=2)
    logger.info(f"Task tracker saved to {TRACKER_FILE}")


def create_task(account_id: str, company_name: str) -> Dict:
    """Create a new task for an account"""
    tracker = load_tracker()
    
    if account_id not in tracker['accounts']:
        tracker['accounts'][account_id] = {
            "account_id": account_id,
            "company_name": company_name,
            "created_at": get_timestamp(),
            "status": "created",
            "pipeline_stages": {
                "demo_call_processed": False,
                "v1_agent_created": False,
                "onboarding_processed": False,
                "v2_agent_created": False
            },
            "timestamps": {},
            "notes": []
        }
        logger.info(f"Created task for {company_name} ({account_id})")
    
    save_tracker(tracker)
    return tracker['accounts'][account_id]


def update_task_stage(account_id: str, stage: str, status: bool = True, note: Optional[str] = None):
    """Update a specific pipeline stage for an account"""
    tracker = load_tracker()
    
    if account_id not in tracker['accounts']:
        logger.error(f"Account {account_id} not found in tracker")
        return
    
    account = tracker['accounts'][account_id]
    
    # Update stage
    if stage in account['pipeline_stages']:
        account['pipeline_stages'][stage] = status
        account['timestamps'][stage] = get_timestamp()
        
        # Update overall status
        stages = account['pipeline_stages']
        if stages['v2_agent_created']:
            account['status'] = 'complete'
        elif stages['v1_agent_created']:
            account['status'] = 'v1_ready'
        elif stages['demo_call_processed']:
            account['status'] = 'in_progress'
        
        logger.info(f"Updated {account_id} - {stage}: {status}")
    
    # Add note if provided
    if note:
        account['notes'].append({
            "timestamp": get_timestamp(),
            "message": note
        })
    
    save_tracker(tracker)


def get_task_status(account_id: str) -> Optional[Dict]:
    """Get current status of an account"""
    tracker = load_tracker()
    return tracker['accounts'].get(account_id)


def get_all_tasks() -> List[Dict]:
    """Get all tasks"""
    tracker = load_tracker()
    return list(tracker['accounts'].values())


def generate_summary() -> Dict:
    """Generate summary statistics"""
    tracker = load_tracker()
    accounts = tracker['accounts'].values()
    
    summary = {
        "total_accounts": len(accounts),
        "complete": sum(1 for a in accounts if a['status'] == 'complete'),
        "v1_ready": sum(1 for a in accounts if a['status'] == 'v1_ready'),
        "in_progress": sum(1 for a in accounts if a['status'] == 'in_progress'),
        "created": sum(1 for a in accounts if a['status'] == 'created'),
        "stages": {
            "demo_calls_processed": sum(1 for a in accounts if a['pipeline_stages']['demo_call_processed']),
            "v1_agents_created": sum(1 for a in accounts if a['pipeline_stages']['v1_agent_created']),
            "onboarding_processed": sum(1 for a in accounts if a['pipeline_stages']['onboarding_processed']),
            "v2_agents_created": sum(1 for a in accounts if a['pipeline_stages']['v2_agent_created'])
        }
    }
    
    return summary


def print_summary():
    """Print a formatted summary"""
    summary = generate_summary()
    
    print("\n" + "="*60)
    print("TASK TRACKER SUMMARY")
    print("="*60)
    print(f"Total Accounts: {summary['total_accounts']}")
    print(f"  Complete (v2): {summary['complete']}")
    print(f"  v1 Ready: {summary['v1_ready']}")
    print(f"  In Progress: {summary['in_progress']}")
    print(f"  Created: {summary['created']}")
    print("\nPipeline Stages:")
    print(f"  Demo Calls Processed: {summary['stages']['demo_calls_processed']}")
    print(f"  v1 Agents Created: {summary['stages']['v1_agents_created']}")
    print(f"  Onboarding Processed: {summary['stages']['onboarding_processed']}")
    print(f"  v2 Agents Created: {summary['stages']['v2_agents_created']}")
    print("="*60 + "\n")


def print_all_tasks():
    """Print all tasks in a formatted table"""
    tasks = get_all_tasks()
    
    if not tasks:
        print("No tasks found.")
        return
    
    print("\n" + "="*120)
    print(f"{'Account ID':<35} {'Company':<30} {'Status':<15} {'v1':<5} {'v2':<5}")
    print("="*120)
    
    for task in tasks:
        account_id = task['account_id'][:33]
        company = task['company_name'][:28]
        status = task['status']
        v1 = '✓' if task['pipeline_stages']['v1_agent_created'] else '✗'
        v2 = '✓' if task['pipeline_stages']['v2_agent_created'] else '✗'
        
        print(f"{account_id:<35} {company:<30} {status:<15} {v1:<5} {v2:<5}")
    
    print("="*120 + "\n")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Task Tracker Commands:")
        print("  python scripts/task_tracker.py summary    - Show summary")
        print("  python scripts/task_tracker.py list       - List all tasks")
        print("  python scripts/task_tracker.py status <account_id>  - Show task details")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "summary":
        print_summary()
    elif command == "list":
        print_all_tasks()
    elif command == "status" and len(sys.argv) == 3:
        account_id = sys.argv[2]
        task = get_task_status(account_id)
        if task:
            print(json.dumps(task, indent=2))
        else:
            print(f"Account {account_id} not found")
    else:
        print("Invalid command")

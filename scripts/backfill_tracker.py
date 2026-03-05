"""
Backfill Task Tracker with Existing Accounts

Scans outputs/accounts/ and creates task tracker entries for already processed accounts
"""

import json
from pathlib import Path
from task_tracker import create_task, update_task_stage, load_tracker, save_tracker
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def backfill_tracker():
    """Scan existing outputs and populate task tracker"""
    
    accounts_dir = Path("outputs/accounts")
    if not accounts_dir.exists():
        logger.error("No outputs/accounts directory found")
        return
    
    tracker = load_tracker()
    accounts_found = 0
    
    for account_path in accounts_dir.iterdir():
        if not account_path.is_dir():
            continue
        
        account_id = account_path.name
        
        # Skip if already in tracker
        if account_id in tracker['accounts']:
            logger.info(f"Account {account_id} already tracked, skipping")
            continue
        
        # Load metadata if exists
        metadata_path = account_path / 'metadata.json'
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            company_name = metadata.get('company_name', 'Unknown')
        else:
            # Try to load from v1 account memo
            v1_memo_path = account_path / 'v1' / 'account_memo.json'
            if v1_memo_path.exists():
                with open(v1_memo_path, 'r') as f:
                    memo = json.load(f)
                company_name = memo.get('company_name', 'Unknown')
            else:
                company_name = account_id.replace('_', ' ').title()
        
        # Create task entry
        logger.info(f"Backfilling {company_name} ({account_id})")
        create_task(account_id, company_name)
        accounts_found += 1
        
        # Check what stages exist
        v1_dir = account_path / 'v1'
        v2_dir = account_path / 'v2'
        
        # Check v1 stages
        if v1_dir.exists():
            if (v1_dir / 'account_memo.json').exists():
                update_task_stage(account_id, 'demo_call_processed', True, "Backfilled from existing files")
            
            if (v1_dir / 'agent_spec.json').exists() and (v1_dir / 'system_prompt.txt').exists():
                update_task_stage(account_id, 'v1_agent_created', True, "Backfilled from existing files")
        
        # Check v2 stages
        if v2_dir.exists():
            if (v2_dir / 'account_memo.json').exists():
                update_task_stage(account_id, 'onboarding_processed', True, "Backfilled from existing files")
            
            if (v2_dir / 'agent_spec.json').exists() and (v2_dir / 'changelog.md').exists():
                update_task_stage(account_id, 'v2_agent_created', True, "Backfilled from existing files")
    
    logger.info(f"\n✓ Backfilled {accounts_found} accounts into task tracker")
    
    return accounts_found


if __name__ == "__main__":
    backfill_tracker()
    
    # Show summary
    print("\nRunning task tracker summary...")
    from task_tracker import print_summary, print_all_tasks
    print_summary()
    print_all_tasks()

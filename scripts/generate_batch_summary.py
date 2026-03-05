"""
Batch Processing Summary Generator

Generates comprehensive reports of all processed accounts
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from task_tracker import load_tracker, generate_summary


def generate_batch_summary() -> Dict:
    """Generate comprehensive batch processing summary"""
    
    # Load task tracker
    tracker = load_tracker()
    accounts = tracker.get('accounts', {})
    
    # Collect statistics
    summary = {
        "generated_at": datetime.now().isoformat(),
        "total_accounts": len(accounts),
        "pipeline_statistics": {
            "demo_calls_processed": 0,
            "v1_agents_created": 0,
            "onboarding_calls_processed": 0,
            "v2_agents_created": 0,
            "complete_pipelines": 0
        },
        "accounts_by_status": {
            "complete": [],
            "v1_ready": [],
            "in_progress": [],
            "created": []
        },
        "outputs_generated": {
            "account_memos": 0,
            "agent_specs": 0,
            "system_prompts": 0,
            "changelogs": 0
        }
    }
    
    # Process each account
    for account_id, account in accounts.items():
        stages = account['pipeline_stages']
        status = account['status']
        
        # Update statistics
        if stages['demo_call_processed']:
            summary['pipeline_statistics']['demo_calls_processed'] += 1
        if stages['v1_agent_created']:
            summary['pipeline_statistics']['v1_agents_created'] += 1
        if stages['onboarding_processed']:
            summary['pipeline_statistics']['onboarding_calls_processed'] += 1
        if stages['v2_agent_created']:
            summary['pipeline_statistics']['v2_agents_created'] += 1
        
        if status == 'complete':
            summary['pipeline_statistics']['complete_pipelines'] += 1
        
        # Group by status
        account_summary = {
            "account_id": account_id,
            "company_name": account['company_name'],
            "created_at": account['created_at'],
            "v1_ready": stages['v1_agent_created'],
            "v2_ready": stages['v2_agent_created']
        }
        
        summary['accounts_by_status'][status].append(account_summary)
    
    # Count output files
    outputs_dir = Path("outputs/accounts")
    if outputs_dir.exists():
        summary['outputs_generated']['account_memos'] = len(list(outputs_dir.glob("*/v*/account_memo.json")))
        summary['outputs_generated']['agent_specs'] = len(list(outputs_dir.glob("*/v*/agent_spec.json")))
        summary['outputs_generated']['system_prompts'] = len(list(outputs_dir.glob("*/v*/system_prompt.txt")))
        summary['outputs_generated']['changelogs'] = len(list(outputs_dir.glob("*/v2/changelog.md")))
    
    return summary


def generate_markdown_report(summary: Dict) -> str:
    """Generate human-readable markdown report"""
    
    lines = [
        "# Clara AI Pipeline - Batch Processing Summary",
        "",
        f"**Generated:** {summary['generated_at']}",
        "",
        "## Overview",
        "",
        f"- **Total Accounts Processed:** {summary['total_accounts']}",
        f"- **Complete Pipelines (v1+v2):** {summary['pipeline_statistics']['complete_pipelines']}",
        "",
        "## Pipeline Statistics",
        "",
        f"- Demo Calls Processed: {summary['pipeline_statistics']['demo_calls_processed']}",
        f"- v1 Agents Created: {summary['pipeline_statistics']['v1_agents_created']}",
        f"- Onboarding Calls Processed: {summary['pipeline_statistics']['onboarding_calls_processed']}",
        f"- v2 Agents Created: {summary['pipeline_statistics']['v2_agents_created']}",
        "",
        "## Output Files Generated",
        "",
        f"- Account Memos: {summary['outputs_generated']['account_memos']}",
        f"- Agent Specifications: {summary['outputs_generated']['agent_specs']}",
        f"- System Prompts: {summary['outputs_generated']['system_prompts']}",
        f"- Changelogs: {summary['outputs_generated']['changelogs']}",
        "",
        "## Accounts by Status",
        ""
    ]
    
    # Complete accounts
    complete = summary['accounts_by_status']['complete']
    if complete:
        lines.append(f"### ✅ Complete (v1 + v2) - {len(complete)} accounts")
        lines.append("")
        for acc in complete:
            lines.append(f"- **{acc['company_name']}** (`{acc['account_id']}`)")
        lines.append("")
    
    # V1 ready accounts
    v1_ready = summary['accounts_by_status']['v1_ready']
    if v1_ready:
        lines.append(f"### 🟡 V1 Ready (awaiting onboarding) - {len(v1_ready)} accounts")
        lines.append("")
        for acc in v1_ready:
            lines.append(f"- **{acc['company_name']}** (`{acc['account_id']}`)")
        lines.append("")
    
    # In progress accounts
    in_progress = summary['accounts_by_status']['in_progress']
    if in_progress:
        lines.append(f"### 🔄 In Progress - {len(in_progress)} accounts")
        lines.append("")
        for acc in in_progress:
            lines.append(f"- **{acc['company_name']}** (`{acc['account_id']}`)")
        lines.append("")
    
    # Created but not started
    created = summary['accounts_by_status']['created']
    if created:
        lines.append(f"### ⭕ Created (not started) - {len(created)} accounts")
        lines.append("")
        for acc in created:
            lines.append(f"- **{acc['company_name']}** (`{acc['account_id']}`)")
        lines.append("")
    
    lines.extend([
        "---",
        "",
        "## Next Steps",
        "",
        "1. Review generated agent specifications in `outputs/accounts/`",
        "2. Check changelogs to see v1→v2 updates",
        "3. Import agent specs into Retell AI (see README for instructions)",
        "4. Test agents with sample calls",
        ""
    ])
    
    return '\n'.join(lines)


def save_reports():
    """Generate and save all reports"""
    
    logger.info("Generating batch processing summary...")
    
    # Generate summary
    summary = generate_batch_summary()
    
    # Save JSON report
    json_path = Path("outputs/batch_summary.json")
    json_path.parent.mkdir(parents=True, exist_ok=True)
    with open(json_path, 'w') as f:
        json.dump(summary, f, indent=2)
    logger.info(f"Saved JSON summary to {json_path}")
    
    # Generate and save markdown report
    markdown = generate_markdown_report(summary)
    md_path = Path("outputs/batch_summary.md")
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(markdown)
    logger.info(f"Saved markdown report to {md_path}")
    
    # Print summary to console
    print("\n" + "="*80)
    print(markdown)
    print("="*80)
    
    return summary


if __name__ == "__main__":
    save_reports()

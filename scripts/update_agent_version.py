"""
Update Agent Version from Onboarding Call
Takes v1 agent + onboarding transcript → generates v2 + changelog
"""

import argparse
import json
import logging
from pathlib import Path
from typing import Dict, Any
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))
from utils import (
    llm_client,
    save_json,
    load_json,
    read_file,
    write_file,
    get_output_path,
    get_timestamp,
    calculate_diff,
    format_changelog,
    logger
)
from generate_agent_spec import generate_system_prompt, build_agent_spec
from task_tracker import update_task_stage

# Update extraction prompt
UPDATE_EXTRACTION_PROMPT = """You are reviewing an onboarding call transcript to identify updates to an existing business configuration.

**Current Configuration (v1):**
{v1_memo}

**Onboarding Call Transcript:**
{onboarding_transcript}

**Task:**
Identify ANY new information or changes mentioned in the onboarding call that should update the v1 configuration.

**Look for:**
- Changes to business hours
- New services or removed services
- New contact information
- Updated routing rules
- New addresses or locations
- Policy changes
- Integration requirements
- Any corrections to v1 data

**Return a JSON object with ONLY the fields that need to be updated.**

If a field should be modified, include the complete NEW value (not a diff).
If nothing needs updating for a field, omit it from the response.

**Rules:**
1. Only include changes explicitly mentioned in the onboarding call
2. Preserve all v1 data that isn't being updated
3. If clarifying or correcting v1 data, include the correction
4. Include a "reason" field explaining each change

**Format:**
{{
  "updates": {{
    "field_name": {{
      "new_value": <complete new value>,
      "reason": "explanation from onboarding call"
    }},
    ...
  }}
}}

**Return ONLY the JSON, no other text.**
"""


def extract_updates(v1_memo: Dict[str, Any], onboarding_transcript: str) -> Dict[str, Dict[str, Any]]:
    """
    Extract updates from onboarding call
    
    Args:
        v1_memo: Version 1 account memo
        onboarding_transcript: Onboarding call transcript
    
    Returns:
        Dictionary of updates by field
    """
    logger.info("Extracting updates from onboarding call...")
    
    # Format prompt
    prompt = UPDATE_EXTRACTION_PROMPT.format(
        v1_memo=json.dumps(v1_memo, indent=2),
        onboarding_transcript=onboarding_transcript
    )
    
    # Call LLM
    logger.info("Calling LLM to identify updates...")
    response = llm_client.call(
        prompt=prompt,
        temperature=0.3
    )
    
    # Parse response
    try:
        if '```json' in response:
            response = response.split('```json')[1].split('```')[0].strip()
        elif '```' in response:
            response = response.split('```')[1].split('```')[0].strip()
        
        result = json.loads(response)
        updates = result.get('updates', {})
        
        logger.info(f"Found {len(updates)} fields to update")
        return updates
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse updates JSON: {e}")
        logger.error(f"Response was: {response}")
        # Return empty updates rather than failing
        return {}


def apply_updates(v1_memo: Dict[str, Any], updates: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Apply updates to v1 memo to create v2
    
    Args:
        v1_memo: Version 1 memo
        updates: Dictionary of updates
    
    Returns:
        Version 2 memo
    """
    logger.info("Applying updates to create v2...")
    
    # Deep copy v1
    v2_memo = json.loads(json.dumps(v1_memo))
    
    # Apply each update
    for field, update_info in updates.items():
        # Handle both formats: dict with new_value/reason, or direct value
        if isinstance(update_info, dict) and 'new_value' in update_info:
            new_value = update_info.get('new_value')
            reason = update_info.get('reason', 'Updated from onboarding')
        else:
            # Direct value format
            new_value = update_info
            reason = 'Updated from onboarding'
        
        v2_memo[field] = new_value
        logger.info(f"  Updated {field}: {reason}")
    
    # Update metadata
    v2_memo['version'] = 'v2'
    v2_memo['updated_at'] = get_timestamp()
    if 'notes' in v2_memo:
        v2_memo['notes'] += ' | Updated from onboarding call'
    else:
        v2_memo['notes'] = 'Updated from onboarding call'
    
    logger.info(f"v2 memo created with {len(updates)} updates")
    return v2_memo


def generate_detailed_changelog(v1_memo: Dict, v2_memo: Dict, updates: Dict) -> str:
    """
    Generate detailed changelog with reasons
    
    Args:
        v1_memo: Version 1 memo
        v2_memo: Version 2 memo
        updates: Update information with reasons
    
    Returns:
        Markdown formatted changelog
    """
    account_id = v2_memo.get('account_id', 'unknown')
    company = v2_memo.get('company_name', 'Unknown Company')
    
    lines = [
        f"# Changelog: {company} (v1 → v2)",
        "",
        f"**Account ID**: {account_id}",
        f"**Updated**: {get_timestamp()}",
        "",
        "## Summary",
        "",
        f"Total fields updated: {len(updates)}",
        "",
        "## Detailed Changes",
        ""
    ]
    
    if not updates:
        lines.append("*No changes detected from onboarding call.*")
        return '\n'.join(lines)
    
    for field, update_info in updates.items():
        lines.append(f"### {field}")
        lines.append("")
        
        # Get old and new values
        old_value = v1_memo.get(field, "(not set)")
        
        # Handle both formats: dict with new_value/reason, or direct value
        if isinstance(update_info, dict) and 'new_value' in update_info:
            new_value = update_info.get('new_value', "(not set)")
            reason = update_info.get('reason', 'No reason provided')
        else:
            new_value = update_info
            reason = 'Updated from onboarding call'
        
        # Format values for display
        if isinstance(old_value, (dict, list)):
            old_display = json.dumps(old_value, indent=2)
        else:
            old_display = str(old_value)
        
        if isinstance(new_value, (dict, list)):
            new_display = json.dumps(new_value, indent=2)
        else:
            new_display = str(new_value)
        
        lines.append(f"**Before (v1):**")
        lines.append(f"```")
        lines.append(old_display)
        lines.append(f"```")
        lines.append("")
        
        lines.append(f"**After (v2):**")
        lines.append(f"```")
        lines.append(new_display)
        lines.append(f"```")
        lines.append("")
        
        lines.append(f"**Reason**: {reason}")
        lines.append("")
        lines.append("---")
        lines.append("")
    
    lines.append("## Impact Assessment")
    lines.append("")
    
    # Analyze impact
    if 'business_hours' in updates:
        lines.append("- ⚠️ **Business hours changed** - Agent will handle calls differently based on new schedule")
    if 'emergency_routing_rules' in updates or 'emergency_definition' in updates:
        lines.append("- ⚠️ **Emergency handling updated** - Critical path modified")
    if 'services_supported' in updates:
        lines.append("- 📋 **Services changed** - Agent will recognize different service requests")
    if 'call_transfer_rules' in updates:
        lines.append("- 📞 **Transfer rules modified** - Call routing behavior updated")
    
    lines.append("")
    lines.append("## Next Steps")
    lines.append("")
    lines.append("1. Review the updated agent specification (agent_spec.json)")
    lines.append("2. Test the new system prompt with sample scenarios")
    lines.append("3. Import updated configuration into Retell (see RETELL_SETUP.md)")
    lines.append("4. Monitor first calls to verify correct behavior")
    
    return '\n'.join(lines)


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Update agent from v1 to v2 using onboarding call'
    )
    parser.add_argument(
        '--account-id',
        type=str,
        required=True,
        help='Account ID to update'
    )
    parser.add_argument(
        '--onboarding',
        type=Path,
        required=True,
        help='Path to onboarding call transcript'
    )
    parser.add_argument(
        '--v1-dir',
        type=Path,
        help='Optional path to v1 directory (default: auto-locate from account-id)'
    )
    
    args = parser.parse_args()
    
    # Locate v1 directory
    if args.v1_dir:
        v1_dir = args.v1_dir
    else:
        v1_dir = get_output_path(args.account_id, 'v1')
    
    # Check v1 exists
    v1_memo_path = v1_dir / 'account_memo.json'
    if not v1_memo_path.exists():
        logger.error(f"v1 memo not found: {v1_memo_path}")
        logger.error(f"Run extract_account_memo.py first to create v1")
        sys.exit(1)
    
    # Check onboarding file exists
    if not args.onboarding.exists():
        logger.error(f"Onboarding transcript not found: {args.onboarding}")
        sys.exit(1)
    
    try:
        # Load v1
        v1_memo = load_json(v1_memo_path)
        logger.info(f"Loaded v1 memo from {v1_memo_path}")
        
        # Load onboarding transcript
        onboarding_transcript = read_file(args.onboarding)
        logger.info(f"Loaded onboarding transcript from {args.onboarding}")
        
        # Extract updates
        updates = extract_updates(v1_memo, onboarding_transcript)
        
        if not updates:
            logger.warning("No updates found in onboarding call")
            logger.warning("v2 will be identical to v1")
        
        # Apply updates to create v2
        v2_memo = apply_updates(v1_memo, updates)
        
        # Generate new agent spec for v2
        logger.info("Regenerating agent specification for v2...")
        system_prompt_v2 = generate_system_prompt(v2_memo)
        agent_spec_v2 = build_agent_spec(v2_memo, system_prompt_v2)
        
        # Generate changelog
        changelog = generate_detailed_changelog(v1_memo, v2_memo, updates)
        
        # Save v2 outputs
        v2_dir = get_output_path(args.account_id, 'v2')
        save_json(v2_memo, v2_dir / 'account_memo.json')
        save_json(agent_spec_v2, v2_dir / 'agent_spec.json')
        write_file(system_prompt_v2, v2_dir / 'system_prompt.txt')
        write_file(changelog, v2_dir / 'changelog.md')
        
        # Update metadata
        metadata_path = v1_dir.parent / 'metadata.json'
        if metadata_path.exists():
            metadata = load_json(metadata_path)
        else:
            metadata = {}
        
        metadata['current_version'] = 'v2'
        metadata['v2_created_at'] = get_timestamp()
        metadata['onboarding_source'] = str(args.onboarding)
        metadata['updates_count'] = len(updates)
        save_json(metadata, metadata_path)
        
        logger.info("="*60)
        logger.info(f"✓ Successfully updated to v2")
        logger.info(f"  Account: {v2_memo.get('company_name')}")
        logger.info(f"  Updates: {len(updates)} fields")
        logger.info(f"  Output: {v2_dir}")
        logger.info("="*60)
        
        # Update task tracker
        account_id = args.account_id
        update_task_stage(account_id, 'onboarding_processed', True,
                        f"Processed onboarding call: {len(updates)} updates")
        update_task_stage(account_id, 'v2_agent_created', True,
                        f"Generated v2 agent: {v2_memo.get('company_name')}")
        
        # Print changelog preview
        print("\n" + "="*60)
        print("CHANGELOG PREVIEW:")
        print("="*60)
        print(changelog[:1000] + "..." if len(changelog) > 1000 else changelog)
        print("="*60)
        
    except Exception as e:
        logger.error(f"Failed to update agent: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

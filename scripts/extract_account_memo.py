"""
Extract Account Memo from Demo Call Transcript
Converts unstructured call transcript into structured JSON format
"""

import argparse
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))
from utils import (
    llm_client, 
    save_json, 
    read_file, 
    get_account_id,
    get_output_path,
    get_timestamp,
    extract_company_name_from_transcript,
    logger
)
from task_tracker import create_task, update_task_stage

# Extraction prompt template
EXTRACTION_PROMPT = """You are an expert at extracting structured business information from call transcripts.

Given the following demo call transcript, extract ALL relevant business information and return it as a JSON object.

**CRITICAL RULES:**
1. Only extract information that is EXPLICITLY stated in the transcript
2. If information is missing, use null or empty array []
3. Do NOT invent or assume information
4. If something is unclear, add it to "questions_or_unknowns"
5. Be precise with times, phone numbers, and addresses

**Transcript:**
{transcript}

**Extract the following structure:**
{{
  "company_name": "exact company name from call",
  "business_hours": {{
    "days": ["Monday", "Tuesday", etc.],
    "start": "HH:MM format",
    "end": "HH:MM format", 
    "timezone": "America/New_York format"
  }},
  "office_address": "full address if mentioned",
  "services_supported": ["list", "of", "services"],
  "emergency_definition": ["what", "qualifies", "as", "emergency"],
  "emergency_routing_rules": {{
    "priority_order": ["who to call first", "second", "third"],
    "contacts": {{
      "role_name": "phone_number"
    }},
    "fallback": "what to do if no one answers"
  }},
  "non_emergency_routing_rules": {{
    "action": "take_message or transfer or schedule",
    "fields": ["what", "info", "to", "collect"]
  }},
  "call_transfer_rules": {{
    "timeout_seconds": 30,
    "max_retries": 2,
    "transfer_failed_message": "exact message to use"
  }},
  "integration_constraints": ["any software or system constraints mentioned"],
  "after_hours_flow_summary": "brief summary of after-hours handling",
  "office_hours_flow_summary": "brief summary of office hours handling",
  "questions_or_unknowns": ["anything unclear or missing"],
  "notes": "any other relevant context"
}}

**Return ONLY the JSON object, no other text.**
"""


def extract_account_memo(transcript: str, account_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Extract structured account memo from transcript
    
    Args:
        transcript: Raw call transcript
        account_id: Optional account ID (will be extracted if not provided)
    
    Returns:
        Structured account memo dictionary
    """
    logger.info("Starting account memo extraction...")
    
    # Format prompt
    prompt = EXTRACTION_PROMPT.format(transcript=transcript)
    
    # Call LLM
    logger.info(f"Calling LLM ({llm_client.provider})...")
    response = llm_client.call(
        prompt=prompt,
        temperature=0.3  # Lower temperature for more consistent extraction
    )
    
    # Parse JSON from response
    try:
        # Try to extract JSON if wrapped in markdown
        if '```json' in response:
            response = response.split('```json')[1].split('```')[0].strip()
        elif '```' in response:
            response = response.split('```')[1].split('```')[0].strip()
        
        memo = json.loads(response)
        
        # Add metadata
        if not account_id:
            account_id = get_account_id(memo.get('company_name', 'unknown'))
        
        memo['account_id'] = account_id
        memo['version'] = 'v1'
        memo['created_at'] = get_timestamp()
        
        logger.info(f"Successfully extracted memo for {memo.get('company_name')}")
        return memo
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from LLM response: {e}")
        logger.error(f"Response was: {response}")
        raise


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Extract structured account memo from demo call transcript'
    )
    parser.add_argument(
        'transcript_file',
        type=Path,
        help='Path to transcript file'
    )
    parser.add_argument(
        '--account-id',
        type=str,
        help='Optional account ID (will be auto-generated if not provided)'
    )
    parser.add_argument(
        '--output',
        type=Path,
        help='Optional output path (default: outputs/accounts/<account_id>/v1/account_memo.json)'
    )
    
    args = parser.parse_args()
    
    # Read transcript
    if not args.transcript_file.exists():
        logger.error(f"Transcript file not found: {args.transcript_file}")
        sys.exit(1)
    
    transcript = read_file(args.transcript_file)
    logger.info(f"Loaded transcript from {args.transcript_file}")
    
    # Extract memo
    try:
        memo = extract_account_memo(transcript, args.account_id)
        
        # Determine output path
        if args.output:
            output_path = args.output
        else:
            account_dir = get_output_path(memo['account_id'], 'v1')
            output_path = account_dir / 'account_memo.json'
        
        # Save
        save_json(memo, output_path)
        
        logger.info("="*60)
        logger.info(f"✓ Account memo extracted successfully")
        logger.info(f"  Account ID: {memo['account_id']}")
        logger.info(f"  Company: {memo.get('company_name')}")
        logger.info(f"  Output: {output_path}")
        logger.info("="*60)
        
        # Also save metadata
        metadata = {
            'account_id': memo['account_id'],
            'company_name': memo.get('company_name'),
            'created_at': memo['created_at'],
            'source_file': str(args.transcript_file),
            'version': 'v1'
        }
        metadata_path = output_path.parent.parent / 'metadata.json'
        save_json(metadata, metadata_path)
        
        # Update task tracker
        create_task(memo['account_id'], memo.get('company_name', 'Unknown'))
        update_task_stage(memo['account_id'], 'demo_call_processed', True, 
                         f"Extracted from {Path(args.transcript_file).name}")
        
    except Exception as e:
        logger.error(f"Failed to extract account memo: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()

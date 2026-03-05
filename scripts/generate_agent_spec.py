"""
Generate Retell Agent Specification from Account Memo
Creates complete agent configuration including system prompt
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
    get_timestamp,
    logger
)
from task_tracker import update_task_stage

# Prompt generation template
PROMPT_GENERATION_TEMPLATE = """You are an expert at creating AI agent system prompts for customer service phone systems.

Given the following structured business information, generate a COMPLETE system prompt for a Retell AI phone agent.

**Business Information:**
{memo_json}

**Requirements for the System Prompt:**

1. **Greeting & Introduction**
   - Warm, professional greeting
   - Identify company name
   - Offer help

2. **Information Collection**
   - Collect caller name and phone number EARLY
   - Only ask for additional info needed for routing/dispatch
   - Keep questions minimal and natural

3. **Business Hours Handling**
   - If during business hours: route based on service type
   - Attempt call transfer to appropriate contact
   - If transfer fails: take detailed message and assure callback

4. **After Hours Handling**
   - Greet and acknowledge after-hours call
   - Determine if emergency
   - If emergency: collect name, phone, address, emergency details
   - Attempt emergency contact transfer
   - If transfer fails: assure urgent callback with timeline
   - If non-emergency: take message, set expectation for next business day

5. **Call Transfer Protocol**
   - Never mention "calling a function" or "executing a tool"
   - Say "Let me connect you to [person/department]"
   - Wait {timeout} seconds
   - If fails: gracefully transition to message taking

6. **Closing**
   - Ask "Is there anything else I can help you with?"
   - Thank caller
   - Confirm they have your callback number
   - Professional goodbye

7. **Tone & Style**
   - Professional but friendly
   - Efficient, don't waste caller's time
   - Empathetic, especially for emergencies
   - Clear and direct

8. **Constraints**
   - NEVER mention function calls, tools, or technical system details
   - NEVER create jobs/tickets (just take information)
   - Follow integration constraints: {integration_constraints}

**Generate the complete system prompt now. Return ONLY the prompt text, no explanation or JSON wrapper.**
"""


def generate_system_prompt(memo: Dict[str, Any]) -> str:
    """
    Generate system prompt from account memo
    
    Args:
        memo: Account memo dictionary
    
    Returns:
        Generated system prompt text
    """
    logger.info("Generating system prompt...")
    
    # Format memo as JSON for context
    memo_json = json.dumps(memo, indent=2)
    
    # Get integration constraints
    constraints = memo.get('integration_constraints', [])
    if isinstance(constraints, list):
        constraints = ', '.join(constraints)
    
    # Get timeout from call_transfer_rules
    timeout = memo.get('call_transfer_rules', {}).get('timeout_seconds', 30)
    
    # Format prompt
    prompt = PROMPT_GENERATION_TEMPLATE.format(
        memo_json=memo_json,
        integration_constraints=constraints or "none specified",
        timeout=timeout
    )
    
    # Call LLM
    logger.info(f"Calling LLM to generate prompt...")
    system_prompt = llm_client.call(
        prompt=prompt,
        temperature=0.7
    )
    
    logger.info("System prompt generated successfully")
    return system_prompt.strip()


def build_agent_spec(memo: Dict[str, Any], system_prompt: str) -> Dict[str, Any]:
    """
    Build complete Retell agent specification
    
    Args:
        memo: Account memo
        system_prompt: Generated system prompt
    
    Returns:
        Complete agent specification
    """
    # Extract key info
    company_name = memo.get('company_name', 'Unknown Company')
    account_id = memo.get('account_id', 'unknown')
    
    # Format business hours
    bh = memo.get('business_hours', {})
    if bh:
        days = ', '.join(bh.get('days', []))
        hours_str = f"{days} {bh.get('start', '?')}-{bh.get('end', '?')} {bh.get('timezone', '')}"
    else:
        hours_str = "Not specified"
    
    # Build spec
    spec = {
        "agent_name": f"{company_name} AI Receptionist",
        "agent_id": account_id,
        "voice": {
            "provider": "elevenlabs",
            "voice_id": "sarah",  # Friendly, professional female voice
            "speed": 1.0,
            "temperature": 0.7
        },
        "llm_config": {
            "model": "gpt-3.5-turbo",  # Retell default
            "temperature": 0.7,
            "max_tokens": 500
        },
        "system_prompt": system_prompt,
        "variables": {
            "company_name": company_name,
            "business_hours": hours_str,
            "office_address": memo.get('office_address', ''),
            "services": ', '.join(memo.get('services_supported', [])),
            "emergency_contact": _get_primary_emergency_contact(memo)
        },
        "tools": [
            {
                "name": "transfer_call",
                "description": "Transfer call to appropriate contact",
                "parameters": {
                    "contact_name": "string",
                    "phone_number": "string"
                }
            },
            {
                "name": "take_message",
                "description": "Record message for callback",
                "parameters": {
                    "caller_name": "string",
                    "phone_number": "string",
                    "message": "string",
                    "urgency": "string"
                }
            }
        ],
        "conversation_config": {
            "greeting": _generate_greeting(company_name),
            "max_duration_minutes": 10,
            "enable_interruption": True,
            "end_call_phrases": [
                "anything else",
                "have a great day",
                "goodbye"
            ]
        },
        "call_transfer_config": memo.get('call_transfer_rules', {
            "timeout_seconds": 30,
            "max_retries": 2,
            "transfer_failed_message": "I'm unable to reach them right now. Let me take your information."
        }),
        "version": memo.get('version', 'v1'),
        "created_at": memo.get('created_at', get_timestamp()),
        "notes": "Generated from account memo"
    }
    
    return spec


def _get_primary_emergency_contact(memo: Dict[str, Any]) -> str:
    """Extract primary emergency contact from memo"""
    emergency = memo.get('emergency_routing_rules', {})
    contacts = emergency.get('contacts', {})
    priority = emergency.get('priority_order', [])
    
    if priority and contacts:
        first_contact = priority[0]
        return contacts.get(first_contact, 'Not specified')
    
    return 'Not specified'


def _generate_greeting(company_name: str) -> str:
    """Generate standard greeting"""
    return f"Thank you for calling {company_name}. How can I help you today?"


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Generate Retell agent specification from account memo'
    )
    parser.add_argument(
        'memo_file',
        type=Path,
        help='Path to account memo JSON file'
    )
    parser.add_argument(
        '--output',
        type=Path,
        help='Optional output path for agent spec (default: same directory as memo)'
    )
    parser.add_argument(
        '--prompt-output',
        type=Path,
        help='Optional separate output path for system prompt text file'
    )
    
    args = parser.parse_args()
    
    # Load memo
    if not args.memo_file.exists():
        logger.error(f"Memo file not found: {args.memo_file}")
        sys.exit(1)
    
    memo = load_json(args.memo_file)
    logger.info(f"Loaded memo from {args.memo_file}")
    
    try:
        # Generate system prompt
        system_prompt = generate_system_prompt(memo)
        
        # Build agent spec
        agent_spec = build_agent_spec(memo, system_prompt)
        
        # Determine output paths
        if args.output:
            spec_output = args.output
        else:
            spec_output = args.memo_file.parent / 'agent_spec.json'
        
        if args.prompt_output:
            prompt_output = args.prompt_output
        else:
            prompt_output = args.memo_file.parent / 'system_prompt.txt'
        
        # Save files
        save_json(agent_spec, spec_output)
        write_file(system_prompt, prompt_output)
        
        logger.info("="*60)
        logger.info(f"✓ Agent specification generated successfully")
        logger.info(f"  Agent: {agent_spec['agent_name']}")
        logger.info(f"  Spec: {spec_output}")
        logger.info(f"  Prompt: {prompt_output}")
        logger.info("="*60)
        
        # Update task tracker
        account_id = memo.get('account_id')
        if account_id:
            update_task_stage(account_id, 'v1_agent_created', True,
                            f"Generated agent: {agent_spec['agent_name']}")
        
        # Print sample of prompt
        print("\n" + "="*60)
        print("SYSTEM PROMPT PREVIEW:")
        print("="*60)
        print(system_prompt[:500] + "..." if len(system_prompt) > 500 else system_prompt)
        print("="*60)
        
    except Exception as e:
        logger.error(f"Failed to generate agent spec: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

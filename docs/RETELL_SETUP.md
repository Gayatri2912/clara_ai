# Retell AI Setup Guide

## Creating Your Retell Account

### Step 1: Sign Up

1. Go to [https://retellai.com](https://retellai.com)
2. Click "Sign Up" or "Get Started"
3. Create a free account with your email
4. Verify your email address

### Step 2: Get API Credentials (If Available on Free Tier)

1. Log into your Retell dashboard
2. Navigate to Settings → API Keys
3. Generate a new API key
4. Copy the key and save it securely

**Note**: If the free tier doesn't support API access, proceed with manual import (see below).

## Importing Agent Configuration (Manual Method)

Since programmatic agent creation may not be available on the free tier, follow these steps to manually import your generated agent configuration:

### Step 1: Locate Your Generated Files

After running the pipeline, you'll have these files:
```
outputs/accounts/<account_id>/v1/
  ├── account_memo.json
  ├── agent_spec.json
  └── system_prompt.txt
```

### Step 2: Create Agent in Retell Dashboard

1. Log into Retell dashboard
2. Click "Create New Agent" or "Add Agent"
3. Fill in basic details:
   - **Agent Name**: Copy from `agent_spec.json` → `agent_name`
   - **Description**: "AI receptionist for [Company Name]"

### Step 3: Configure Voice Settings

From `agent_spec.json` → `voice`:
- **Voice Provider**: ElevenLabs (or Retell default)
- **Voice**: Sarah or similar professional female voice
- **Speed**: 1.0 (normal)
- **Temperature**: 0.7

### Step 4: Configure LLM Settings

From `agent_spec.json` → `llm_config`:
- **Model**: GPT-3.5-turbo (or Retell default)
- **Temperature**: 0.7
- **Max Tokens**: 500

### Step 5: Add System Prompt

1. Open `system_prompt.txt`
2. Copy the ENTIRE prompt
3. Paste into the "System Prompt" or "Instructions" field in Retell
4. Review and ensure no truncation occurred

### Step 6: Configure Variables (If Supported)

From `agent_spec.json` → `variables`:
- **Company Name**: [from variables]
- **Business Hours**: [from variables]
- **Office Address**: [from variables]
- **Services**: [from variables]

### Step 7: Set Up Call Transfer Tool (If Available)

If Retell supports custom tools:
1. Add "Transfer Call" function
2. Configure with parameters:
   - `contact_name` (string)
   - `phone_number` (string)

If not supported, the prompt will handle this conversationally.

### Step 8: Configure Conversation Settings

From `agent_spec.json` → `conversation_config`:
- **Greeting**: Copy the greeting message
- **Max Duration**: 10 minutes
- **Enable Interruption**: Yes
- **End Call Phrases**: "anything else", "have a great day"

### Step 9: Test the Agent

1. Click "Test" or "Try it out"
2. Call the test number Retell provides
3. Run through scenarios:
   - Emergency call during business hours
   - Non-emergency call during business hours
   - Emergency call after hours
   - Non-emergency call after hours

### Step 10: Deploy

1. Once testing is successful, click "Deploy" or "Activate"
2. Get your production phone number from Retell
3. Share with client

## Updating to Version 2

When you process an onboarding call and generate v2:

### Option A: Create New Agent Version

1. Follow the same import steps above
2. Use files from `v2/` directory instead of `v1/`
3. Name it "[Company Name] v2" to distinguish
4. Compare behavior with v1

### Option B: Update Existing Agent

1. Open the existing agent in Retell dashboard
2. Update the system prompt with new `v2/system_prompt.txt`
3. Update any changed variables
4. Save as new version (if Retell supports versioning)
5. Test thoroughly before deploying

## Comparing v1 and v2

Use the generated `changelog.md` to identify what changed:

```bash
cat outputs/accounts/<account_id>/v2/changelog.md
```

Pay special attention to:
- Business hours changes
- Emergency routing updates
- New services added
- Call handling procedure modifications

## Troubleshooting

### Issue: Prompt Too Long

**Solution**: Retell may have character limits. If prompt is too long:
1. Open `system_prompt.txt`
2. Remove any excessive examples while keeping core instructions
3. Ensure critical info remains:
   - Business hours
   - Emergency vs non-emergency definition
   - Contact routing order
   - Transfer failure protocol

### Issue: Voice Sounds Unnatural

**Solution**:
1. Try different voice options in Retell
2. Adjust speed (try 0.9 for slower, more clear speech)
3. Adjust temperature (lower = more consistent, higher = more natural variation)

### Issue: Agent Doesn't Follow Instructions

**Solution**:
1. Check that the ENTIRE system prompt was copied
2. Verify no special characters were corrupted
3. Make prompt instructions more explicit
4. Add "You MUST..." statements for critical behaviors

### Issue: Transfer Not Working

**Solution**:
1. Verify phone numbers are in correct format (+1XXXXXXXXXX)
2. Check Retell's call transfer documentation
3. Ensure your Retell plan supports call transfer
4. Test with a known working number first

## API Integration (If Available)

If you gain access to Retell API:

### Update .env

```bash
RETELL_API_KEY=your_api_key_here
RETELL_BASE_URL=https://api.retellai.com/v1
```

### Programmatic Agent Creation

```python
import requests
import json

def create_retell_agent(agent_spec: dict, api_key: str):
    """Create agent via Retell API"""
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        'name': agent_spec['agent_name'],
        'voice': agent_spec['voice'],
        'llm_config': agent_spec['llm_config'],
        'system_prompt': agent_spec['system_prompt'],
        'conversation_config': agent_spec['conversation_config']
    }
    
    response = requests.post(
        'https://api.retellai.com/v1/agents',
        headers=headers,
        json=payload
    )
    
    return response.json()

# Load your generated spec
with open('outputs/accounts/abc_plumbing_001/v1/agent_spec.json') as f:
    spec = json.load(f)

# Create agent
result = create_retell_agent(spec, 'your_api_key')
print(f"Agent created: {result['id']}")
```

## Notes

- Keep a copy of all generated configurations for reference
- Test thoroughly before giving client access
- Document any manual adjustments made in Retell that differ from generated config
- Update the `metadata.json` file with Retell agent ID once deployed

## Support

If you encounter issues:
1. Check Retell documentation: https://docs.retellai.com
2. Review generated `changelog.md` for version differences
3. Compare working vs non-working prompts
4. Reach out to Retell support for platform-specific issues

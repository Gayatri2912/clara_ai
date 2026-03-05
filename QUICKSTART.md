# Quick Start Guide

Get the Clara AI automation pipeline running in under 10 minutes!

## Prerequisites Check

Before starting, ensure you have:

- [ ] Python 3.10 or higher installed
- [ ] pip (Python package manager)
- [ ] Docker Desktop installed (for n8n)
- [ ] Git installed
- [ ] Text editor (VS Code recommended)

Check versions:
```bash
python --version   # Should be 3.10+
pip --version
docker --version
git --version
```

## Step-by-Step Setup

### 1. Navigate to Project Directory

```bash
cd "c:\Users\kaila\Desktop\company"
```

### 2. Create Virtual Environment

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Mac/Linux:**
```bash
python -m venv venv
source venv/bin/activate
```

You should see `(venv)` in your terminal prompt.

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- openai (for OpenRouter compatibility)
- pydantic (data validation)
- requests (API calls)
- python-dotenv (environment variables)
- And other dependencies

### 4. Configure Environment Variables

**Windows:**
```bash
copy .env.example .env
```

**Mac/Linux:**
```bash
cp .env.example .env
```

Edit `.env` file with your preferred text editor:

```bash
# For FREE OpenRouter (recommended for quick start)
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=your_key_here  # Get from https://openrouter.ai
```

**Getting OpenRouter Free API Key:**
1. Go to https://openrouter.ai
2. Sign up (free)
3. Go to Keys section
4. Create new API key
5. Copy and paste into `.env`

**Alternative - Local Ollama (no API key needed, but slower):**
```bash
LLM_PROVIDER=ollama
# First install Ollama from https://ollama.ai
# Then run: ollama pull llama2
```

### 5. Create Required Directories

The scripts will create these automatically, but you can create them now:

```bash
mkdir -p outputs\accounts
mkdir -p logs
mkdir -p database
```

### 6. Test with Sample Data

We've included 2 sample accounts. Let's test with them:

```bash
# Process demo calls (generates v1 agents)
python scripts\batch_process.py --mode demo

# Wait for completion, then process onboarding calls (generates v2)
python scripts\batch_process.py --mode onboarding

# View summary
python scripts\batch_process.py --mode summary
```

### 7. Check Outputs

```bash
# List created accounts
dir outputs\accounts

# View ABC Plumbing v1 outputs
type outputs\accounts\abc_plumbing_and_heating_001\v1\account_memo.json
type outputs\accounts\abc_plumbing_and_heating_001\v1\system_prompt.txt

# View v2 changelog
type outputs\accounts\abc_plumbing_and_heating_001\v2\changelog.md
```

## Testing Individual Commands

### Extract Account Memo from Demo Call

```bash
python scripts\extract_account_memo.py dataset\demo_calls\abc_plumbing_demo.txt
```

**Expected output:**
- `outputs/accounts/abc_plumbing_and_heating_001/v1/account_memo.json` created
- Console shows extracted company name and account ID

### Generate Agent Spec

```bash
python scripts\generate_agent_spec.py outputs\accounts\abc_plumbing_and_heating_001\v1\account_memo.json
```

**Expected output:**
- `agent_spec.json` created in same directory
- `system_prompt.txt` created
- Console shows preview of system prompt

### Update to V2

```bash
python scripts\update_agent_version.py --account-id abc_plumbing_and_heating_001 --onboarding dataset\onboarding_calls\abc_plumbing_onboarding.txt
```

**Expected output:**
- `outputs/accounts/abc_plumbing_and_heating_001/v2/` directory created
- All v2 files generated
- `changelog.md` shows differences
- Console shows changelog preview

## Optional: Start n8n

If you want to use the workflow orchestration:

### 1. Start n8n with Docker

```bash
docker-compose up -d
```

### 2. Access n8n

Open browser to: http://localhost:5678

### 3. Import Workflow

1. Click "Import from File"
2. Select `workflows/n8n-workflow.json`
3. Activate the workflow

### 4. Stop n8n (when done)

```bash
docker-compose down
```

## Troubleshooting

### Error: "No module named 'dotenv'"

**Solution:**
```bash
pip install python-dotenv
```

### Error: "LLM call failed"

**Possible causes:**
1. Invalid API key in `.env`
2. Rate limit exceeded (wait a minute)
3. No internet connection

**Solution:**
```bash
# Check your .env file
type .env

# Try with --help to see options
python scripts\batch_process.py --help

# Use local Ollama instead (no API needed)
# 1. Install Ollama from https://ollama.ai
# 2. Run: ollama pull llama2
# 3. Change .env: LLM_PROVIDER=ollama
```

### Error: "Transcript file not found"

**Solution:**
```bash
# Check files exist
dir dataset\demo_calls
dir dataset\onboarding_calls

# Ensure .txt files are present
```

### Error: "JSON decode error"

This means the LLM returned invalid JSON. Retry the command - it usually works on second attempt due to LLM variability.

### Warning: "No updates found in onboarding call"

This is normal if the onboarding call didn't mention any changes. v2 will be identical to v1.

## Next Steps

### 1. Add Your Own Data

Replace the sample transcripts:
```bash
# Add your 5 demo calls
# Save as: dataset/demo_calls/<company_name>_demo.txt

# Add your 5 onboarding calls  
# Save as: dataset/onboarding_calls/<company_name>_onboarding.txt
```

Naming convention is important for auto-matching!

### 2. Process All Data

```bash
python scripts\batch_process.py --mode all
```

### 3. Review Outputs

Check each account directory:
```bash
dir outputs\accounts
```

Review generated prompts for quality:
```bash
type outputs\accounts\<account_id>\v1\system_prompt.txt
```

### 4. Import to Retell

Follow the guide: `docs\RETELL_SETUP.md`

### 5. Test the Agents

Call the Retell numbers and verify behavior matches expected call handling.

## Daily Usage

Once set up, your typical workflow:

```bash
# Activate environment
venv\Scripts\activate

# Process new demo call
python scripts\extract_account_memo.py dataset\demo_calls\new_company_demo.txt
python scripts\generate_agent_spec.py outputs\accounts\<account_id>\v1\account_memo.json

# Or process new onboarding call
python scripts\update_agent_version.py --account-id <account_id> --onboarding dataset\onboarding_calls\new_company_onboarding.txt

# Or batch process all
python scripts\batch_process.py --mode all
```

## Getting Help

1. **Check logs:**
   ```bash
   type logs\extraction.log
   ```

2. **Review documentation:**
   - `README.md` - Overview
   - `docs/ARCHITECTURE.md` - System design
   - `docs/RETELL_SETUP.md` - Retell integration
   - `docs/TROUBLESHOOTING.md` - Common issues

3. **Test with sample data first** before processing real transcripts

4. **Review generated outputs** to ensure quality before importing to Retell

## Success Checklist

- [ ] Python environment activated
- [ ] Dependencies installed
- [ ] `.env` configured with API key
- [ ] Sample data processed successfully
- [ ] Outputs generated in `outputs/accounts/`
- [ ] System prompts look reasonable
- [ ] Changelogs show correct differences

If all checked, you're ready to process your actual data! 🎉

## Time Estimate

- Setup (steps 1-4): ~5 minutes
- Testing with sample data: ~2 minutes
- Understanding outputs: ~3 minutes
- **Total: ~10 minutes**

Processing time per call:
- Demo call → v1: ~30-60 seconds
- Onboarding → v2: ~30-60 seconds
- 10 calls total: ~10-20 minutes

## Cost

**$0.00** - Everything uses free tiers or local processing!

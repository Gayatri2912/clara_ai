# Clara AI - Zero-Cost Automation Pipeline
## Demo Call → Retell Agent Draft → Onboarding Updates → Agent Revision

## Project Overview

This project automates the creation and updating of Retell AI agent configurations from call transcripts, using **100% free tools**.

### What It Does

1. **Pipeline A**: Processes demo call transcripts → Generates preliminary agent configuration (v1)
2. **Pipeline B**: Processes onboarding call transcripts → Updates agent configuration (v2) with changelog

### Architecture

```
┌─────────────────┐
│  Demo Call      │
│  Transcript     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Extract Data   │
│  (Python Script)│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Account Memo   │
│  JSON (v1)      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Generate Agent │
│  Prompt & Spec  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌──────────────────┐
│  Store v1       │      │  Onboarding Call │
│  Outputs        │      │  Transcript      │
└─────────────────┘      └────────┬─────────┘
                                  │
                                  ▼
                         ┌────────────────────┐
                         │  Extract Updates   │
                         └────────┬────────────┘
                                  │
                                  ▼
                         ┌────────────────────┐
                         │  Merge & Generate  │
                         │  v2 + Changelog    │
                         └─────────────────────┘
```

## Tech Stack (All Free)

- **Orchestration**: n8n (self-hosted via Docker)
- **LLM**: OpenRouter free tier (Google Gemini Flash) or local Ollama
- **Storage**: Local JSON files + SQLite
- **Language**: Python 3.10+
- **Deployment**: Docker Compose

## Project Structure

```
company/
├── README.md                          # This file
├── docker-compose.yml                 # Docker setup for n8n
├── .env.example                       # Environment variables template
├── requirements.txt                   # Python dependencies
├── scripts/
│   ├── extract_account_memo.py       # Extract data from transcripts
│   ├── generate_agent_spec.py        # Generate Retell agent config
│   ├── update_agent_version.py       # Handle v1→v2 updates
│   ├── batch_process.py              # Process all 10 files
│   ├── task_tracker.py               # Task tracking system
│   ├── generate_batch_summary.py     # Batch processing reports
│   ├── backfill_tracker.py           # Backfill existing accounts
│   └── utils.py                      # Helper functions
├── templates/
│   ├── agent_prompt_template.txt     # Base prompt template
│   └── system_instructions.txt       # Retell system instructions
├── workflows/
│   └── n8n_clara_ai_pipeline.json    # n8n workflow export (visual pipeline)
├── dataset/
│   ├── demo_calls/                   # 5 demo call transcripts
│   └── onboarding_calls/             # 5 onboarding call transcripts
├── outputs/
│   ├── task_tracker.json             # Task tracking state
│   ├── batch_summary.json            # Batch processing summary (JSON)
│   ├── batch_summary.md              # Batch processing summary (Markdown)
│   └── accounts/
│       └── <account_id>/
│           ├── v1/
│           │   ├── account_memo.json
│           │   ├── agent_spec.json
│           │   └── system_prompt.txt
│           ├── v2/
│           │   ├── account_memo.json
│           │   ├── agent_spec.json
│           │   ├── system_prompt.txt
│           │   └── changelog.md
│           └── metadata.json
└── database/
    └── accounts.db                   # SQLite tracking database
```

## Quick Start

### Prerequisites

- Docker & Docker Compose installed
- Python 3.10+ installed
- Git installed

### Step 1: Clone and Setup

```bash
cd "c:\Users\kaila\Desktop\company"

# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment variables
copy .env.example .env
# Edit .env and add your OpenRouter API key (free tier)
```

### Step 2: Start n8n

```bash
# Start n8n via Docker
docker-compose up -d

# Access n8n at http://localhost:5678
```

### Step 3: Import n8n Workflow

1. Open http://localhost:5678
2. Create account (local only)
3. Go to Workflows → Import from File
4. Select `workflows/n8n-workflow.json`

### Step 4: Add Dataset

Place your transcripts in:
- `dataset/demo_calls/` (5 files)
- `dataset/onboarding_calls/` (5 files)

Name format: `<company_name>_demo.txt` and `<company_name>_onboarding.txt`

### Step 5: Run Pipeline

```bash
# Process all demo calls (generates v1)
python scripts/batch_process.py --mode demo

# Process all onboarding calls (generates v2)
python scripts/batch_process.py --mode onboarding

# Or process single account
python scripts/batch_process.py --mode demo --account "ABC_Plumbing"
```

## Output Format

### Account Memo JSON

```json
{
  "account_id": "abc_plumbing_001",
  "company_name": "ABC Plumbing",
  "business_hours": {
    "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
    "start": "08:00",
    "end": "17:00",
    "timezone": "America/New_York"
  },
  "office_address": "123 Main St, City, State 12345",
  "services_supported": ["plumbing", "water heater repair", "drain cleaning"],
  "emergency_definition": [
    "water leak",
    "burst pipe",
    "no hot water",
    "sewage backup"
  ],
  "emergency_routing_rules": {
    "priority_order": ["on_call_tech", "manager", "owner"],
    "contacts": {
      "on_call_tech": "+1234567890",
      "manager": "+1234567891",
      "owner": "+1234567892"
    },
    "fallback": "take message and promise callback within 30 minutes"
  },
  "non_emergency_routing_rules": {
    "action": "take_message",
    "fields": ["caller_name", "phone_number", "issue_description"]
  },
  "call_transfer_rules": {
    "timeout_seconds": 30,
    "max_retries": 2,
    "transfer_failed_message": "I'm unable to reach them right now. Let me take your information and ensure someone calls you back shortly."
  },
  "integration_constraints": [
    "never create sprinkler jobs in ServiceTrade"
  ],
  "after_hours_flow_summary": "Check if emergency → collect contact info → attempt transfer → fallback to message",
  "office_hours_flow_summary": "Greet → identify need → collect info → transfer or take message",
  "questions_or_unknowns": [],
  "notes": "Demo call - initial configuration",
  "version": "v1",
  "created_at": "2026-03-04T10:30:00Z"
}
```

### Retell Agent Spec JSON

```json
{
  "agent_name": "ABC Plumbing AI Receptionist",
  "agent_id": "abc_plumbing_001",
  "voice": {
    "provider": "elevenlabs",
    "voice_id": "sarah",
    "speed": 1.0,
    "temperature": 0.7
  },
  "llm_config": {
    "model": "gpt-3.5-turbo",
    "temperature": 0.7,
    "max_tokens": 500
  },
  "system_prompt": "<GENERATED_PROMPT>",
  "variables": {
    "company_name": "ABC Plumbing",
    "business_hours": "Monday-Friday 8am-5pm EST",
    "office_address": "123 Main St, City, State",
    "emergency_contact": "+1234567890"
  },
  "tools": [
    {
      "name": "transfer_call",
      "description": "Transfer call to technician",
      "parameters": ["contact_name", "phone_number"]
    }
  ],
  "conversation_config": {
    "greeting": "Thank you for calling ABC Plumbing, this is Sarah. How can I help you today?",
    "max_duration_minutes": 10,
    "enable_interruption": true,
    "end_call_phrases": ["anything else", "have a great day"]
  },
  "version": "v1",
  "created_at": "2026-03-04T10:30:00Z"
}
```

### Changelog (v1 → v2)

```markdown
# Changelog: ABC Plumbing v1 → v2

**Updated**: 2026-03-04T11:45:00Z

## Changes

### Business Hours
- **Before**: Monday-Friday 8am-5pm
- **After**: Monday-Friday 7am-6pm, Saturday 9am-2pm
- **Reason**: Extended hours mentioned in onboarding call

### Services
- **Added**: "emergency water extraction", "sump pump installation"
- **Reason**: New service offerings discussed in onboarding

### Emergency Routing
- **Changed**: Added secondary on-call number +1234567893
- **Reason**: Backup technician hired

### Prompt Updates
- Added Saturday hours handling
- Updated emergency service list in prompt
- Modified greeting to mention Saturday availability

## Impact
- Agent can now handle Saturday calls correctly
- Expanded service recognition
- Improved emergency routing reliability
```

## Task Tracking & Reporting

### Task Tracker

The project includes an automatic task tracking system that logs the progress of each account through the pipeline:

```bash
# View all tasks summary
python scripts/task_tracker.py summary

# List all tasks
python scripts/task_tracker.py list

# View specific account status
python scripts/task_tracker.py status abc_plumbing_001
```

**Task Stages Tracked:**
- Demo call processed
- v1 agent created
- Onboarding processed
- v2 agent created

**Output:** Task tracker is automatically saved to `outputs/task_tracker.json`

### Batch Processing Reports

Generate comprehensive reports of all processed accounts:

```bash
# Generate batch summary
python scripts/generate_batch_summary.py
```

**Generated Reports:**
- `outputs/batch_summary.json` - Machine-readable summary
- `outputs/batch_summary.md` - Human-readable report

**Report Includes:**
- Total accounts processed
- Pipeline statistics (demo calls, v1/v2 agents created)
- Accounts by status (complete, v1 ready, in progress)
- Output files count

### Backfilling Existing Data

If you've already processed accounts before adding the task tracker:

```bash
# Scan existing outputs and populate tracker
python scripts/backfill_tracker.py
```

## Usage Guide

### Process Individual Account

```bash
# Demo call only
python scripts/extract_account_memo.py dataset/demo_calls/abc_plumbing_demo.txt

# Generate agent
python scripts/generate_agent_spec.py outputs/accounts/abc_plumbing_001/v1/account_memo.json

# Update from onboarding
python scripts/update_agent_version.py \
  --account-id abc_plumbing_001 \
  --onboarding dataset/onboarding_calls/abc_plumbing_onboarding.txt
```

### Batch Processing

```bash
# Process all 10 files automatically
python scripts/batch_process.py --mode all

# View summary
python scripts/batch_process.py --mode summary
```

## Configuration

### Environment Variables (.env)

```bash
# LLM Configuration (choose one)
LLM_PROVIDER=openrouter  # or 'ollama' for local
OPENROUTER_API_KEY=your_free_tier_key_here

# For local Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2

# n8n Configuration
N8N_PORT=5678
N8N_BASIC_AUTH_ACTIVE=false

# Storage
OUTPUT_DIR=outputs/accounts
DATABASE_PATH=database/accounts.db
```

## Testing

### Test with Sample Data

We provide 2 test accounts in `dataset/examples/`:
1. ABC Plumbing (complete demo + onboarding)
2. XYZ HVAC (complete demo + onboarding)

```bash
# Run test
python scripts/batch_process.py --mode demo --account "test"
```

### Verify Outputs

```bash
# Check structure
ls outputs/accounts/

# View generated memo
cat outputs/accounts/abc_plumbing_001/v1/account_memo.json

# View agent spec
cat outputs/accounts/abc_plumbing_001/v1/agent_spec.json
```

## Monitoring & Logs

Logs are stored in `logs/` directory:
- `extraction.log` - Data extraction logs
- `agent_generation.log` - Agent spec generation logs
- `updates.log` - Version update logs

```bash
# View recent logs
tail -f logs/extraction.log
```

## Zero-Cost Guarantee

This solution uses:
- n8n self-hosted (free, local)
- OpenRouter free tier (Google Gemini Flash) OR Ollama (local)
- Local JSON storage (free)
- SQLite (free)
- Python scripts (free)
- Docker (free)

**Total cost: $0.00**

## Known Limitations

1. **Retell API**: Free tier doesn't support programmatic agent creation
   - **Workaround**: We generate the complete agent spec JSON that can be manually imported
   - **Instructions**: See `docs/retell_manual_import.md`

2. **LLM Rate Limits**: Free tier has limits
   - **Workaround**: Built-in retry logic with exponential backoff
   - **Alternative**: Use local Ollama (unlimited, slower)

3. **Transcription**: Not included (assumes transcripts provided)
   - **Alternative**: Add Whisper.cpp for local transcription (see `docs/add_transcription.md`)

## Demo Video

See `demo_video.mp4` or watch on [Loom](#) (to be recorded)

The video demonstrates:
1. Starting the system
2. Processing a demo call → v1 agent
3. Processing onboarding call → v2 agent + changelog
4. Viewing outputs and diffs

## Additional Documentation

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) - Detailed system design
- [`docs/PROMPT_ENGINEERING.md`](docs/PROMPT_ENGINEERING.md) - How prompts are generated
- [`docs/RETELL_SETUP.md`](docs/RETELL_SETUP.md) - Retell account setup
- [`docs/TROUBLESHOOTING.md`](docs/TROUBLESHOOTING.md) - Common issues

## Production Improvements

With production access, I would add:

1. **Real Retell API Integration** - Automated agent deployment
2. **Asana/Linear Integration** - Automatic task creation
3. **Better LLM** - GPT-4 for improved extraction accuracy
4. **Real-time Processing** - Webhook-based triggers
5. **UI Dashboard** - Visual diff viewer and management interface
6. **Audio Processing** - Direct audio file ingestion with Deepgram
7. **Multi-tenant Support** - Handle multiple clients
8. **Automated Testing** - CI/CD pipeline
9. **Monitoring** - Sentry, DataDog integration
10. **Version Control** - Git-based agent versioning

## Contributing

This is an assignment submission, but feedback is welcome!

## License

MIT License - Free to use and modify

## Contact

Created by: [Your Name]
Date: March 4, 2026
Assignment: Clara AI Intern Technical Challenge

---

**Status**: Assignment Complete - All requirements met with zero cost

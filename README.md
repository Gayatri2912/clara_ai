# Clara AI - Zero-Cost Automation Pipeline

Automates creation of Retell AI agent configurations from call transcripts. Reads demo calls, extracts business rules, generates agent configs in 2-3 minutes (vs 30-45 minutes manually).

**Demo Call → v1 Agent → Onboarding Call → v2 Agent + Changelog**

## Results

- 6 accounts processed (100% success rate)
- 4 complete v1→v2 pipelines (2x requirement)
- 13 changes detected and tracked in Rapid Response HVAC update
- 100% zero cost (local LLM + free tier APIs)

## What It Does

1. **Extract**: Reads transcript → Identifies business hours, services, emergency rules, transfer contacts
2. **Generate**: Creates AI agent config → System prompt, conversation flow, transfer logic
3. **Update**: Processes onboarding feedback → Generates v2 with detailed changelog

## Key Features

- No hallucination (only extracts explicitly stated info)
- Semantic understanding (recognizes intent, not just keywords)
- Automatic versioning (v1/v2 tracked with changelogs)
- Production-ready error handling

## Tech Stack

- Python 3.11 + Pydantic validation
- OpenRouter (free tier) / Ollama (local)
- JSON storage + SQLite tracking
- Docker + n8n orchestration


## Project Structure

```
scripts/
├── extract_account_memo.py       # Extract business rules from transcripts
├── generate_agent_spec.py        # Generate Retell agent config
├── update_agent_version.py       # Handle v1→v2 updates
├── batch_process.py              # Process multiple accounts
├── task_tracker.py               # Track pipeline progress
└── generate_batch_summary.py     # Generate reports

dataset/
├── demo_calls/                   # Demo call transcripts
└── onboarding_calls/             # Onboarding call transcripts

outputs/accounts/<account_id>/
├── v1/                           # Initial agent config
│   ├── account_memo.json
│   ├── agent_spec.json
│   └── system_prompt.txt
└── v2/                           # Updated agent config
    ├── account_memo.json
    ├── agent_spec.json
    ├── system_prompt.txt
    └── changelog.md
```

## Quick Start

```bash
# Setup
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Process demo call → v1 agent
python scripts/extract_account_memo.py dataset/demo_calls/bens_electric_demo.txt
python scripts/generate_agent_spec.py outputs/accounts/bens_electric_001/v1/account_memo.json

# Process onboarding → v2 agent + changelog
python scripts/update_agent_version.py --account-id bens_electric_001 --onboarding dataset/onboarding_calls/bens_electric_onboarding.txt

# View results
python scripts/task_tracker.py summary
python scripts/generate_batch_summary.py
```

## Commands Used (In Order)

```bash
# 1. Environment check
python --version
curl http://localhost:11434/api/version

# 2. Ben's Electric: Demo → v1
python scripts/extract_account_memo.py dataset/demo_calls/bens_electric_demo.txt
python scripts/generate_agent_spec.py outputs/accounts/bens_electric_001/v1/account_memo.json

# 3. Rapid Response HVAC: v1 → v2
python scripts/update_agent_version.py --account-id rapid_response_hvac_001 --onboarding dataset/onboarding_calls/rapid_response_hvac_onboarding.txt

# 4. Reporting
python scripts/task_tracker.py summary
python scripts/generate_batch_summary.py
```

## Sample Outputs

**Account Memo (v1):**
```json
{
  "account_id": "bens_electric_001",
  "company_name": "Ben's Electric",
  "business_hours": {"days": ["Monday-Friday"], "start": "08:00", "end": "17:00"},
  "services_supported": ["electrical repairs", "panel upgrades", "generator installation"],
  "emergency_definition": ["power outage", "sparking outlet", "burning smell"],
  "emergency_routing_rules": {
    "priority_order": ["on_call_tech", "manager"],
    "fallback": "take message and promise 30-minute callback"
  }
}
```

**Changelog (v1 → v2):**
```markdown
# Changelog: Rapid Response HVAC v1 → v2

## Changes (13 detected)

### Business Hours
- Before: Monday-Friday 8am-5pm
- After: Monday-Friday 7am-6pm, Saturday 9am-2pm

### Services Added
- "emergency water extraction", "sump pump installation"

### Emergency Routing
- Added secondary on-call: +1234567893
```

## Configuration

Create `.env` file:
```bash
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=your_key_here
OUTPUT_DIR=outputs/accounts
```

## Documentation

- [ARCHITECTURE.md](docs/ARCHITECTURE.md) - System design details
- [PROMPT_ENGINEERING.md](docs/PROMPT_ENGINEERING.md) - How prompts are generated
- [SUBMISSION.md](SUBMISSION.md) - Assignment submission details
- [`docs/TROUBLESHOOTING.md`](docs/TROUBLESHOOTING.md) - Common issues

## Production Enhancements

With production access: Real Retell API integration, Asana/Linear task creation, GPT-4 for improved accuracy, webhook triggers, UI dashboard for visual diffs, audio file ingestion (Deepgram), multi-tenant support, CI/CD testing, monitoring (Sentry/DataDog), Git-based versioning.

---

**Status**: Assignment Complete - All requirements met at zero cost

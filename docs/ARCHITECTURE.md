# System Architecture

## Overview

This system automates the creation and updating of Retell AI agent configurations from call transcripts using a zero-cost tech stack.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Input Layer                          │
│  ┌──────────────────┐         ┌──────────────────────────┐ │
│  │  Demo Call       │         │  Onboarding Call         │ │
│  │  Transcripts     │         │  Transcripts             │ │
│  │  (5 files)       │         │  (5 files)               │ │
│  └────────┬─────────┘         └────────────┬─────────────┘ │
└───────────┼──────────────────────────────────┼──────────────┘
            │                                  │
            ▼                                  ▼
┌─────────────────────────────────────────────────────────────┐
│                    Processing Layer                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Python Scripts                          │  │
│  │  ┌────────────────┐  ┌────────────────────────────┐ │  │
│  │  │ extract_       │  │ generate_agent_spec.py     │ │  │
│  │  │ account_memo   │  │ - Prompt generation        │ │  │
│  │  │ .py            │  │ - Agent config builder     │ │  │
│  │  │ - LLM extract  │  │                            │ │  │
│  │  │ - Validate     │  │                            │ │  │
│  │  │ - Structure    │  │                            │ │  │
│  │  └───────┬────────┘  └────────────┬───────────────┘ │  │
│  │          │                        │                  │  │
│  │          ▼                        ▼                  │  │
│  │  ┌─────────────────────────────────────────────┐   │  │
│  │  │      Account Memo JSON (v1)                  │   │  │
│  │  │  - Business hours, services, routing rules   │   │  │
│  │  └──────────────────┬───────────────────────────┘   │  │
│  │                     │                                │  │
│  │                     ▼                                │  │
│  │  ┌─────────────────────────────────────────────┐   │  │
│  │  │      Agent Spec JSON (v1)                    │   │  │
│  │  │  - System prompt, voice config, tools        │   │  │
│  │  └──────────────────────────────────────────────┘   │  │
│  │                                                      │  │
│  │  ┌────────────────────────────────────────────┐    │  │
│  │  │ update_agent_version.py                     │    │  │
│  │  │ - Compare v1 vs onboarding                  │    │  │
│  │  │ - Extract updates                           │    │  │
│  │  │ - Generate v2 + changelog                   │    │  │
│  │  └────────────────────────────────────────────┘    │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────┐
│                      Storage Layer                          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  outputs/accounts/<account_id>/                      │  │
│  │    ├── v1/                                           │  │
│  │    │   ├── account_memo.json                         │  │
│  │    │   ├── agent_spec.json                           │  │
│  │    │   └── system_prompt.txt                         │  │
│  │    ├── v2/                                           │  │
│  │    │   ├── account_memo.json                         │  │
│  │    │   ├── agent_spec.json                           │  │
│  │    │   ├── system_prompt.txt                         │  │
│  │    │   └── changelog.md                              │  │
│  │    └── metadata.json                                 │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  database/accounts.db (SQLite)                       │  │
│  │  - Account tracking                                  │  │
│  │  - Processing history                                │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────┐
│                  Orchestration Layer (Optional)             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  n8n Workflows                                       │  │
│  │  - Webhook triggers                                  │  │
│  │  - Batch processing                                  │  │
│  │  - Error handling                                    │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────┐
│                      Output Layer                           │
│  ┌──────────────────┐         ┌──────────────────────────┐ │
│  │  Retell Agent    │         │  Manual Import           │ │
│  │  Configuration   │         │  Instructions            │ │
│  │  (JSON Spec)     │         │  + Changelog             │ │
│  └──────────────────┘         └──────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Input Layer

**Supported Formats:**
- Plain text transcripts (.txt)
- JSON transcripts (with speaker labels)
- SRT subtitle files

**Naming Convention:**
- Demo: `<company_name>_demo.txt`
- Onboarding: `<company_name>_onboarding.txt`

### 2. Processing Layer

#### LLM Client (`utils.py`)
- **Purpose**: Unified interface for LLM calls
- **Providers**:
  - OpenRouter (free tier): Google Gemini Flash
  - Ollama (local): Llama2, Mistral, etc.
- **Features**:
  - Automatic retry with exponential backoff
  - Rate limit handling
  - Response parsing and validation

#### Extract Account Memo (`extract_account_memo.py`)
- **Input**: Raw transcript text
- **Output**: Structured JSON with business info
- **Process**:
  1. Load transcript
  2. Identify company name
  3. Send to LLM with extraction prompt
  4. Parse and validate JSON response
  5. Add metadata (account_id, timestamp, version)
  6. Save to `v1/account_memo.json`

**Extraction Schema:**
```json
{
  "account_id": "string",
  "company_name": "string",
  "business_hours": {
    "days": ["array"],
    "start": "HH:MM",
    "end": "HH:MM",
    "timezone": "string"
  },
  "services_supported": ["array"],
  "emergency_definition": ["array"],
  "emergency_routing_rules": {
    "priority_order": ["array"],
    "contacts": {"object"},
    "fallback": "string"
  },
  ...
}
```

#### Generate Agent Spec (`generate_agent_spec.py`)
- **Input**: Account memo JSON
- **Output**: Complete agent specification + system prompt
- **Process**:
  1. Load account memo
  2. Generate system prompt via LLM
  3. Build agent spec structure
  4. Add voice settings, LLM config
  5. Define tools and conversation config
  6. Save both `agent_spec.json` and `system_prompt.txt`

**System Prompt Generation:**
- Includes greeting protocol
- Business hours vs after-hours logic
- Emergency vs non-emergency handling
- Call transfer protocol with fallback
- Natural language, no technical terms
- Empathetic but efficient tone

#### Update Agent Version (`update_agent_version.py`)
- **Input**: v1 memo + onboarding transcript
- **Output**: v2 memo, v2 agent spec, changelog
- **Process**:
  1. Load v1 memo
  2. Send both v1 and onboarding to LLM
  3. Extract updates with reasons
  4. Apply updates to create v2 memo
  5. Regenerate agent spec from v2 memo
  6. Generate detailed changelog
  7. Save all v2 artifacts

**Changelog Format:**
- Field-by-field comparison
- Before/after values
- Reason for each change
- Impact assessment
- Next steps

#### Batch Processor (`batch_process.py`)
- **Purpose**: Process multiple files automatically
- **Modes**:
  - `demo`: Process all demo calls → v1
  - `onboarding`: Process all onboarding calls → v2
  - `all`: Both in sequence
  - `summary`: Show current status
- **Features**:
  - Account matching (demo ↔ onboarding)
  - Progress tracking
  - Error handling per file
  - Batch summary report

### 3. Storage Layer

#### File Structure
```
outputs/accounts/
└── <account_id>/
    ├── metadata.json           # Account metadata
    ├── v1/
    │   ├── account_memo.json   # Structured business info
    │   ├── agent_spec.json     # Complete agent config
    │   └── system_prompt.txt   # System prompt text
    └── v2/
        ├── account_memo.json   # Updated business info
        ├── agent_spec.json     # Updated agent config
        ├── system_prompt.txt   # Updated prompt
        └── changelog.md        # v1→v2 changes
```

#### SQLite Database (Optional)
- **Purpose**: Track processing history
- **Tables**:
  - `accounts`: Account information
  - `processing_runs`: Batch processing history
  - `updates`: Version update log

**Schema:**
```sql
CREATE TABLE accounts (
  account_id TEXT PRIMARY KEY,
  company_name TEXT,
  current_version TEXT,
  created_at TEXT,
  updated_at TEXT
);

CREATE TABLE processing_runs (
  run_id TEXT PRIMARY KEY,
  run_type TEXT,
  started_at TEXT,
  completed_at TEXT,
  accounts_processed INTEGER,
  status TEXT
);
```

### 4. Orchestration Layer

#### n8n Workflows
- **Purpose**: Automate end-to-end pipeline
- **Triggers**:
  - Webhook (demo call uploaded)
  - Webhook (onboarding call uploaded)
  - Schedule (batch process)
- **Nodes**:
  1. Receive webhook
  2. Execute Python script
  3. Check for errors
  4. Send notification
  5. Store results

**Workflow Benefits:**
- Visual pipeline representation
- Error handling and retries
- Notifications on completion
- Logging and monitoring

### 5. Output Layer

#### Retell Integration
- **Method 1**: API (if available)
  - Programmatically create agents
  - Update configurations
  - Deploy automatically
  
- **Method 2**: Manual Import (free tier)
  - Generated JSON spec
  - Copy-paste system prompt
  - Manual configuration in UI

## Data Flow

### Pipeline A: Demo Call → v1 Agent

```
1. User uploads demo_call.txt to dataset/demo_calls/
2. batch_process.py detects new file
3. extract_account_memo.py processes transcript:
   - Calls LLM with extraction prompt
   - Parses structured JSON
   - Validates all required fields
   - Saves to v1/account_memo.json
4. generate_agent_spec.py creates agent:
   - Loads memo
   - Generates system prompt via LLM
   - Builds complete agent spec
   - Saves agent_spec.json and system_prompt.txt
5. metadata.json updated with account info
6. Ready for Retell import
```

### Pipeline B: Onboarding Call → v2 Agent

```
1. User uploads onboarding_call.txt to dataset/onboarding_calls/
2. batch_process.py matches to existing account
3. update_agent_version.py processes:
   - Loads v1 memo
   - Calls LLM to identify changes
   - Applies updates to create v2 memo
   - Regenerates agent spec from v2
   - Generates detailed changelog
4. All v2 artifacts saved to v2/ directory
5. metadata.json updated to show v2 as current
6. Changelog available for review
7. Ready for Retell update
```

## Scalability Considerations

### Current Limits
- **Free LLM tier**: Rate limits apply
- **Local processing**: Single machine
- **Sequential**: Processes one at a time

### Production Improvements
1. **Parallel Processing**: Process multiple accounts concurrently
2. **Queue System**: Redis/Celery for background jobs
3. **API Layer**: REST API for webhook triggers
4. **Caching**: Cache LLM responses for similar queries
5. **Database**: PostgreSQL for better concurrency
6. **Monitoring**: Grafana dashboards for health metrics
7. **Testing**: Automated test suite for prompt quality

## Security & Privacy

### Current Implementation
- All processing local
- No external storage
- Transcripts not sent to third parties (except LLM processing)

### Best Practices
1. **Transcripts**: Keep in private repository
2. **API Keys**: Store in .env, never commit
3. **PII**: Sanitize personal information where possible
4. **Access**: Limit who can access outputs
5. **Cleanup**: Delete old transcripts after processing

## Error Handling

### Retry Logic
- LLM calls: 3 retries with exponential backoff
- File operations: Immediate failure with clear error
- Batch processing: Continue on single failure

### Logging
- INFO: Progress and success messages
- WARNING: Retries and recoverable issues
- ERROR: Failures with stack traces
- All logs saved to `logs/` directory

### Recovery
- Failed extractions: Manual review of transcript
- Invalid JSON: Fallback to template-based extraction
- Missing data: Flag in `questions_or_unknowns` field

## Testing Strategy

### Unit Tests
- Test LLM response parsing
- Test JSON schema validation
- Test diff calculation logic

### Integration Tests
- End-to-end demo → v1 flow
- End-to-end onboarding → v2 flow
- Error scenarios

### Manual Testing
- Review generated prompts for quality
- Test agent behavior with sample calls
- Verify changelog accuracy

## Deployment

### Local Development
```bash
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
python scripts/batch_process.py --mode all
```

### Docker Deployment
```bash
docker-compose up -d
# n8n available at http://localhost:5678
```

### Production (Future)
- Deploy to cloud (AWS/GCP/Azure)
- Use managed services (RDS, S3, etc.)
- Add CI/CD pipeline
- Implement monitoring and alerting

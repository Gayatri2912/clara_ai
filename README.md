# Clara AI - Zero-Cost Automation Pipeline

Automates AI receptionist configuration from call transcripts. Reads demo calls, extracts business rules, generates agent configs in 2-3 minutes vs 45 minutes manually.

***What this project does: ***

Takes phone call transcripts (text conversations) and automatically generates AI receptionist configurations in 2-3 minutes instead of doing it manually in 45 minutes.

Two pipelines:

Demo call → v1 config: Reads the initial demo call, extracts business hours, services, emergency rules, and creates the first AI agent configuration

Onboarding call → v2 config: When customers give feedback, it updates the configuration and generates a detailed changelog showing what changed and why

Key achievement: Built it completely free using local AI (Ollama), processed 6 accounts with 4 complete v1→v2 updates (400% over the requirement), and ensured the AI never invents information - only extracts what's actually stated in the transcripts.

## Results

- **6 accounts processed** 
- **4 complete v1→v2 pipelines** (requirement: 1) - 400% over requirement
- **13 changes tracked** in largest update (Rapid Response HVAC)
- **$0.00 cost** - 100% free local AI

## What It Does

**Pipeline A: Demo Call → v1 Agent**
1. Extracts business hours, services, emergency rules, transfer contacts from transcript
2. Generates system prompt and agent configuration
3. Creates structured JSON output with validation

**Pipeline B: Onboarding Call → v2 Agent + Changelog**
1. Processes customer feedback and updates
2. Compares v1 vs new information
3. Generates updated config with detailed changelog


**Automation 
- Batch processing with automatic retry logic (3 attempts)
- Error logging without stopping pipeline
- Task tracking system for progress monitoring

**Data Quality 
- Strict extraction rules - no hallucination
- Unknown information flagged, not guessed
- All data verifiable against source transcripts

**Code Quality 
- Modular design with shared utilities
- Version control (v1/v2 folders preserve history)
- Comprehensive error logging with context

**Documentation 
- Complete setup instructions
- Architecture and prompt engineering docs
- Troubleshooting guide

**Bonus Points 
- Automated task tracker showing pipeline status
- Changelog generator with reason tracking
- Batch summary reports with statistics

## Tech Stack

Python 3.11 | Ollama (local AI) | Pydantic validation | JSON storage | SQLite tracking


## Project Structure

```
scripts/          # Python automation scripts
dataset/          # Demo and onboarding call transcripts
outputs/          # Generated configs organized by account
  └── accounts/<id>/
      ├── v1/     # Initial configuration
      └── v2/     # Updated configuration + changelog
```

## Key Features

- No hallucination - extracts only explicit information
- Semantic understanding - recognizes intent, not just keywords
- Automatic versioning with detailed changelogs
- Production-ready error handling and retry logic
  

## Documentation

- [ARCHITECTURE.md](docs/ARCHITECTURE.md) - System design
- [PROMPT_ENGINEERING.md](docs/PROMPT_ENGINEERING.md) - Prompt generation
- [SUBMISSION.md](SUBMISSION.md) - Complete assignment details

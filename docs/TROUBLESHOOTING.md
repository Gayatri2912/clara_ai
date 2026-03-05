# Troubleshooting Guide

## Common Issues and Solutions

### Installation Issues

#### Issue: `pip install` fails

**Error:**
```
ERROR: Could not find a version that satisfies the requirement...
```

**Solutions:**
1. Upgrade pip:
   ```bash
   python -m pip install --upgrade pip
   ```

2. Use specific version:
   ```bash
   pip install -r requirements.txt --upgrade
   ```

3. Check Python version:
   ```bash
   python --version  # Must be 3.10+
   ```

#### Issue: Virtual environment won't activate

**Windows Error:**
```
cannot be loaded because running scripts is disabled on this system
```

**Solution:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Mac/Linux Error:**
```
Permission denied
```

**Solution:**
```bash
chmod +x venv/bin/activate
source venv/bin/activate
```

### API and LLM Issues

#### Issue: "OpenRouter API key invalid"

**Solutions:**
1. Check your `.env` file:
   ```bash
   type .env  # Windows
   cat .env   # Mac/Linux
   ```

2. Ensure no extra spaces:
   ```
   OPENROUTER_API_KEY=sk-or-v1-xxxxx  # Correct
   OPENROUTER_API_KEY= sk-or-v1-xxxxx  # WRONG (space before key)
   ```

3. Get new key from https://openrouter.ai/keys

4. Check if key has credits:
   - Log into OpenRouter
   - Check usage page
   - Free tier should show available credits

#### Issue: "Rate limit exceeded"

**Error:**
```
429 Too Many Requests
```

**Solutions:**
1. Wait 60 seconds and retry
2. Add delay between calls in batch processing (already implemented)
3. Switch to local Ollama:
   ```bash
   # Install Ollama from https://ollama.ai
   ollama pull llama2
   
   # Update .env
   LLM_PROVIDER=ollama
   ```

#### Issue: "Cannot connect to Ollama"

**Error:**
```
Connection refused to http://localhost:11434
```

**Solutions:**
1. Start Ollama:
   ```bash
   ollama serve
   ```

2. Check if running:
   ```bash
   curl http://localhost:11434
   # Should return "Ollama is running"
   ```

3. Verify model downloaded:
   ```bash
   ollama list
   # Should show llama2 or mistral
   ```

### Data Processing Issues

#### Issue: "JSONDecodeError: Expecting value"

**Error:**
```
json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
```

**Cause:** LLM returned invalid JSON or no response

**Solutions:**
1. **Retry** - LLMs can be inconsistent:
   ```bash
   # Just run the same command again
   python scripts\extract_account_memo.py [same arguments]
   ```

2. Lower temperature for more consistent output:
   - Edit `scripts/utils.py`
   - Change `temperature=0.7` to `temperature=0.3` in LLM calls

3. Check LLM response in logs:
   ```bash
   type logs\extraction.log
   ```

4. If persistent, increase timeout:
   - Edit `.env`
   - Change `TIMEOUT_SECONDS=30` to `TIMEOUT_SECONDS=60`

#### Issue: "Company name extraction failed"

**Error:**
```
Extracted company name: Unknown Company
```

**Solutions:**
1. **Manual override**: Provide account ID explicitly:
   ```bash
   python scripts\extract_account_memo.py transcript.txt --account-id abc_plumbing_001
   ```

2. **Improve transcript**: Ensure company name appears in first few lines:
   ```
   Thank you for calling ABC Plumbing...
   ```

3. **Edit the memo**: Manually update `account_memo.json` after generation

#### Issue: "No updates found in onboarding call"

**Message:**
```
WARNING: No updates found in onboarding call
```

**This is NOT an error** - it means:
- Onboarding call didn't mention changes, OR
- LLM didn't detect differences, OR
- All information was already captured in demo call

**Solutions:**
1. Review onboarding transcript - does it actually mention changes?
2. If changes ARE mentioned, retry with clearer transcript
3. Manually edit v2 if needed

#### Issue: "Account not found for onboarding"

**Error:**
```
Could not match onboarding file to existing account
```

**Cause:** Naming mismatch between demo and onboarding files

**Solutions:**
1. **Check naming convention**:
   ```
   ✓ Correct:
   abc_plumbing_demo.txt
   abc_plumbing_onboarding.txt
   
   ✗ Wrong:
   abc_demo.txt
   abc_plumbing_onboarding.txt
   ```

2. **Specify account ID explicitly**:
   ```bash
   python scripts\update_agent_version.py \
     --account-id abc_plumbing_001 \
     --onboarding dataset\onboarding_calls\somefile.txt
   ```

3. **Check what accounts exist**:
   ```bash
   dir outputs\accounts
   ```

### File and Path Issues

#### Issue: "File not found"

**Error:**
```
FileNotFoundError: [Errno 2] No such file or directory
```

**Solutions:**
1. **Check current directory**:
   ```bash
   pwd  # Mac/Linux
   cd   # Windows
   
   # Should be: c:\Users\kaila\Desktop\company
   ```

2. **Use absolute paths**:
   ```bash
   python scripts\extract_account_memo.py "C:\Users\kaila\Desktop\company\dataset\demo_calls\file.txt"
   ```

3. **Check file exists**:
   ```bash
   dir dataset\demo_calls
   ```

#### Issue: "Permission denied"

**Error:**
```
PermissionError: [Errno 13] Permission denied
```

**Solutions:**
1. Close files if open in Excel or text editor
2. Check file isn't read-only:
   - Right-click → Properties → Uncheck "Read-only"
3. Run terminal as administrator (Windows)

### Docker and n8n Issues

#### Issue: "Docker daemon not running"

**Error:**
```
Cannot connect to the Docker daemon
```

**Solutions:**
1. Start Docker Desktop application
2. Wait for Docker to fully start (whale icon in system tray)
3. Verify:
   ```bash
   docker ps
   ```

#### Issue: "Port 5678 already in use"

**Error:**
```
Bind for 0.0.0.0:5678 failed: port is already allocated
```

**Solutions:**
1. **Change port** in `docker-compose.yml`:
   ```yaml
   ports:
     - "5679:5678"  # Use 5679 instead
   ```

2. **Kill existing process**:
   ```bash
   # Windows
   netstat -ano | findstr :5678
   taskkill /PID <PID> /F
   
   # Mac/Linux
   lsof -ti:5678 | xargs kill -9
   ```

3. **Stop existing n8n**:
   ```bash
   docker-compose down
   ```

#### Issue: "n8n workflow import fails"

**Solutions:**
1. Check JSON file is valid:
   ```bash
   type workflows\n8n-workflow.json
   ```

2. Use n8n UI import:
   - Settings → Import from File
   - Select `n8n-workflow.json`

3. Manually recreate workflow using UI (simpler for this project)

### Output Quality Issues

#### Issue: "System prompt sounds unnatural"

**Symptoms:**
- Too robotic
- Too verbose
- Mentions technical terms like "function calls"

**Solutions:**
1. **Adjust temperature** - Edit `scripts/generate_agent_spec.py`:
   ```python
   system_prompt = llm_client.call(
       prompt=prompt,
       temperature=0.8  # Higher = more creative (was 0.7)
   )
   ```

2. **Improve extraction** - Better account memo = better prompt
   - Review `v1/account_memo.json`
   - Fix any incorrect extractions
   - Re-generate agent spec

3. **Manual editing** - It's okay to edit `system_prompt.txt` manually!
   - Just document changes in `notes`

#### Issue: "Memo missing critical information"

**Symptoms:**
```json
{
  "business_hours": null,
  "questions_or_unknowns": ["business hours not clear"]
}
```

**Solutions:**
1. **Review transcript** - Is info actually there?
   ```bash
   type dataset\demo_calls\company_demo.txt | findstr "hours"
   ```

2. **Re-extract with better prompt** - Edit `EXTRACTION_PROMPT` in `scripts/extract_account_memo.py`

3. **Manual completion**:
   - Edit `account_memo.json` directly
   - Add missing information
   - Regenerate agent spec:
     ```bash
     python scripts\generate_agent_spec.py outputs\accounts\<id>\v1\account_memo.json
     ```

#### Issue: "Changelog shows incorrect differences"

**Solutions:**
1. **Check v1 and v2 memos**:
   ```bash
   type outputs\accounts\<id>\v1\account_memo.json
   type outputs\accounts\<id>\v2\account_memo.json
   ```

2. **Regenerate v2** with updated onboarding transcript

3. **Manual changelog** - Edit `changelog.md` to reflect actual changes

### Performance Issues

#### Issue: "Processing very slow"

**Causes:**
- Using Ollama locally (slower but free)
- Large transcripts
- Network latency to API

**Solutions:**
1. **Switch to OpenRouter** (faster than local Ollama):
   ```bash
   LLM_PROVIDER=openrouter
   ```

2. **Use faster model** in `.env`:
   ```bash
   OPENROUTER_MODEL=google/gemini-flash-1.5-8b  # Very fast, still free
   ```

3. **Reduce transcript length** - Only include relevant parts

4. **Process in background**:
   ```bash
   python scripts\batch_process.py --mode all > output.log 2>&1 &
   ```

#### Issue: "Running out of memory"

**Solutions:**
1. Close other applications
2. Process accounts one at a time instead of batch
3. Use smaller local model:
   ```bash
   ollama pull llama2:7b  # Smaller than default
   ```

### Validation Issues

#### Issue: "Agent spec missing required fields"

**Solutions:**
1. Check `agent_spec.json` schema matches Retell requirements
2. Review Retell documentation for current API format
3. Manually add any missing required fields

#### Issue: "Phone numbers in wrong format"

**Symptoms:**
```json
"phone_number": "555-0123"  # Missing country code
```

**Solutions:**
1. **Manual fix** in the memo:
   ```json
   "phone_number": "+1-555-0123"
   ```

2. **Add validation** in `utils.py`:
   ```python
   def validate_phone(number):
       if not number.startswith('+'):
           return '+1-' + number
       return number
   ```

## Debugging Tips

### Enable Debug Logging

Edit `.env`:
```bash
DEBUG=true
LOG_LEVEL=DEBUG
```

Then check detailed logs:
```bash
type logs\extraction.log
```

### Test LLM Connection

Create `test_llm.py`:
```python
from scripts.utils import llm_client

response = llm_client.call("Say 'hello world'")
print(response)
```

Run:
```bash
python test_llm.py
```

### Validate JSON Structure

```bash
python -m json.tool outputs\accounts\<id>\v1\account_memo.json
```

If this fails, JSON is invalid.

### Check Environment Variables

```bash
# Windows
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('LLM_PROVIDER'))"

# Should print: openrouter or ollama
```

## Getting Help

If you're still stuck:

1. **Check logs** in `logs/` directory
2. **Review similar working examples** in `outputs/accounts/`
3. **Verify test data works** before trying real data
4. **Simplify** - test one component at a time
5. **Document your error** with full error message and steps to reproduce

## Prevention Best Practices

1. **Test with sample data first** (already provided)
2. **Validate transcripts** before processing
3. **Review outputs** after each step
4. **Keep backups** of working configurations
5. **Document any manual changes** you make
6. **Use version control** (git) for your configurations

## Quick Recovery

If everything is broken:

```bash
# 1. Backup current outputs
mv outputs outputs_backup

# 2. Reset environment
deactivate
rm -rf venv
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# 3. Test with sample data
python scripts\batch_process.py --mode demo

# 4. If it works, you're back on track!
```

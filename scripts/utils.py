"""
Utility functions for Clara AI Automation Pipeline
Handles LLM calls, file operations, and common helpers
"""

import os
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LLMClient:
    """Unified LLM client supporting OpenRouter (free) and Ollama (local)"""
    
    def __init__(self):
        self.provider = os.getenv('LLM_PROVIDER', 'openrouter')
        self.max_retries = int(os.getenv('MAX_RETRIES', 3))
        self.retry_delay = int(os.getenv('RETRY_DELAY', 2))
        
        if self.provider == 'openrouter':
            self.api_key = os.getenv('OPENROUTER_API_KEY')
            self.base_url = os.getenv('OPENROUTER_BASE_URL', 'https://openrouter.ai/api/v1')
            self.model = os.getenv('OPENROUTER_MODEL', 'google/gemini-flash-1.5-8b')
        elif self.provider == 'ollama':
            self.base_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
            self.model = os.getenv('OLLAMA_MODEL', 'llama2')
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")
    
    def call(self, prompt: str, system_prompt: Optional[str] = None, temperature: float = 0.7) -> str:
        """
        Call LLM with retry logic
        
        Args:
            prompt: User prompt
            system_prompt: Optional system instructions
            temperature: Generation temperature (0-1)
        
        Returns:
            LLM response text
        """
        for attempt in range(self.max_retries):
            try:
                if self.provider == 'openrouter':
                    return self._call_openrouter(prompt, system_prompt, temperature)
                elif self.provider == 'ollama':
                    return self._call_ollama(prompt, system_prompt, temperature)
            except Exception as e:
                logger.warning(f"LLM call attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                else:
                    raise
        
        raise Exception("LLM call failed after all retries")
    
    def _call_openrouter(self, prompt: str, system_prompt: Optional[str], temperature: float) -> str:
        """Call OpenRouter API"""
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'HTTP-Referer': 'https://github.com/clara-ai-assignment',
        }
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        data = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=data,
            timeout=int(os.getenv('TIMEOUT_SECONDS', 30))
        )
        response.raise_for_status()
        
        result = response.json()
        return result['choices'][0]['message']['content']
    
    def _call_ollama(self, prompt: str, system_prompt: Optional[str], temperature: float) -> str:
        """Call local Ollama instance"""
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        data = {
            "model": self.model,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": temperature
            }
        }
        
        response = requests.post(
            f"{self.base_url}/api/generate",
            json=data,
            timeout=300  # 5 minutes for large transcripts
        )
        response.raise_for_status()
        
        result = response.json()
        return result['response']


def get_account_id(company_name: str) -> str:
    """
    Generate consistent account ID from company name
    
    Args:
        company_name: Company name
    
    Returns:
        account_id in format: company_name_001
    """
    # Normalize company name
    normalized = company_name.lower().replace(' ', '_').replace('-', '_')
    # Remove special characters
    normalized = ''.join(c for c in normalized if c.isalnum() or c == '_')
    return f"{normalized}_001"


def ensure_dir(path: Path) -> Path:
    """
    Ensure directory exists, create if not
    
    Args:
        path: Directory path
    
    Returns:
        Path object
    """
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_json(data: Dict[Any, Any], filepath: Path) -> None:
    """
    Save dictionary as formatted JSON
    
    Args:
        data: Data to save
        filepath: Target file path
    """
    ensure_dir(filepath.parent)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved JSON to {filepath}")


def load_json(filepath: Path) -> Dict[Any, Any]:
    """
    Load JSON file
    
    Args:
        filepath: Source file path
    
    Returns:
        Parsed JSON data
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def read_file(filepath: Path) -> str:
    """
    Read text file
    
    Args:
        filepath: File path
    
    Returns:
        File contents
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()


def write_file(content: str, filepath: Path) -> None:
    """
    Write text file
    
    Args:
        content: Text content
        filepath: Target file path
    """
    ensure_dir(filepath.parent)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    logger.info(f"Saved file to {filepath}")


def get_timestamp() -> str:
    """Get ISO formatted timestamp"""
    return datetime.utcnow().isoformat() + 'Z'


def get_output_path(account_id: str, version: str = 'v1') -> Path:
    """
    Get output directory path for account
    
    Args:
        account_id: Account identifier
        version: Version (v1 or v2)
    
    Returns:
        Path to account version directory
    """
    output_dir = Path(os.getenv('OUTPUT_DIR', 'outputs/accounts'))
    return output_dir / account_id / version


def extract_company_name_from_transcript(transcript: str) -> str:
    """
    Extract company name from transcript
    Basic heuristic - looks for common patterns
    
    Args:
        transcript: Call transcript
    
    Returns:
        Extracted company name or "Unknown Company"
    """
    # Common patterns
    patterns = [
        "calling ",
        "you've reached ",
        "this is ",
        "welcome to ",
        "thank you for calling "
    ]
    
    lines = transcript.split('\n')
    for line in lines[:10]:  # Check first 10 lines
        line_lower = line.lower()
        for pattern in patterns:
            if pattern in line_lower:
                # Extract text after pattern
                start = line_lower.index(pattern) + len(pattern)
                rest = line[start:].strip()
                # Take first 2-5 words as company name
                words = rest.split()[:5]
                company = ' '.join(words).rstrip('.,!?')
                if len(company) > 3:
                    return company
    
    return "Unknown Company"


def calculate_diff(v1_data: Dict, v2_data: Dict) -> Dict[str, List[Dict[str, Any]]]:
    """
    Calculate differences between two versions
    
    Args:
        v1_data: Version 1 data
        v2_data: Version 2 data
    
    Returns:
        Dictionary of changes by field
    """
    changes = {
        "added": [],
        "removed": [],
        "modified": []
    }
    
    # Find all keys
    all_keys = set(v1_data.keys()) | set(v2_data.keys())
    
    for key in all_keys:
        if key in ['version', 'created_at', 'updated_at']:
            continue  # Skip metadata
        
        if key not in v1_data:
            changes["added"].append({
                "field": key,
                "value": v2_data[key]
            })
        elif key not in v2_data:
            changes["removed"].append({
                "field": key,
                "value": v1_data[key]
            })
        elif v1_data[key] != v2_data[key]:
            changes["modified"].append({
                "field": key,
                "before": v1_data[key],
                "after": v2_data[key]
            })
    
    return changes


def format_changelog(changes: Dict, account_id: str) -> str:
    """
    Format changes as markdown changelog
    
    Args:
        changes: Changes dictionary from calculate_diff
        account_id: Account identifier
    
    Returns:
        Markdown formatted changelog
    """
    lines = [
        f"# Changelog: {account_id} v1 → v2",
        "",
        f"**Updated**: {get_timestamp()}",
        "",
        "## Changes",
        ""
    ]
    
    if changes["added"]:
        lines.append("### Added Fields")
        for change in changes["added"]:
            lines.append(f"- **{change['field']}**: {change['value']}")
        lines.append("")
    
    if changes["removed"]:
        lines.append("### Removed Fields")
        for change in changes["removed"]:
            lines.append(f"- **{change['field']}**: {change['value']}")
        lines.append("")
    
    if changes["modified"]:
        lines.append("### Modified Fields")
        for change in changes["modified"]:
            lines.append(f"\n#### {change['field']}")
            lines.append(f"- **Before**: {change['before']}")
            lines.append(f"- **After**: {change['after']}")
        lines.append("")
    
    if not any([changes["added"], changes["removed"], changes["modified"]]):
        lines.append("No changes detected.")
    
    return '\n'.join(lines)


# Initialize global LLM client
llm_client = LLMClient()

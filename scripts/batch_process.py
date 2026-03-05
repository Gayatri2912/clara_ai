"""
Batch Process Demo and Onboarding Calls
Automates processing of multiple call transcripts
"""

import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any
import sys
import time

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))
from utils import (
    logger,
    get_account_id,
    extract_company_name_from_transcript,
    read_file,
    save_json,
    load_json
)
from extract_account_memo import extract_account_memo
from generate_agent_spec import generate_system_prompt, build_agent_spec
from update_agent_version import extract_updates, apply_updates, generate_detailed_changelog


class BatchProcessor:
    """Batch process demo and onboarding calls"""
    
    def __init__(self, dataset_dir: Path, output_dir: Path):
        self.dataset_dir = dataset_dir
        self.output_dir = output_dir
        self.demo_dir = dataset_dir / 'demo_calls'
        self.onboarding_dir = dataset_dir / 'onboarding_calls'
        self.results = []
    
    def process_demos(self) -> List[Dict[str, Any]]:
        """
        Process all demo calls and generate v1 agents
        
        Returns:
            List of results
        """
        logger.info("="*60)
        logger.info("PROCESSING DEMO CALLS (v1 Generation)")
        logger.info("="*60)
        
        if not self.demo_dir.exists():
            logger.error(f"Demo directory not found: {self.demo_dir}")
            return []
        
        # Find all transcript files
        demo_files = list(self.demo_dir.glob('*.txt'))
        logger.info(f"Found {len(demo_files)} demo call transcripts")
        
        results = []
        for i, demo_file in enumerate(demo_files, 1):
            logger.info(f"\n[{i}/{len(demo_files)}] Processing: {demo_file.name}")
            
            try:
                result = self._process_single_demo(demo_file)
                results.append(result)
                logger.info(f"✓ Success: {result['account_id']}")
                
                # Small delay to avoid rate limits
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"✗ Failed: {demo_file.name} - {e}")
                results.append({
                    'file': demo_file.name,
                    'status': 'failed',
                    'error': str(e)
                })
        
        self._save_batch_summary('demo', results)
        return results
    
    def process_onboardings(self) -> List[Dict[str, Any]]:
        """
        Process all onboarding calls and generate v2 agents
        
        Returns:
            List of results
        """
        logger.info("="*60)
        logger.info("PROCESSING ONBOARDING CALLS (v2 Updates)")
        logger.info("="*60)
        
        if not self.onboarding_dir.exists():
            logger.error(f"Onboarding directory not found: {self.onboarding_dir}")
            return []
        
        # Find all transcript files
        onboarding_files = list(self.onboarding_dir.glob('*.txt'))
        logger.info(f"Found {len(onboarding_files)} onboarding call transcripts")
        
        results = []
        for i, onboarding_file in enumerate(onboarding_files, 1):
            logger.info(f"\n[{i}/{len(onboarding_files)}] Processing: {onboarding_file.name}")
            
            try:
                result = self._process_single_onboarding(onboarding_file)
                results.append(result)
                logger.info(f"✓ Success: {result['account_id']} updated to v2")
                
                # Small delay to avoid rate limits
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"✗ Failed: {onboarding_file.name} - {e}")
                results.append({
                    'file': onboarding_file.name,
                    'status': 'failed',
                    'error': str(e)
                })
        
        self._save_batch_summary('onboarding', results)
        return results
    
    def _process_single_demo(self, demo_file: Path) -> Dict[str, Any]:
        """Process a single demo call"""
        # Read transcript
        transcript = read_file(demo_file)
        
        # Extract company name
        company_name = extract_company_name_from_transcript(transcript)
        account_id = get_account_id(company_name)
        
        logger.info(f"  Company: {company_name}")
        logger.info(f"  Account ID: {account_id}")
        
        # Extract memo
        logger.info("  Extracting account memo...")
        memo = extract_account_memo(transcript, account_id)
        
        # Generate agent spec
        logger.info("  Generating agent specification...")
        system_prompt = generate_system_prompt(memo)
        agent_spec = build_agent_spec(memo, system_prompt)
        
        # Save outputs
        v1_dir = self.output_dir / account_id / 'v1'
        v1_dir.mkdir(parents=True, exist_ok=True)
        
        save_json(memo, v1_dir / 'account_memo.json')
        save_json(agent_spec, v1_dir / 'agent_spec.json')
        
        with open(v1_dir / 'system_prompt.txt', 'w', encoding='utf-8') as f:
            f.write(system_prompt)
        
        # Save metadata
        metadata = {
            'account_id': account_id,
            'company_name': company_name,
            'demo_source': str(demo_file),
            'current_version': 'v1',
            'created_at': memo.get('created_at')
        }
        save_json(metadata, self.output_dir / account_id / 'metadata.json')
        
        return {
            'file': demo_file.name,
            'account_id': account_id,
            'company_name': company_name,
            'status': 'success',
            'version': 'v1',
            'output_dir': str(v1_dir)
        }
    
    def _process_single_onboarding(self, onboarding_file: Path) -> Dict[str, Any]:
        """Process a single onboarding call"""
        # Match to existing account
        account_id = self._match_account_from_filename(onboarding_file.name)
        
        if not account_id:
            raise ValueError(f"Could not match onboarding file to existing account")
        
        logger.info(f"  Matched to account: {account_id}")
        
        # Load v1
        v1_dir = self.output_dir / account_id / 'v1'
        v1_memo_path = v1_dir / 'account_memo.json'
        
        if not v1_memo_path.exists():
            raise FileNotFoundError(f"v1 not found for {account_id}. Run demo processing first.")
        
        v1_memo = load_json(v1_memo_path)
        
        # Read onboarding transcript
        onboarding_transcript = read_file(onboarding_file)
        
        # Extract updates
        logger.info("  Extracting updates...")
        updates = extract_updates(v1_memo, onboarding_transcript)
        logger.info(f"  Found {len(updates)} updates")
        
        # Apply updates
        v2_memo = apply_updates(v1_memo, updates)
        
        # Generate new agent spec
        logger.info("  Generating v2 agent specification...")
        system_prompt_v2 = generate_system_prompt(v2_memo)
        agent_spec_v2 = build_agent_spec(v2_memo, system_prompt_v2)
        
        # Generate changelog
        changelog = generate_detailed_changelog(v1_memo, v2_memo, updates)
        
        # Save v2 outputs
        v2_dir = self.output_dir / account_id / 'v2'
        v2_dir.mkdir(parents=True, exist_ok=True)
        
        save_json(v2_memo, v2_dir / 'account_memo.json')
        save_json(agent_spec_v2, v2_dir / 'agent_spec.json')
        
        with open(v2_dir / 'system_prompt.txt', 'w', encoding='utf-8') as f:
            f.write(system_prompt_v2)
        
        with open(v2_dir / 'changelog.md', 'w', encoding='utf-8') as f:
            f.write(changelog)
        
        # Update metadata
        metadata_path = self.output_dir / account_id / 'metadata.json'
        metadata = load_json(metadata_path)
        metadata['current_version'] = 'v2'
        metadata['onboarding_source'] = str(onboarding_file)
        metadata['updates_count'] = len(updates)
        save_json(metadata, metadata_path)
        
        return {
            'file': onboarding_file.name,
            'account_id': account_id,
            'company_name': v2_memo.get('company_name'),
            'status': 'success',
            'version': 'v2',
            'updates_count': len(updates),
            'output_dir': str(v2_dir)
        }
    
    def _match_account_from_filename(self, filename: str) -> str:
        """
        Match onboarding file to existing account
        Assumes naming convention: <company>_onboarding.txt matches <company>_demo.txt
        """
        # Remove _onboarding.txt suffix
        base_name = filename.replace('_onboarding.txt', '').replace('-onboarding.txt', '')
        
        # Look for matching account
        if self.output_dir.exists():
            for account_dir in self.output_dir.iterdir():
                if account_dir.is_dir():
                    account_id = account_dir.name
                    # Check if base name is in account ID
                    if base_name.lower().replace(' ', '_') in account_id.lower():
                        return account_id
        
        return None
    
    def _save_batch_summary(self, batch_type: str, results: List[Dict[str, Any]]):
        """Save batch processing summary"""
        summary_dir = self.output_dir / '_summaries'
        summary_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        summary_file = summary_dir / f'{batch_type}_batch_{timestamp}.json'
        
        summary = {
            'batch_type': batch_type,
            'timestamp': timestamp,
            'total_files': len(results),
            'successful': len([r for r in results if r.get('status') == 'success']),
            'failed': len([r for r in results if r.get('status') == 'failed']),
            'results': results
        }
        
        save_json(summary, summary_file)
        logger.info(f"\nBatch summary saved to: {summary_file}")
    
    def print_summary(self):
        """Print overall processing summary"""
        logger.info("\n" + "="*60)
        logger.info("BATCH PROCESSING SUMMARY")
        logger.info("="*60)
        
        # Count accounts
        if self.output_dir.exists():
            accounts = [d for d in self.output_dir.iterdir() if d.is_dir() and not d.name.startswith('_')]
            logger.info(f"Total accounts: {len(accounts)}")
            
            for account_dir in sorted(accounts):
                metadata_path = account_dir / 'metadata.json'
                if metadata_path.exists():
                    metadata = load_json(metadata_path)
                    logger.info(f"  - {metadata.get('company_name', 'Unknown')} ({metadata.get('current_version', 'v1')})")


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Batch process demo and onboarding calls'
    )
    parser.add_argument(
        '--mode',
        choices=['demo', 'onboarding', 'all', 'summary'],
        default='all',
        help='Processing mode: demo (v1), onboarding (v2), all (both), or summary (just show status)'
    )
    parser.add_argument(
        '--dataset-dir',
        type=Path,
        default=Path('dataset'),
        help='Path to dataset directory (default: dataset/)'
    )
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=Path('outputs/accounts'),
        help='Path to output directory (default: outputs/accounts/)'
    )
    
    args = parser.parse_args()
    
    processor = BatchProcessor(args.dataset_dir, args.output_dir)
    
    try:
        if args.mode == 'summary':
            processor.print_summary()
        elif args.mode == 'demo':
            processor.process_demos()
            processor.print_summary()
        elif args.mode == 'onboarding':
            processor.process_onboardings()
            processor.print_summary()
        elif args.mode == 'all':
            processor.process_demos()
            logger.info("\n" + "="*60)
            logger.info("Demo processing complete. Starting onboarding processing...")
            logger.info("="*60 + "\n")
            time.sleep(2)
            processor.process_onboardings()
            processor.print_summary()
        
        logger.info("\n" + "="*60)
        logger.info("✓ BATCH PROCESSING COMPLETE")
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"Batch processing failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

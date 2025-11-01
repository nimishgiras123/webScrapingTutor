"""
Jira Scraper - Fetches issue data from Apache Jira
"""

import requests
import json
import os
import time
from datetime import datetime
from typing import Dict, List, Optional
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

from config import (
    JIRA_BASE_URL,
    MAX_RESULTS_PER_PAGE,
    MAX_RETRIES,
    RETRY_WAIT_MIN,
    RETRY_WAIT_MAX,
    RAW_DATA_DIR,
    JIRA_FIELDS
)
from checkpoint_manager import CheckpointManager


class JiraScraper:
    
    def __init__(self, project_key: str):
        self.project_key = project_key
        self.checkpoint_manager = CheckpointManager(project_key)
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
        os.makedirs(RAW_DATA_DIR, exist_ok=True)
        print(f"\n{'='*60}")
        print(f"Initialized scraper for project: {project_key}")
        print(f"{'='*60}\n")
    
    @retry(
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(
            multiplier=1,
            min=RETRY_WAIT_MIN,
            max=RETRY_WAIT_MAX
        ),
        retry=retry_if_exception_type((
            requests.exceptions.RequestException,
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError
        ))
    )
    def _make_request(self, url: str, params: Dict) -> Dict:
        print(f"→ Making request to: {url}")
        print(f"  Parameters: {params}")
        
        response = self.session.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        print(f"✓ Request successful (Status: {response.status_code})")
        return response.json()
    
    def fetch_issues(self, start_at: int = 0) -> Dict:
        url = f"{JIRA_BASE_URL}/search"
        params = {
            'jql': f'project={self.project_key}',
            'fields': ','.join(JIRA_FIELDS),
            'startAt': start_at,
            'maxResults': MAX_RESULTS_PER_PAGE,
            'expand': 'comments'
        }
        
        try:
            data = self._make_request(url, params)
            return data
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                print(f"✗ Rate limited! Waiting 60 seconds...")
                time.sleep(60)
                return self.fetch_issues(start_at)
            raise
    
    def save_raw_data(self, issues: List[Dict], batch_number: int) -> None:
        filename = os.path.join(
            RAW_DATA_DIR,
            f"{self.project_key}_batch_{batch_number}.json"
        )
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(issues, f, indent=2, ensure_ascii=False)
            print(f"✓ Saved {len(issues)} issues to {filename}")
        except Exception as e:
            print(f"✗ Error saving data: {e}")
    
    def scrape_all_issues(self) -> int:
        print(f"Starting scrape for project: {self.project_key}")
        
        start_at = self.checkpoint_manager.get_last_position()
        total_fetched = start_at
        batch_number = start_at // MAX_RESULTS_PER_PAGE
        
        if start_at > 0:
            print(f"ℹ Resuming from position {start_at}")
        
        try:
            print("\n→ Fetching total issue count...")
            first_response = self.fetch_issues(start_at)
            total_issues = first_response['total']
            
            print(f"\n{'='*60}")
            print(f"Project: {self.project_key}")
            print(f"Total issues: {total_issues}")
            print(f"Starting at: {start_at}")
            print(f"Issues remaining: {total_issues - start_at}")
            print(f"{'='*60}\n")
            
            while start_at < total_issues:
                print(f"\n--- Batch {batch_number} ---")
                print(f"Fetching issues {start_at} to {start_at + MAX_RESULTS_PER_PAGE}")
                
                response = self.fetch_issues(start_at)
                issues = response['issues']
                
                if not issues:
                    print("ℹ No more issues to fetch")
                    break
                
                self.save_raw_data(issues, batch_number)
                
                fetched_count = len(issues)
                total_fetched += fetched_count
                start_at += fetched_count
                batch_number += 1
                
                checkpoint_data = {
                    'last_start_at': start_at,
                    'total_fetched': total_fetched,
                    'total_issues': total_issues,
                    'last_updated': datetime.now().isoformat(),
                    'project_key': self.project_key
                }
                self.checkpoint_manager.save_checkpoint(checkpoint_data)
                
                progress = (total_fetched / total_issues) * 100
                print(f"Progress: {total_fetched}/{total_issues} ({progress:.1f}%)")
                
                time.sleep(1)
            
            print(f"\n{'='*60}")
            print(f"✓ Scraping complete for {self.project_key}")
            print(f"Total issues fetched: {total_fetched}")
            print(f"{'='*60}\n")
            
            return total_fetched
        
        except KeyboardInterrupt:
            print(f"\n\n✗ Scraping interrupted by user")
            print(f"Progress saved. You can resume later.")
            return total_fetched
        
        except Exception as e:
            print(f"\n✗ Error during scraping: {e}")
            print(f"Progress saved at position {start_at}")
            raise


if __name__ == "__main__":
    scraper = JiraScraper("KAFKA")
    total = scraper.scrape_all_issues()
    print(f"\nDone! Fetched {total} issues from KAFKA")

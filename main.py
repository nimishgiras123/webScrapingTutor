"""
Main Pipeline - Orchestrates the entire scraping and transformation process
"""

import argparse
import sys
import time
from datetime import datetime

from config import PROJECTS
from scraper import JiraScraper
from transformer import DataTransformer


def scrape_project(project_key: str) -> bool:
    print(f"\n{'#'*70}")
    print(f"# SCRAPING PROJECT: {project_key}")
    print(f"{'#'*70}\n")
    
    try:
        scraper = JiraScraper(project_key)
        total = scraper.scrape_all_issues()
        print(f"\n✓ Successfully scraped {total} issues from {project_key}")
        return True
    except KeyboardInterrupt:
        print(f"\n\n✗ Scraping interrupted by user for {project_key}")
        print(f"Progress has been saved. You can resume later.")
        return False
    except Exception as e:
        print(f"\n✗ Error scraping {project_key}: {e}")
        return False


def transform_project(project_key: str) -> bool:
    print(f"\n{'#'*70}")
    print(f"# TRANSFORMING PROJECT: {project_key}")
    print(f"{'#'*70}\n")
    
    try:
        transformer = DataTransformer(project_key)
        total = transformer.transform_all_batches()
        
        if total > 0:
            print(f"\n✓ Successfully created {total} training examples from {project_key}")
            return True
        else:
            print(f"\n⚠ No data to transform for {project_key}")
            return False
    except Exception as e:
        print(f"\n✗ Error transforming {project_key}: {e}")
        return False


def scrape_all_projects():
    print(f"\n{'='*70}")
    print(f"STARTING SCRAPING PIPELINE")
    print(f"Projects to scrape: {', '.join(PROJECTS)}")
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}\n")
    
    results = {'successful': [], 'failed': []}
    
    for i, project in enumerate(PROJECTS, 1):
        print(f"\n[{i}/{len(PROJECTS)}] Processing {project}...")
        success = scrape_project(project)
        
        if success:
            results['successful'].append(project)
        else:
            results['failed'].append(project)
        
        if i < len(PROJECTS):
            print(f"\n⏸ Waiting 5 seconds before next project...")
            time.sleep(5)
    
    print(f"\n{'='*70}")
    print(f"SCRAPING SUMMARY")
    print(f"{'='*70}")
    print(f"✓ Successful: {len(results['successful'])} projects")
    for project in results['successful']:
        print(f"  - {project}")
    
    if results['failed']:
        print(f"\n✗ Failed: {len(results['failed'])} projects")
        for project in results['failed']:
            print(f"  - {project}")
    
    print(f"\nEnd time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}\n")


def transform_all_projects():
    print(f"\n{'='*70}")
    print(f"STARTING TRANSFORMATION PIPELINE")
    print(f"Projects to transform: {', '.join(PROJECTS)}")
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}\n")
    
    results = {'successful': [], 'failed': []}
    
    for i, project in enumerate(PROJECTS, 1):
        print(f"\n[{i}/{len(PROJECTS)}] Processing {project}...")
        success = transform_project(project)
        
        if success:
            results['successful'].append(project)
        else:
            results['failed'].append(project)
    
    print(f"\n{'='*70}")
    print(f"TRANSFORMATION SUMMARY")
    print(f"{'='*70}")
    print(f"✓ Successful: {len(results['successful'])} projects")
    for project in results['successful']:
        print(f"  - {project}")
    
    if results['failed']:
        print(f"\n✗ Failed: {len(results['failed'])} projects")
        for project in results['failed']:
            print(f"  - {project}")
    
    print(f"\nEnd time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}\n")


def main():
    parser = argparse.ArgumentParser(
        description='Jira Scraper and Transformer Pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                  # Run full pipeline (scrape + transform)
  python main.py --scrape-only    # Only scrape data
  python main.py --transform-only # Only transform existing data
        """
    )
    
    parser.add_argument('--scrape-only', action='store_true', help='Only run scraping pipeline')
    parser.add_argument('--transform-only', action='store_true', help='Only run transformation pipeline')
    
    args = parser.parse_args()
    
    try:
        if args.scrape_only and args.transform_only:
            print("✗ Error: Cannot use both --scrape-only and --transform-only")
            sys.exit(1)
        elif args.scrape_only:
            print("\nRunning SCRAPING pipeline only\n")
            scrape_all_projects()
        elif args.transform_only:
            print("\nRunning TRANSFORMATION pipeline only\n")
            transform_all_projects()
        else:
            print("\nRunning FULL pipeline (scraping + transformation)\n")
            scrape_all_projects()
            print("\n\n" + "="*70)
            print("SCRAPING COMPLETE - STARTING TRANSFORMATION")
            print("="*70 + "\n")
            transform_all_projects()
        
        print("\n✓ Pipeline completed successfully!")
        print("Check the data/ folder for results:\n")
        print("  - data/raw/           → Raw JSON files from Jira")
        print("  - data/processed/     → JSONL files for LLM training")
        print("  - data/checkpoints/   → Progress checkpoints\n")
    
    except KeyboardInterrupt:
        print("\n\n✗ Pipeline interrupted by user")
        print("Progress has been saved. Run again to resume.")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Pipeline failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

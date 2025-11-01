"""
Data Transformer - Converts raw Jira data into JSONL format for LLM training
"""

import json
import os
import re
from typing import Dict, List, Optional
from datetime import datetime

from config import RAW_DATA_DIR, PROCESSED_DATA_DIR


class DataTransformer:
    
    def __init__(self, project_key: str):
        self.project_key = project_key
        os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)
        print(f"\n{'='*60}")
        print(f"Initialized transformer for project: {project_key}")
        print(f"{'='*60}\n")
    
    def clean_text(self, text: Optional[str]) -> str:
        if not text:
            return ""
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        return text
    
    def extract_comments(self, issue: Dict) -> str:
        comments = []
        if 'fields' in issue and 'comment' in issue['fields']:
            comment_data = issue['fields']['comment']
            if 'comments' in comment_data:
                for comment in comment_data['comments']:
                    body = comment.get('body', '')
                    author = comment.get('author', {}).get('displayName', 'Unknown')
                    if body:
                        comments.append(f"{author}: {self.clean_text(body)}")
        return "\n".join(comments)
    
    def get_field_value(self, issue: Dict, field_name: str, nested_key: Optional[str] = None) -> str:
        try:
            fields = issue.get('fields', {})
            value = fields.get(field_name)
            
            if value is None:
                return "Unknown"
            
            if isinstance(value, dict) and nested_key:
                return value.get(nested_key, "Unknown")
            
            if isinstance(value, list):
                return ", ".join(str(v) for v in value)
            
            return str(value)
        except Exception:
            return "Unknown"
    
    def create_summarization_task(self, issue: Dict) -> Dict:
        fields = issue.get('fields', {})
        description = self.clean_text(fields.get('description', ''))
        summary = self.clean_text(fields.get('summary', ''))
        comments = self.extract_comments(issue)
        
        full_input = description
        if comments:
            full_input += f"\n\nComments:\n{comments}"
        
        return {
            "instruction": "Summarize the following Jira issue",
            "input": full_input,
            "output": summary,
            "task_type": "summarization",
            "metadata": {
                "issue_key": issue.get('key', 'Unknown'),
                "project": self.project_key,
                "status": self.get_field_value(issue, 'status', 'name'),
                "priority": self.get_field_value(issue, 'priority', 'name')
            }
        }
    
    def create_classification_task(self, issue: Dict, classify_by: str = "status") -> Dict:
        fields = issue.get('fields', {})
        description = self.clean_text(fields.get('description', ''))
        summary = self.clean_text(fields.get('summary', ''))
        
        full_input = f"Title: {summary}\n\nDescription: {description}"
        
        if classify_by == "status":
            label = self.get_field_value(issue, 'status', 'name')
            instruction = "Classify the status of this Jira issue (e.g., Open, In Progress, Resolved, Closed)"
        elif classify_by == "priority":
            label = self.get_field_value(issue, 'priority', 'name')
            instruction = "Classify the priority of this Jira issue (e.g., Critical, Major, Minor, Trivial)"
        else:
            label = "Unknown"
            instruction = f"Classify the {classify_by} of this Jira issue"
        
        return {
            "instruction": instruction,
            "input": full_input,
            "output": label,
            "task_type": f"classification_{classify_by}",
            "metadata": {
                "issue_key": issue.get('key', 'Unknown'),
                "project": self.project_key,
                "status": self.get_field_value(issue, 'status', 'name'),
                "priority": self.get_field_value(issue, 'priority', 'name')
            }
        }
    
    def create_qa_task(self, issue: Dict) -> Dict:
        fields = issue.get('fields', {})
        summary = self.clean_text(fields.get('summary', ''))
        description = self.clean_text(fields.get('description', ''))
        
        context = f"Title: {summary}\n\nDescription: {description}"
        question = "What is this issue about and what problem does it address?"
        answer = description if description else summary
        full_input = f"{context}\n\nQuestion: {question}"
        
        return {
            "instruction": "Answer the following question about this Jira issue",
            "input": full_input,
            "output": answer,
            "task_type": "qa",
            "metadata": {
                "issue_key": issue.get('key', 'Unknown'),
                "project": self.project_key,
                "status": self.get_field_value(issue, 'status', 'name'),
                "priority": self.get_field_value(issue, 'priority', 'name')
            }
        }
    
    def transform_issue(self, issue: Dict) -> List[Dict]:
        examples = []
        fields = issue.get('fields', {})
        description = fields.get('description', '')
        summary = fields.get('summary', '')
        
        if not description and not summary:
            return examples
        
        try:
            examples.append(self.create_summarization_task(issue))
            examples.append(self.create_classification_task(issue, "status"))
            examples.append(self.create_classification_task(issue, "priority"))
            examples.append(self.create_qa_task(issue))
        except Exception as e:
            print(f"✗ Error transforming issue {issue.get('key', 'Unknown')}: {e}")
        
        return examples
    
    def process_batch_file(self, batch_file: str) -> List[Dict]:
        print(f"→ Processing {batch_file}")
        
        try:
            with open(batch_file, 'r', encoding='utf-8') as f:
                issues = json.load(f)
            
            all_examples = []
            for issue in issues:
                examples = self.transform_issue(issue)
                all_examples.extend(examples)
            
            print(f"✓ Created {len(all_examples)} training examples from {len(issues)} issues")
            return all_examples
        except Exception as e:
            print(f"✗ Error processing batch file: {e}")
            return []
    
    def transform_all_batches(self) -> int:
        print(f"Starting transformation for project: {self.project_key}")
        
        batch_files = []
        for filename in os.listdir(RAW_DATA_DIR):
            if filename.startswith(self.project_key) and filename.endswith('.json'):
                batch_files.append(os.path.join(RAW_DATA_DIR, filename))
        
        batch_files.sort()
        print(f"Found {len(batch_files)} batch files to process")
        
        if not batch_files:
            print(f"✗ No batch files found for {self.project_key}")
            return 0
        
        all_examples = []
        for batch_file in batch_files:
            examples = self.process_batch_file(batch_file)
            all_examples.extend(examples)
        
        output_file = os.path.join(
            PROCESSED_DATA_DIR,
            f"{self.project_key}_training_data.jsonl"
        )
        
        print(f"\n→ Saving to {output_file}")
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                for example in all_examples:
                    json.dump(example, f, ensure_ascii=False)
                    f.write('\n')
            
            print(f"✓ Saved {len(all_examples)} training examples")
            
            pretty_output = os.path.join(
                PROCESSED_DATA_DIR,
                f"{self.project_key}_training_data_pretty.json"
            )
            
            with open(pretty_output, 'w', encoding='utf-8') as f:
                json.dump(all_examples[:10], f, indent=2, ensure_ascii=False)
            
            print(f"✓ Saved first 10 examples to {pretty_output} for inspection")
        except Exception as e:
            print(f"✗ Error saving data: {e}")
            return 0
        
        print(f"\n{'='*60}")
        print(f"✓ Transformation complete for {self.project_key}")
        print(f"Total training examples: {len(all_examples)}")
        print(f"{'='*60}\n")
        
        return len(all_examples)


if __name__ == "__main__":
    transformer = DataTransformer("KAFKA")
    total = transformer.transform_all_batches()
    print(f"\nDone! Created {total} training examples from KAFKA")

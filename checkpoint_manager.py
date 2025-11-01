"""
Checkpoint Manager - Handles saving and loading scraping progress
"""

import json
import os
from typing import Dict, Optional
from config import CHECKPOINT_DIR


class CheckpointManager:
    
    def __init__(self, project_key: str):
        self.project_key = project_key
        self.checkpoint_file = os.path.join(
            CHECKPOINT_DIR, 
            f"{project_key}_checkpoint.json"
        )
        os.makedirs(CHECKPOINT_DIR, exist_ok=True)
    
    def save_checkpoint(self, data: Dict) -> None:
        try:
            with open(self.checkpoint_file, 'w') as f:
                json.dump(data, f, indent=4)
            print(f"✓ Checkpoint saved for {self.project_key}")
        except Exception as e:
            print(f"✗ Error saving checkpoint: {e}")
    
    def load_checkpoint(self) -> Optional[Dict]:
        if not os.path.exists(self.checkpoint_file):
            print(f"ℹ No checkpoint found for {self.project_key}. Starting fresh.")
            return None
        
        try:
            with open(self.checkpoint_file, 'r') as f:
                data = json.load(f)
            print(f"✓ Checkpoint loaded for {self.project_key}")
            print(f"  Last position: {data.get('last_start_at', 0)}")
            return data
        except Exception as e:
            print(f"✗ Error loading checkpoint: {e}")
            print(f"  Starting fresh for {self.project_key}")
            return None
    
    def delete_checkpoint(self) -> None:
        if os.path.exists(self.checkpoint_file):
            try:
                os.remove(self.checkpoint_file)
                print(f"✓ Checkpoint deleted for {self.project_key}")
            except Exception as e:
                print(f"✗ Error deleting checkpoint: {e}")
        else:
            print(f"ℹ No checkpoint to delete for {self.project_key}")
    
    def get_last_position(self) -> int:
        checkpoint = self.load_checkpoint()
        if checkpoint:
            return checkpoint.get('last_start_at', 0)
        return 0


if __name__ == "__main__":
    manager = CheckpointManager("KAFKA")
    
    test_data = {
        "last_start_at": 150,
        "total_fetched": 150,
        "last_updated": "2025-11-02T04:45:00"
    }
    manager.save_checkpoint(test_data)
    
    loaded = manager.load_checkpoint()
    print(f"Loaded data: {loaded}")
    
    position = manager.get_last_position()
    print(f"Last position: {position}")
    
    manager.delete_checkpoint()

"""
Checkpoint Manager - Handles saving and loading research state
"""
import json
import os
from datetime import datetime
from config.config import CHECKPOINT_DIR


class CheckpointManager:
    """Manages research checkpoints for resume capability."""
    
    def __init__(self, checkpoint_name="research_checkpoint"):
        self.checkpoint_dir = CHECKPOINT_DIR
        self.checkpoint_name = checkpoint_name
        self.checkpoint_path = os.path.join(self.checkpoint_dir, f"{checkpoint_name}.json")
        
        # Create checkpoint directory if it doesn't exist
        os.makedirs(self.checkpoint_dir, exist_ok=True)
    
    def save(self, state):
        """
        Save research state to checkpoint file.
        
        Args:
            state (dict): Research state containing:
                - user_prompt
                - research_plan
                - completed_steps
                - all_collected_facts
                - current_step
                - scraped_urls
        """
        checkpoint_data = {
            **state,
            "timestamp": datetime.now().isoformat(),
            "checkpoint_version": "1.0"
        }
        
        with open(self.checkpoint_path, 'w', encoding='utf-8') as f:
            json.dump(checkpoint_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Checkpoint saved: Step {state.get('current_step', 'N/A')}")
    
    def load(self):
        """
        Load research state from checkpoint file.
        
        Returns:
            dict or None: Checkpoint data if exists, None otherwise
        """
        if not os.path.exists(self.checkpoint_path):
            return None
        
        try:
            with open(self.checkpoint_path, 'r', encoding='utf-8') as f:
                checkpoint_data = json.load(f)
            
            print(f"📂 Checkpoint found: {checkpoint_data.get('timestamp', 'Unknown time')}")
            return checkpoint_data
            
        except Exception as e:
            print(f"⚠ Error loading checkpoint: {e}")
            return None
    
    def exists(self):
        """Check if a checkpoint file exists."""
        return os.path.exists(self.checkpoint_path)
    
    def clear(self):
        """Delete the checkpoint file."""
        if os.path.exists(self.checkpoint_path):
            os.remove(self.checkpoint_path)
            print("🗑 Checkpoint cleared")
    
    def get_summary(self):
        """Get a human-readable summary of the checkpoint."""
        checkpoint = self.load()
        if not checkpoint:
            return "No checkpoint found"
        
        summary = []
        summary.append(f"Prompt: {checkpoint.get('user_prompt', 'N/A')[:100]}...")
        summary.append(f"Timestamp: {checkpoint.get('timestamp', 'N/A')}")
        summary.append(f"Current Step: {checkpoint.get('current_step', 'N/A')}")
        summary.append(f"Completed Steps: {checkpoint.get('completed_steps', [])}")
        summary.append(f"Facts Collected: {len(checkpoint.get('all_collected_facts', []))}")
        
        return "\n".join(summary)

"""
API Manager - Handles Gemini API key rotation with rate limit management
"""
import time
import google.generativeai as genai
from config.config import GEMINI_API_KEYS


# Global metrics tracker reference (set by main.py)
_global_metrics_tracker = None

def set_global_metrics_tracker(tracker):
    """Set the global metrics tracker for all API calls."""
    global _global_metrics_tracker
    _global_metrics_tracker = tracker


class GeminiAPIManager:
    """Manages multiple Gemini API keys with automatic rotation on rate limits."""
    
    def __init__(self):
        self.api_keys = [{"key": key, "exhausted": False} for key in GEMINI_API_KEYS]
        self.current_index = 0
        
        if not self.api_keys:
            raise ValueError("No Gemini API keys configured!")
    
    def get_current_key(self):
        """Get the currently active API key."""
        return self.api_keys[self.current_index]["key"]
    
    def mark_current_exhausted(self):
        """Mark current API key as exhausted and rotate to next."""
        self.api_keys[self.current_index]["exhausted"] = True
        print(f"⚠ API Key {self.current_index + 1} exhausted. Rotating...")
        
        # Try to find next available key
        initial_index = self.current_index
        while True:
            self.current_index = (self.current_index + 1) % len(self.api_keys)
            
            # If we've cycled through all keys
            if self.current_index == initial_index:
                if self.api_keys[self.current_index]["exhausted"]:
                    raise Exception("All Gemini API keys exhausted! Please wait or add more keys.")
                break
            
            # Found a non-exhausted key
            if not self.api_keys[self.current_index]["exhausted"]:
                print(f"✓ Switched to API Key {self.current_index + 1}")
                break
    
    def generate_content(self, model_name, system_instruction, user_prompt, 
                        generation_config=None, max_retries=3):
        """
        Generate content with automatic API key rotation on rate limits.
        
        Args:
            model_name (str): Model to use (e.g., 'gemini-2.5-flash')
            system_instruction (str): System instruction for the model
            user_prompt (str): User's prompt
            generation_config (dict): Optional generation configuration
            max_retries (int): Maximum retry attempts across different keys
            
        Returns:
            Response object from the model
        """
        retries = 0
        
        while retries < max_retries:
            try:
                # Configure current API key
                genai.configure(api_key=self.get_current_key())
                
                # Create model
                model = genai.GenerativeModel(
                    model_name=model_name,
                    system_instruction=system_instruction,
                    generation_config=generation_config
                )
                
                # Generate content
                response = model.generate_content(user_prompt)
                
                # Track API call and tokens if global metrics tracker is set
                if _global_metrics_tracker:
                    # Estimate tokens (rough approximation)
                    input_tokens = len(user_prompt.split()) * 1.3
                    output_tokens = len(response.text.split()) * 1.3 if hasattr(response, 'text') else 0
                    total_tokens = int(input_tokens + output_tokens)
                    
                    _global_metrics_tracker.record_api_call(model_name, total_tokens)
                
                return response
                
            except Exception as e:
                error_str = str(e)
                
                # Check if it's a rate limit error (429)
                if "429" in error_str or "quota" in error_str.lower():
                    print(f"⚠ Rate limit hit on Key {self.current_index + 1}")
                    
                    # Track key rotation in metrics
                    if _global_metrics_tracker:
                        _global_metrics_tracker.record_api_key_rotation()
                    
                    try:
                        self.mark_current_exhausted()
                        retries += 1
                        
                        # Extract retry delay if present
                        if "retry" in error_str.lower():
                            # Wait a bit before trying next key
                            time.sleep(1)
                        
                        continue
                        
                    except Exception as rotation_error:
                        # All keys exhausted
                        raise rotation_error
                else:
                    # Non-rate-limit error, re-raise
                    raise e
        
        raise Exception(f"Failed to generate content after {max_retries} retries")
    
    def reset_keys(self):
        """Reset all keys to non-exhausted state."""
        for key_info in self.api_keys:
            key_info["exhausted"] = False
        self.current_index = 0
        print("✓ All API keys reset")
    
    def get_status(self):
        """Get current status of all API keys."""
        status = []
        for i, key_info in enumerate(self.api_keys):
            state = "Exhausted" if key_info["exhausted"] else "Active"
            current = " (current)" if i == self.current_index else ""
            status.append(f"Key {i + 1}: {state}{current}")
        return status


# Global instance for use across modules
gemini_manager = GeminiAPIManager()

"""
GPT Manager - Handles GPT-5 API calls via GitHub Models
"""
from openai import OpenAI
import json
from config.config import GITHUB_TOKENS, GITHUB_ENDPOINT


# Global metrics tracker reference (set by main.py)
_global_metrics_tracker = None

def set_global_metrics_tracker(tracker):
    """Set the global metrics tracker for all API calls."""
    global _global_metrics_tracker
    _global_metrics_tracker = tracker


class GPTManager:
    """Manages GPT-5 API calls through GitHub Models endpoint with token rotation."""
    
    def __init__(self):
        self.tokens = GITHUB_TOKENS if isinstance(GITHUB_TOKENS, list) else [GITHUB_TOKENS]
        self.current_token_index = 0
        self.client = OpenAI(
            base_url=GITHUB_ENDPOINT,
            api_key=self.tokens[self.current_token_index],
        )
        self.model = "gpt-4o"  # Using GPT-4o as fallback if GPT-5 not available
    
    def _rotate_token(self):
        """Rotate to the next GitHub token."""
        self.current_token_index = (self.current_token_index + 1) % len(self.tokens)
        self.client = OpenAI(
            base_url=GITHUB_ENDPOINT,
            api_key=self.tokens[self.current_token_index],
        )
        return self.current_token_index
        
    def generate_content(self, system_instruction, user_prompt, json_mode=True, 
                        temperature=0.5, max_retries=1):
        """
        Generate content using GPT-5 via GitHub Models with token rotation.
        Tries all available GitHub tokens before failing.
        
        Args:
            system_instruction (str): System instruction for the model
            user_prompt (str): User's prompt
            json_mode (bool): Whether to use JSON response format
            temperature (float): Sampling temperature (GitHub Models may ignore this)
            max_retries (int): Maximum retry attempts per token
            
        Returns:
            str: Generated text response
        """
        messages = [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_prompt}
        ]
        
        tokens_tried = 0
        max_tokens_to_try = len(self.tokens)
        
        while tokens_tried < max_tokens_to_try:
            retries = 0
            while retries < max_retries:
                try:
                    # Try GPT-5 first, fall back to GPT-4o if needed
                    # Note: GitHub Models may not support all OpenAI parameters
                    try:
                        # Basic call without temperature or response_format to match working test
                        response = self.client.chat.completions.create(
                            model="gpt-5",
                            messages=messages
                        )
                    except Exception as e:
                        # If GPT-5 fails, use GPT-4o
                        if "gpt-5" in str(e).lower() or "not found" in str(e).lower():
                            print(" GPT-5 not available, using GPT-4o")
                            response = self.client.chat.completions.create(
                                model="gpt-4o",
                                messages=messages
                            )
                        else:
                            raise
                    
                    content = response.choices[0].message.content
                    
                    # Track metrics if available
                    if _global_metrics_tracker:
                        # Get actual token usage from response
                        if hasattr(response, 'usage'):
                            total_tokens = response.usage.total_tokens
                        else:
                            # Estimate if not available
                            input_tokens = len(user_prompt.split()) * 1.3
                            output_tokens = len(content.split()) * 1.3
                            total_tokens = int(input_tokens + output_tokens)
                        
                        model_used = response.model if hasattr(response, 'model') else "gpt-5"
                        _global_metrics_tracker.record_api_call(model_used, total_tokens)
                    
                    return content
                    
                except Exception as e:
                    retries += 1
                    error_str = str(e)
                    
                    # Handle rate limits specially - rotate tokens
                    if "rate limit" in error_str.lower() or "too many requests" in error_str.lower():
                        if retries >= max_retries:
                            # Try next token instead of failing
                            tokens_tried += 1
                            if tokens_tried < max_tokens_to_try:
                                new_index = self._rotate_token()
                                print(f" Token {tokens_tried}/{max_tokens_to_try} rate limited. Rotating to token #{new_index + 1}...")
                                break  # Break inner loop to retry with new token
                            else:
                                print(f" All {max_tokens_to_try} GitHub tokens rate limited.")
                                raise Exception(f"All GitHub tokens rate limited. Fallback to Gemini required.")
                        
                        print(f" Rate limited. Waiting 5 seconds before retry {retries}/{max_retries}...")
                        import time
                        time.sleep(5)
                        retries -= 1  # Don't count this as a retry
                        continue
                    
                    if retries >= max_retries:
                        # Non-rate-limit error after max retries - try next token
                        tokens_tried += 1
                        if tokens_tried < max_tokens_to_try:
                            new_index = self._rotate_token()
                            print(f" Token error. Rotating to token #{new_index + 1}...")
                            break  # Break inner loop to retry with new token
                        else:
                            raise Exception(f"GPT API failed on all {max_tokens_to_try} tokens: {error_str}")
                    
                    print(f" GPT API error (retry {retries}/{max_retries}): {error_str[:100]}")
                    import time
                    time.sleep(1)
        
        raise Exception(f"Failed to generate content after trying all {max_tokens_to_try} GitHub tokens")
    
    def generate_json(self, system_instruction, user_prompt, temperature=0.5):
        """
        Generate JSON response.
        
        Returns:
            dict: Parsed JSON object
        """
        response_text = self.generate_content(
            system_instruction=system_instruction,
            user_prompt=user_prompt,
            json_mode=True,
            temperature=temperature
        )
        
        try:
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            print(f" JSON parse error: {e}")
            print(f"Response: {response_text[:200]}")
            raise


# Global instance for use across modules
gpt_manager = GPTManager()

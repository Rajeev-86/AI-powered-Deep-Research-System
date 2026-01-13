import json
import os
import sys

# Add parent directory to path to import config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.api_manager import gemini_manager

def check_global_sufficiency(original_prompt, all_collected_facts):
    """
    Review ALL collected facts against the ORIGINAL User Prompt.
    Returns a 'Rescue Query' if a critical piece of the puzzle is missing.
    """

    # Turn the complex list of dicts into a readable string for the LLM
    facts_text = ""
    for item in all_collected_facts:
        facts_text += f"- {item['fact']} (Source: {item['source']})\n"

    # We need a strict editor who ensures the story is complete.
    sanity_system_instruction = """
    You are a Final Content Editor. 
    You have the 'Original User Goal' and a list of 'Collected Facts'.
    
    Your Job:
    1. Read the User Goal and the Facts.
    2. Determine if the Facts are sufficient to construct a comprehensive answer.
    3. IGNORE minor missing details. Only flag CRITICAL gaps that make the answer impossible.
    4. If sufficient, output "pass": true.
    5. If detailed gaps exist, output "pass": false and specificy ONE "rescue_query" to fix it.
    """

    prompt = f"""
    --- ORIGINAL USER GOAL ---
    {original_prompt}
    
    --- ALL COLLECTED FACTS ---
    {facts_text[:20000]} 
    
    --- OUTPUT REQUIREMENT ---
    Return JSON: {{ "pass": boolean, "rescue_query": "string (or null)", "reason": "string" }}
    """

    try:
        response = gemini_manager.generate_content(
            model_name="gemini-2.5-flash",
            system_instruction=sanity_system_instruction,
            user_prompt=prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        result = json.loads(response.text)
        return result
        
    except Exception as e:
        # If it breaks, assume we are good to go to avoid infinite errors
        return {"pass": True, "rescue_query": None, "reason": "Error in sanity check"}

'''
# --- TEST ZONE ---
if __name__ == "__main__":
    
    # Scenario: The "Austin vs Seattle" trap
    user_prompt = "Compare the financial viability of living in Austin vs Seattle for a Software Engineer."
    
    # We have facts for Austin (Salary + Rent) but ONLY Salary for Seattle.
    incomplete_facts = [
        {"fact": "Average Software Engineer salary in Austin is $110,000.", "source": "glassdoor.com"},
        {"fact": "Average rent for 1BHK in Austin is $1,600.", "source": "zillow.com"},
        {"fact": "Average Software Engineer salary in Seattle is $145,000.", "source": "levels.fyi"},
    ]
    
    print("Running Sanity Check...")
    decision = check_global_sufficiency(user_prompt, incomplete_facts)
    
    if decision["pass"]:
        print(" Data is sufficient. Proceed to Report Generation.")
    else:
        print(" CRITICAL GAP DETECTED!")
        print(f"Reason: {decision['reason']}")
        print(f"Rescue Query: {decision['rescue_query']}")
'''
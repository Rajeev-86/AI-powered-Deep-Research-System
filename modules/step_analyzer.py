import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.api_manager import gemini_manager

def analyze_step_fulfillment(current_step_instruction, scraped_text, previous_queries):
    """
    Checks if the CURRENT STEP is satisfied by the scraped text.
    Ensures new queries do not repeat previous failures.
    """

    # We explicitly tell it to focus on the STEP, not the global goal.
    judge_system_instruction = """
    You are a Task Completion Judge. 
    You are given a 'Current Step' from a larger plan and 'Scraped Data'.
    
    Your Job:
    1. Determine if the 'Scraped Data' contains the information required by the 'Current Step'.
    2. If YES: Output "step_completed": true.
    3. If NO: Output "step_completed": false and generate a NEW, UNIQUE search query.
    
    CRITICAL RULES:
    - Focus ONLY on the Current Step. Do not worry about the Main Goal.
    - Check the 'Previous Queries' list. You MUST NOT generate a query that is semantically similar to one already used.
    - If the Previous Queries list is long and we are still failing, try a completely different angle or keyword.
    """

    prompt = f"""
    --- CURRENT STEP OBJECTIVE ---
    {current_step_instruction}
    
    --- PREVIOUS QUERIES TRIED (DO NOT REPEAT) ---
    {json.dumps(previous_queries)}
    
    --- SCRAPED DATA FOUND ---
    {scraped_text[:12000]} 
    
    --- OUTPUT REQUIREMENT ---
    Return JSON: {{ "step_completed": boolean, "reason": "string", "new_query": "string (or null)" }}
    """

    try:
        response = gemini_manager.generate_content(
            model_name="gemini-2.5-flash",
            system_instruction=judge_system_instruction,
            user_prompt=prompt,
            generation_config={"response_mime_type": "application/json", "temperature": 0.2}
        )
        decision = json.loads(response.text)
        return decision
        
    except Exception as e:
        # Fail safe
        return {"step_completed": False, "reason": f"Error: {e}", "new_query": None}

'''
# --- TEST ZONE ---
if __name__ == "__main__":
    
    # Scenario: We are on Step 3 of a plan to buy a house.
    step_instruction = "Find the current home loan interest rates for HDFC Bank in India for 2025."
    
    # The agent already tried a generic query and got generic results
    past_queries = ["HDFC home loan interest rate"]
    
    # The scraping results (Simulated: Marketing fluff, no numbers)
    scraped_content = """
    HDFC Bank offers competitive interest rates on home loans. 
    Apply today to unlock your dream home! Our rates are tailored to your credit score.
    (No actual percentage mentioned)
    """
    
    print(f"Goal: {step_instruction}")
    print(f"Past Queries: {past_queries}\n")
    
    decision = analyze_step_fulfillment(step_instruction, scraped_content, past_queries)
    
    print(f"Step Completed? {decision['step_completed']}")
    if not decision['step_completed']:
        print(f"Reason: {decision['reason']}")
        print(f"New Smart Query: {decision['new_query']}")
'''
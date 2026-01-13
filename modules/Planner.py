import os
import sys
import json
import datetime

# Add parent directory to path to import config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.gpt_manager import gpt_manager
from utils.api_manager import gemini_manager

def planner(user_prompt: str) -> dict:

    today_date = datetime.date.today().strftime("%B %d, %Y")

    planner_system_instruction = f"""
You are a Senior Research Architect. Current Date: {today_date}

Your goal is NOT to answer the user's question directly, 
but to create a comprehensive, step-by-step research plan to answer it thoroughly.
You must prioritize recent data (late 2024, 2025) over older data.

For every user request, you must generate a JSON object containing:
1. "main_objective": A clear restatement of the goal.
2. "steps": A list of steps, where each step has:
    - "step_number": The order of execution.
    - "action": What needs to be done (e.g., "Compare X and Y", "Find statistics on Z").
    - "search_queries": A list of 2-3 specific Google search queries to execute this step.
    - "reasoning": Why this step is critical.

Keep the plan between 4-8 distinct steps.
Return ONLY valid JSON, no other text.
"""

    print(" Attempting GPT-5 for strategic planning...\n")
    
    try:
        # Try GPT-5 first
        research_plan = gpt_manager.generate_json(
            system_instruction=planner_system_instruction,
            user_prompt=user_prompt,
            temperature=0.5
        )
        
        print(f" Used GPT-5 for planning")
        
    except Exception as gpt_error:
        # Fallback to Gemini if GPT-5 fails (rate limit, etc.)
        print(f"  GPT-5 unavailable ({str(gpt_error)[:60]}...)")
        print(" Falling back to Gemini 2.5 Flash for planning...\n")
        
        try:
            response = gemini_manager.generate_content(
                model_name="gemini-2.5-flash",
                system_instruction=planner_system_instruction,
                user_prompt=user_prompt,
                generation_config={"response_mime_type": "application/json", "temperature": 0.5}
            )
            research_plan = json.loads(response.text)
            print(f" Used Gemini Flash as fallback")
            
        except Exception as gemini_error:
            print(f" Both GPT-5 and Gemini failed!")
            print(f"   GPT-5 error: {str(gpt_error)[:100]}")
            print(f"   Gemini error: {str(gemini_error)[:100]}")
            return None
    
    # Display the plan
    print(f"\n OBJECTIVE: {research_plan['main_objective']}\n")
    print("-" * 50)
    
    for step in research_plan['steps']:
        print(f"Step {step['step_number']}: {step['action']}")
        print(f"   Why: {step['reasoning']}")
        print(f"    Queries to Run: {step['search_queries']}")
        print("-" * 50)

    return research_plan


def refine_plan(original_plan: dict, user_feedback: str) -> dict:
    """
    Refine an existing research plan based on user feedback.
    
    Args:
        original_plan (dict): The original research plan
        user_feedback (str): User's suggestions, modifications, or additions
        
    Returns:
        dict: The refined research plan
    """
    today_date = datetime.date.today().strftime("%B %d, %Y")
    
    refiner_system_instruction = f"""
You are a Senior Research Architect. Current Date: {today_date}

You are refining a research plan based on user feedback.
The user has reviewed the initial plan and provided suggestions for improvement.

Your task:
1. Understand the user's feedback carefully
2. Modify the research plan accordingly:
   - Add new steps if requested
   - Remove or merge steps if suggested
   - Adjust search queries to be more specific
   - Reorder steps if needed
   - Modify step objectives to match user priorities
3. Maintain the same JSON structure
4. Keep the plan between 4-10 distinct steps
5. Prioritize recent data (late 2024, 2025) over older data

Return ONLY valid JSON with the same structure:
{{
  "main_objective": "...",
  "steps": [
    {{
      "step_number": 1,
      "action": "...",
      "search_queries": [...],
      "reasoning": "..."
    }}
  ]
}}
"""

    refinement_prompt = f"""
--- ORIGINAL PLAN ---
{json.dumps(original_plan, indent=2)}

--- USER FEEDBACK ---
{user_feedback}

--- INSTRUCTIONS ---
Refine the research plan based on the user's feedback.
Maintain all required fields and return valid JSON.
"""

    print("\n Refining plan based on your feedback...\n")
    
    try:
        # Try GPT-5 first
        refined_plan = gpt_manager.generate_json(
            system_instruction=refiner_system_instruction,
            user_prompt=refinement_prompt,
            temperature=0.5
        )
        print(f" Used GPT-5 for plan refinement")
        
    except Exception as gpt_error:
        # Fallback to Gemini
        print(f"  GPT-5 unavailable, using Gemini...")
        
        try:
            response = gemini_manager.generate_content(
                model_name="gemini-2.5-flash",
                system_instruction=refiner_system_instruction,
                user_prompt=refinement_prompt,
                generation_config={"response_mime_type": "application/json", "temperature": 0.5}
            )
            refined_plan = json.loads(response.text)
            print(f" Used Gemini Flash for plan refinement")
            
        except Exception as gemini_error:
            print(f" Plan refinement failed!")
            print(f"   Keeping original plan...")
            return original_plan
    
    # Display the refined plan
    print(f"\n REFINED OBJECTIVE: {refined_plan['main_objective']}\n")
    print("-" * 50)
    
    for step in refined_plan['steps']:
        print(f"Step {step['step_number']}: {step['action']}")
        print(f"   Why: {step['reasoning']}")
        print(f"    Queries: {step['search_queries']}")
        print("-" * 50)
    
    return refined_plan

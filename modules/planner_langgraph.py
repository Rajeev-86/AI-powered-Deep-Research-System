"""
LangGraph-Enhanced Plan Refinement Module

Uses LangGraph for the interactive planning refinement loop while keeping
the rest of the system's optimized direct implementation.

This module ONLY handles:
1. Interactive plan refinement with conversation memory
2. Multi-model fallback routing (GPT-5 → Gemini)
3. State management for the planning phase

Everything else (parallel execution, caching, streaming) stays as-is.
"""

from typing import TypedDict, Annotated, Literal
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
import operator
import datetime
import json

from utils.gpt_manager import gpt_manager
from utils.api_manager import gemini_manager


# State definition for the planning graph
class PlanningState(TypedDict):
    """State for the interactive planning process"""
    user_prompt: str
    current_plan: dict
    refinement_history: Annotated[list, operator.add]  # Accumulate refinements
    user_feedback: str
    iteration: int
    status: Literal["planning", "refining", "approved", "cancelled"]
    model_used: str


def create_initial_plan(state: PlanningState) -> PlanningState:
    """
    Node: Generate initial research plan using GPT-5 or Gemini fallback
    """
    user_prompt = state["user_prompt"]
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
        model_used = "GPT-5"
        print(f" Used GPT-5 for planning")
        
    except Exception as gpt_error:
        # Fallback to Gemini
        print(f"️  GPT-5 unavailable ({str(gpt_error)[:60]}...)")
        print(" Falling back to Gemini 2.5 Flash for planning...\n")
        
        response = gemini_manager.generate_content(
            model_name="gemini-2.5-flash",
            system_instruction=planner_system_instruction,
            user_prompt=user_prompt,
            generation_config={"response_mime_type": "application/json", "temperature": 0.5}
        )
        research_plan = json.loads(response.text)
        model_used = "Gemini Flash"
        print(f" Used Gemini Flash as fallback")
    
    # Display the plan
    print(f"\n OBJECTIVE: {research_plan['main_objective']}\n")
    print("-" * 50)
    
    for step in research_plan['steps']:
        print(f"Step {step['step_number']}: {step['action']}")
        print(f"   Why: {step['reasoning']}")
        print(f"    Queries to Run: {step['search_queries']}")
        print("-" * 50)
    
    return {
        **state,
        "current_plan": research_plan,
        "iteration": 1,
        "status": "planning",
        "model_used": model_used
    }


def get_user_feedback(state: PlanningState) -> PlanningState:
    """
    Node: Get user feedback on the plan
    """
    print("\n" + "="*70)
    print("\n Would you like to modify this plan?")
    print("   - Type your feedback to refine the plan")
    print("   - Type 'start' or press Enter to begin research")
    print("   - Type 'quit' to exit")
    print("\n" + "="*70)
    
    user_input = input("\n Your response: ").strip()
    
    if not user_input or user_input.lower() == 'start':
        return {**state, "status": "approved"}
    elif user_input.lower() == 'quit':
        return {**state, "status": "cancelled"}
    else:
        return {
            **state,
            "user_feedback": user_input,
            "status": "refining"
        }


def refine_plan(state: PlanningState) -> PlanningState:
    """
    Node: Refine the plan based on user feedback
    """
    original_plan = state["current_plan"]
    user_feedback = state["user_feedback"]
    iteration = state["iteration"]
    
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
    
    print(f"\n Refining plan based on your feedback (iteration {iteration})...\n")
    
    try:
        # Try GPT-5 first
        refined_plan = gpt_manager.generate_json(
            system_instruction=refiner_system_instruction,
            user_prompt=refinement_prompt,
            temperature=0.5
        )
        model_used = "GPT-5"
        print(f" Used GPT-5 for plan refinement")
        
    except Exception as gpt_error:
        # Fallback to Gemini
        print(f"️  GPT-5 unavailable, using Gemini...")
        
        response = gemini_manager.generate_content(
            model_name="gemini-2.5-flash",
            system_instruction=refiner_system_instruction,
            user_prompt=refinement_prompt,
            generation_config={"response_mime_type": "application/json", "temperature": 0.5}
        )
        refined_plan = json.loads(response.text)
        model_used = "Gemini Flash"
        print(f" Used Gemini Flash for plan refinement")
    
    # Display the refined plan
    print(f"\n REFINED OBJECTIVE: {refined_plan['main_objective']}\n")
    print("-" * 50)
    
    for step in refined_plan['steps']:
        print(f"Step {step['step_number']}: {step['action']}")
        print(f"   Why: {step['reasoning']}")
        print(f"    Queries: {step['search_queries']}")
        print("-" * 50)
    
    return {
        **state,
        "current_plan": refined_plan,
        "refinement_history": [(iteration, user_feedback, model_used)],
        "iteration": iteration + 1,
        "status": "planning",
        "model_used": model_used
    }


def should_continue_planning(state: PlanningState) -> Literal["get_feedback", "end"]:
    """
    Conditional edge: Determine if we should continue planning or end
    """
    status = state["status"]
    
    if status in ["approved", "cancelled"]:
        return "end"
    else:
        return "get_feedback"


# Build the LangGraph
def create_planning_graph():
    """
    Create the interactive planning state graph
    
    Flow:
    1. create_initial_plan → get_user_feedback
    2. If user provides feedback → refine_plan → get_user_feedback (loop)
    3. If user approves/quits → END
    """
    workflow = StateGraph(PlanningState)
    
    # Add nodes
    workflow.add_node("create_initial_plan", create_initial_plan)
    workflow.add_node("get_feedback", get_user_feedback)
    workflow.add_node("refine", refine_plan)
    
    # Define edges
    workflow.set_entry_point("create_initial_plan")
    workflow.add_edge("create_initial_plan", "get_feedback")
    
    # Conditional routing from get_feedback
    workflow.add_conditional_edges(
        "get_feedback",
        should_continue_planning,
        {
            "get_feedback": "get_feedback",  # Loop back for approval
            "end": END
        }
    )
    
    # After refinement, go back to get feedback
    workflow.add_edge("refine", "get_feedback")
    
    # Special handling: if status is "refining", go to refine node
    def route_after_feedback(state: PlanningState) -> Literal["refine", "end"]:
        if state["status"] == "refining":
            return "refine"
        return "end"
    
    workflow.add_conditional_edges(
        "get_feedback",
        route_after_feedback,
        {
            "refine": "refine",
            "end": END
        }
    )
    
    # Compile with memory (for conversation history)
    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory)
    
    return app


# Main function for external use (replaces the original planner + refine_plan)
def interactive_planner(user_prompt: str) -> dict:
    """
    Run the interactive planning process with LangGraph.
    
    This replaces the original planner() and manual refinement loop.
    
    Args:
        user_prompt (str): The user's research question
        
    Returns:
        dict: The final approved research plan, or None if cancelled
    """
    # Create the graph
    app = create_planning_graph()
    
    # Initial state
    initial_state = {
        "user_prompt": user_prompt,
        "current_plan": {},
        "refinement_history": [],
        "user_feedback": "",
        "iteration": 0,
        "status": "planning",
        "model_used": ""
    }
    
    # Run the graph with a unique thread ID for conversation memory
    config = {"configurable": {"thread_id": "planning_session"}}
    
    # Execute the graph
    final_state = None
    for state in app.stream(initial_state, config):
        final_state = state
    
    # Extract final state (LangGraph returns dict of dicts)
    if final_state:
        # Get the actual state from the last node
        final_node_state = list(final_state.values())[0]
        
        if final_node_state["status"] == "approved":
            print("\n Starting research with approved plan...\n")
            return final_node_state["current_plan"]
        elif final_node_state["status"] == "cancelled":
            print("\n Research cancelled by user.")
            return None
    
    return None


# For testing
if __name__ == "__main__":
    test_prompt = "What are the latest advances in quantum computing?"
    plan = interactive_planner(test_prompt)
    
    if plan:
        print("\n" + "="*70)
        print("FINAL APPROVED PLAN:")
        print("="*70)
        print(json.dumps(plan, indent=2))

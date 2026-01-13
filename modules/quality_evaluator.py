"""
Quality Evaluator Module

Evaluates the quality of collected research data across multiple dimensions:
- Completeness: Does it answer the step objective?
- Technical Depth: Are there code examples, API details, implementation specifics?
- Source Quality: Official docs vs blogs vs Reddit?
- Recency: Is data from 2024-2025 or outdated?
"""

import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.api_manager import gemini_manager


def evaluate_research_quality(
    step_objective: str,
    extracted_facts: list,
    sources: list,
    iteration: int = 1
) -> dict:
    """
    Evaluates the quality of research collected for a specific step.
    
    Args:
        step_objective (str): The goal of the current research step
        extracted_facts (list): List of fact dictionaries with 'fact' and 'source' keys
        sources (list): List of source URLs that were scraped
        iteration (int): Current iteration number for context
        
    Returns:
        dict: {
            "completeness": float (0-1),
            "technical_depth": float (0-1),
            "source_quality": float (0-1),
            "recency": float (0-1),
            "overall_score": float (0-1),
            "threshold_met": bool,
            "missing_aspects": list[str],
            "reasoning": str
        }
    """
    
    current_year = datetime.now().year
    
    system_instruction = f"""
You are a Research Quality Auditor. Current year: {current_year}.

Your task is to evaluate research quality across 4 dimensions (scale 0.0 to 1.0):

1. COMPLETENESS (0.0-1.0):
   - 1.0: Fully answers the step objective with comprehensive details
   - 0.7: Answers most aspects but missing some details
   - 0.4: Partial answer, significant gaps remain
   - 0.0: Does not address the objective

2. TECHNICAL_DEPTH (0.0-1.0):
   - 1.0: Contains code examples, API schemas, implementation patterns, specific configurations
   - 0.7: Has technical details but lacks code/examples
   - 0.4: Only high-level concepts, no implementation specifics
   - 0.0: Pure marketing/conceptual content

3. SOURCE_QUALITY (0.0-1.0):
   - 1.0: Official documentation, academic papers, GitHub repos, technical blogs
   - 0.7: Reputable tech news sites, established blogs
   - 0.4: General websites, medium.com articles
   - 0.0: Reddit threads, quora, marketing pages

4. RECENCY (0.0-1.0):
   - 1.0: Information from {current_year} or {current_year-1}
   - 0.7: Information from {current_year-2}
   - 0.4: Information from {current_year-3} or older
   - 0.0: Severely outdated (pre-2020)

Calculate OVERALL_SCORE as weighted average:
- Completeness: 40%
- Technical Depth: 30%
- Source Quality: 20%
- Recency: 10%

THRESHOLD_MET: True if overall_score >= 0.7

MISSING_ASPECTS: List specific things needed to reach 1.0 (e.g., "Python code examples", "API authentication details", "Error handling patterns")

Return valid JSON only.
"""

    # Prepare facts summary
    facts_summary = "\n".join([
        f"- {fact.get('fact', 'N/A')[:200]}... [Source: {fact.get('source', 'Unknown')}]"
        for fact in extracted_facts[:30]  # Limit to avoid token overflow
    ])
    
    # Prepare sources summary
    sources_summary = "\n".join([f"- {url}" for url in sources[:20]])
    
    prompt = f"""
--- STEP OBJECTIVE ---
{step_objective}

--- ITERATION ---
This is iteration {iteration} of research for this step.

--- EXTRACTED FACTS ({len(extracted_facts)} total) ---
{facts_summary}

--- SOURCES USED ({len(sources)} total) ---
{sources_summary}

--- EVALUATION REQUIRED ---
Evaluate the quality of this research and identify what's missing.

Return JSON:
{{
  "completeness": float,
  "technical_depth": float,
  "source_quality": float,
  "recency": float,
  "overall_score": float,
  "threshold_met": boolean,
  "missing_aspects": [list of specific missing items],
  "reasoning": "Brief explanation of the scores"
}}
"""

    try:
        response = gemini_manager.generate_content(
            model_name="gemini-2.5-flash",
            system_instruction=system_instruction,
            user_prompt=prompt,
            generation_config={
                "response_mime_type": "application/json",
                "temperature": 0.3
            }
        )
        
        evaluation = json.loads(response.text)
        
        # Display evaluation results
        print(f"\n   Quality Evaluation (Iteration {iteration}):")
        print(f"     Completeness:     {evaluation['completeness']:.2f}")
        print(f"     Technical Depth:  {evaluation['technical_depth']:.2f}")
        print(f"     Source Quality:   {evaluation['source_quality']:.2f}")
        print(f"     Recency:          {evaluation['recency']:.2f}")
        print(f"     ───────────────────────────────")
        print(f"     Overall Score:    {evaluation['overall_score']:.2f}")
        
        if evaluation['threshold_met']:
            print(f"      Quality threshold met!")
        else:
            print(f"     ️  Below threshold (0.70)")
            if evaluation.get('missing_aspects'):
                print(f"     Missing: {', '.join(evaluation['missing_aspects'][:3])}")
        
        return evaluation
        
    except Exception as e:
        print(f"  ️  Quality evaluation error: {e}")
        # Return conservative default evaluation
        return {
            "completeness": 0.5,
            "technical_depth": 0.5,
            "source_quality": 0.5,
            "recency": 0.5,
            "overall_score": 0.5,
            "threshold_met": False,
            "missing_aspects": ["Evaluation failed - assuming incomplete"],
            "reasoning": f"Error during evaluation: {str(e)}"
        }


def identify_knowledge_gaps(
    step_objective: str,
    extracted_facts: list,
    missing_aspects: list,
    previous_queries: list
) -> list:
    """
    Generates highly specific refined search queries to fill knowledge gaps.
    
    Args:
        step_objective (str): The goal of the current step
        extracted_facts (list): Facts collected so far
        missing_aspects (list): Specific missing items from quality evaluation
        previous_queries (list): Queries already tried (to avoid repetition)
        
    Returns:
        list: 2-3 highly specific refined search queries
    """
    
    system_instruction = """
You are a Search Query Specialist for technical research.

Your task: Generate 2-3 HIGHLY SPECIFIC search queries to fill knowledge gaps.

CRITICAL RULES:
1. DO NOT repeat or rephrase previous queries
2. Target EXACTLY what's missing (e.g., if missing "code examples", search for "code example github")
3. Prioritize queries that will return:
   - Official documentation
   - GitHub repositories
   - Technical tutorials with code
   - API references
4. Use technical keywords: "API", "SDK", "implementation", "tutorial", "github", "documentation"
5. Avoid generic terms: "overview", "introduction", "what is"

Return valid JSON only: {"refined_queries": [list of 2-3 queries]}
"""

    facts_brief = "\n".join([
        f"- {fact.get('fact', '')[:150]}"
        for fact in extracted_facts[:15]
    ])
    
    prompt = f"""
--- STEP OBJECTIVE ---
{step_objective}

--- WHAT WE ALREADY FOUND ---
{facts_brief}

--- WHAT'S STILL MISSING ---
{', '.join(missing_aspects)}

--- QUERIES ALREADY TRIED (DO NOT REPEAT) ---
{', '.join(previous_queries)}

--- TASK ---
Generate 2-3 NEW, HIGHLY SPECIFIC queries that will find EXACTLY what's missing.
Focus on official docs, GitHub repos, and technical tutorials.

Return JSON: {{"refined_queries": ["query1", "query2", "query3"]}}
"""

    try:
        response = gemini_manager.generate_content(
            model_name="gemini-2.5-flash",
            system_instruction=system_instruction,
            user_prompt=prompt,
            generation_config={
                "response_mime_type": "application/json",
                "temperature": 0.7  # Higher temp for creative query generation
            }
        )
        
        result = json.loads(response.text)
        refined_queries = result.get('refined_queries', [])
        
        print(f"\n   Refined Queries Generated:")
        for i, query in enumerate(refined_queries, 1):
            print(f"     {i}. {query}")
        
        return refined_queries
        
    except Exception as e:
        print(f"  ️  Query refinement error: {e}")
        # Fallback: Create basic refined query
        return [f"{step_objective} detailed implementation guide"]


# Test function
if __name__ == "__main__":
    # Test evaluation
    test_facts = [
        {"fact": "Gemini uses agentic systems", "source": "https://gemini.google.com"},
        {"fact": "Has 1M token context window", "source": "https://ai.google.dev"}
    ]
    
    test_sources = [
        "https://gemini.google.com/overview",
        "https://reddit.com/r/GeminiAI"
    ]
    
    evaluation = evaluate_research_quality(
        step_objective="Find Python SDK implementation details for Gemini Deep Research",
        extracted_facts=test_facts,
        sources=test_sources,
        iteration=1
    )
    
    print("\n" + "="*50)
    print(json.dumps(evaluation, indent=2))
    
    # Test gap identification
    if not evaluation['threshold_met']:
        refined = identify_knowledge_gaps(
            step_objective="Find Python SDK implementation details",
            extracted_facts=test_facts,
            missing_aspects=evaluation['missing_aspects'],
            previous_queries=["Gemini deep research", "Google AI Studio API"]
        )
        print("\n" + "="*50)
        print("Refined Queries:", refined)

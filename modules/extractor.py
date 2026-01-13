import json
import os
import sys

# Add parent directory to path to import config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.api_manager import gemini_manager

def extract_key_info(query, raw_text, source_url):
    """
    Reads the raw text and extracts ONLY the facts relevant to the query.
    Attaches the source URL to every extracted fact for citation.
    """

    # Enhanced extraction for technical research
    extractor_system_instruction = """
    You are a Technical Information Extraction Specialist optimized for deep research.
    
    EXTRACTION PRIORITIES (in order):
    1. **Code Examples**: Extract any code snippets, API calls, configuration examples, command-line usage
    2. **Technical Specifications**: Architecture details, algorithms, data structures, system designs
    3. **Implementation Details**: Step-by-step procedures, installation instructions, integration patterns
    4. **Quantitative Data**: Statistics, benchmarks, performance metrics, version numbers, dates
    5. **API/SDK Information**: Function signatures, parameter details, response formats, authentication methods
    6. **Dependencies**: Required libraries, versions, system requirements, compatibility notes
    
    EXTRACTION RULES:
    - Preserve technical accuracy: Keep function names, variable names, URLs exactly as written
    - Include context: "The X function takes Y parameter" not just "X function exists"
    - Extract code blocks verbatim (maintain formatting if possible)
    - Capture comparative statements: "X is faster than Y by 30%"
    - Include error messages, edge cases, limitations if mentioned
    - Ignore: Marketing language, generic introductions, author bios, unrelated content
    
    OUTPUT FORMAT:
    JSON with "key_findings" array. Each finding should be:
    - Self-contained (readable without the source)
    - Specific (not "supports authentication" but "supports OAuth 2.0 and API key authentication")
    - Technical (prioritize implementation over theory)
    
    If no relevant technical information found, return empty array.
    """

    # We limit text length to ~30k chars to stay safe on tokens, though Flash handles more.
    prompt = f"""
    --- USER QUERY ---
    {query}
    
    --- SOURCE URL ---
    {source_url}
    
    --- RAW TEXT CONTENT ---
    {raw_text[:30000]}
    
    --- OUTPUT FORMAT ---
    Return JSON: {{ "key_findings": ["fact 1", "fact 2", ...] }}
    """

    try:
        # Use Flash-lite for extraction (faster, pattern matching task)
        response = gemini_manager.generate_content(
            model_name="gemini-2.5-flash-lite",
            system_instruction=extractor_system_instruction,
            user_prompt=prompt,
            generation_config={"response_mime_type": "application/json", "temperature": 0.1}
        )
        data = json.loads(response.text)
        
        findings = data.get("key_findings", [])

        # We attach the URL here programmatically so the LLM doesn't have to hallucinate it.
        cited_findings = []
        for fact in findings:
            cited_findings.append({
                "fact": fact,
                "source": source_url
            })
            
        return cited_findings
    except Exception as e:
        print(f"Extraction Error for {source_url}: {e}")
        return []

'''
# --- TEST ZONE ---
if __name__ == "__main__":
    # Context: The Planner asked us to find population stats.
    query = "What is the population of Tokyo in 2024 and 2025?"
    
    # Simulated Scraped Text (Mix of useful info and fluff)
    scraped_text = """
    Welcome to our travel blog! Tokyo is a beautiful city with amazing food. 
    As of late 2024, the Tokyo metropolitan area population is estimated at 37.1 million.
    However, projections for 2025 suggest a slight decline to 37.0 million due to aging demographics.
    You should definitely visit the Shibuya crossing!
    """
    
    url = "https://example-travel-blog.com/tokyo"
    
    print(f"Extracting facts for: '{query}'...")
    results = extract_key_info(query, scraped_text, url)
    
    print("\n--- EXTRACTED DATA ---")
    print(json.dumps(results, indent=2))
'''
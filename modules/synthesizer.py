import os
import datetime
import sys
import json

# Add parent directory to path to import config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.gpt_manager import gpt_manager
from utils.api_manager import gemini_manager


def generate_research_report_streaming(user_prompt, all_verified_facts):
    """
    Generate research report with streaming output (real-time display).
    Shows report as it's being generated for better user experience.
    
    Args:
        user_prompt (str): Original research question
        all_verified_facts (list): List of verified facts with sources
        
    Returns:
        str: Complete research report with citations
    """
    print("\n  Generating report with streaming output...\n")
    print("="*70)
    
    # Deduplicate sources
    url_to_citation = {}
    citation_counter = 1
    
    for item in all_verified_facts:
        source_url = item['source']
        if source_url not in url_to_citation:
            url_to_citation[source_url] = citation_counter
            citation_counter += 1
    
    # Serialize facts with deduplicated citations
    evidence_text = ""
    for i, item in enumerate(all_verified_facts, 1):
        citation_num = url_to_citation[item['source']]
        evidence_text += f"[{i}] Fact: {item['fact']}\n    Citation: [^{citation_num}]\n"
    
    # Create references section
    references_text = "\n\n## References\n\n"
    for url, citation_num in sorted(url_to_citation.items(), key=lambda x: x[1]):
        references_text += f"[^{citation_num}]: {url}\n"
    
    writer_system_instruction = f"""
You are a Senior Technical Research Writer specializing in comprehensive technical documentation.
Current Date: {datetime.date.today().strftime("%B %d, %Y")}

WRITING OBJECTIVE:
Transform research evidence into a professional, in-depth technical report that would satisfy:
- Software engineers seeking implementation details
- Researchers requiring architectural understanding
- Technical leads evaluating technologies

STRUCTURAL REQUIREMENTS:

1. **Executive Summary** (2-3 paragraphs):
   - High-level overview of findings
   - Key technical insights
   - Main conclusions

2. **Introduction** (1-2 sections):
   - Context and background
   - Scope of analysis
   - Methodology note (if relevant)

3. **Technical Architecture** (multiple subsections):
   - System components and their interactions
   - Data flow and processing pipelines
   - Core algorithms or approaches
   - Use technical diagrams in text if describing architecture

4. **Implementation Details** (deepest section):
   - Step-by-step procedures
   - Code examples (preserve exactly as found in evidence)
   - Configuration examples
   - API usage patterns
   - Command-line instructions
   - Integration patterns

5. **Technical Specifications**:
   - Performance characteristics
   - System requirements
   - Compatibility notes
   - Limitations and constraints

6. **Critical Analysis**:
   - Trade-offs and design decisions
   - Comparison with alternatives (if applicable)
   - Known issues or limitations
   - Best practices and recommendations

7. **Conclusion**:
   - Summary of key technical insights
   - Implementation readiness assessment
   - Future considerations

TECHNICAL WRITING RULES:

**Code Formatting**:
- Use code blocks with language tags: ```python, ```bash, ```json
- Preserve code exactly as it appears in evidence
- Include installation commands, imports, and configuration
- Show both minimal and complete examples when available

**Technical Precision**:
- Use exact terminology (don't paraphrase technical terms)
- Include version numbers when mentioned
- Specify parameter types and return values
- Reference specific functions, classes, modules by name
- Include error codes and messages if discussed

**Evidence Integration**:
- EVERY technical claim must cite evidence with footnote [^N]
- Group related citations: [^1, 2, 3]
- Prioritize primary sources (official docs, papers) over blogs
- If evidence contradicts, present both views with citations

**Depth vs Breadth**:
- For "how to implement" queries: Prioritize step-by-step detail
- For "architecture" queries: Focus on system design and component interaction
- For "comparison" queries: Provide detailed technical criteria
- Always include code/configuration examples if available in evidence

**Language Style**:
- Professional but accessible (explain acronyms on first use)
- Active voice for procedures: "Install the library" not "The library should be installed"
- Present tense for current state: "The system uses" not "The system used"
- Past tense for historical context or experiments

CITATION FORMAT:
- Each fact in the evidence is already assigned a citation number: [^N]
- Use these exact citation numbers when referencing facts
- You can combine multiple citations: [^1, 2, 3] or [^1][^2][^3]
- DO NOT create your own citation numbers - use only the ones provided with each fact
- DO NOT create a References section - it will be appended automatically

QUALITY CRITERIA:
 A developer could begin implementation using only this report
 Code examples are directly usable (copy-paste ready)
 Technical terminology is precise and consistent
 Architecture is explained at multiple levels (overview → detail)
 Every factual statement has a citation
 Report anticipates and answers technical "how" questions

OUTPUT FORMAT: Markdown with proper headings, code blocks, and citations.
"""

    prompt = f"""
--- RESEARCH TOPIC ---
{user_prompt}

--- AVAILABLE EVIDENCE ---
{evidence_text}

--- INSTRUCTIONS ---
Write the final technical report following the structure defined in the system instruction.

IMPORTANT CITATION RULES:
- Each fact includes its citation number: [^N]
- Use ONLY these pre-assigned citation numbers when referencing facts
- Example: If Fact 5 has "Citation: [^2]", use [^2] when citing that fact
- You can combine citations: [^1, 2, 3] for multiple sources supporting one claim
- DO NOT create a References section - it will be appended automatically

SPECIFIC GUIDANCE:
1. Start with an Executive Summary that captures the core technical insights
2. Include code examples verbatim from evidence - preserve formatting
3. Use proper section hierarchy: Overview before deep-dive details
4. If the topic involves implementation: Provide step-by-step procedures
5. If the topic involves architecture: Explain components and their interactions
6. Every technical claim must cite the provided evidence using the citation numbers
7. Do NOT create your own References section

Focus on technical depth and actionable information. A developer should be able to understand and implement based on this report alone.
"""

    # Try GPT-5 with streaming
    try:
        from openai import OpenAI
        from config.config import GITHUB_TOKENS, GITHUB_ENDPOINT
        
        client = OpenAI(base_url=GITHUB_ENDPOINT, api_key=GITHUB_TOKENS[0])
        
        # Create streaming request
        stream = client.chat.completions.create(
            model="gpt-4o",  # Use GPT-4o as it's more reliable than GPT-5
            messages=[
                {"role": "system", "content": writer_system_instruction},
                {"role": "user", "content": prompt}
            ],
            stream=True
        )
        
        # Collect chunks and display in real-time
        report_chunks = []
        for chunk in stream:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                print(content, end='', flush=True)
                report_chunks.append(content)
        
        report = ''.join(report_chunks)
        print("\n" + "="*70)
        print(" Streaming synthesis complete!")
        
        # Append references
        return report + references_text
        
    except Exception as streaming_error:
        # Fallback to non-streaming if streaming fails
        print(f"\n  Streaming failed: {str(streaming_error)[:60]}...")
        print(" Falling back to non-streaming synthesis...\n")
        return generate_research_report(user_prompt, all_verified_facts)

def generate_research_report(user_prompt, all_verified_facts):
    """
    Takes the user's original query and a list of verified facts.
    Synthesizes them into a professional Markdown report with footnotes.
    """

    # Deduplicate sources: create a URL -> citation_number mapping
    url_to_citation = {}
    citation_counter = 1
    
    for item in all_verified_facts:
        source_url = item['source']
        if source_url not in url_to_citation:
            url_to_citation[source_url] = citation_counter
            citation_counter += 1
    
    # Serialize facts with their deduplicated citation numbers
    evidence_text = ""
    for i, item in enumerate(all_verified_facts, 1):
        citation_num = url_to_citation[item['source']]
        evidence_text += f"[{i}] Fact: {item['fact']}\n    Citation: [^{citation_num}]\n"
    
    # Create the references section with deduplicated URLs
    references_text = "\n\n## References\n\n"
    for url, citation_num in sorted(url_to_citation.items(), key=lambda x: x[1]):
        references_text += f"[^{citation_num}]: {url}\n"

    writer_system_instruction = f"""
You are a Senior Technical Research Writer specializing in comprehensive technical documentation.
Current Date: {datetime.date.today().strftime("%B %d, %Y")}

WRITING OBJECTIVE:
Transform research evidence into a professional, in-depth technical report that would satisfy:
- Software engineers seeking implementation details
- Researchers requiring architectural understanding
- Technical leads evaluating technologies

STRUCTURAL REQUIREMENTS:

1. **Executive Summary** (2-3 paragraphs):
   - High-level overview of findings
   - Key technical insights
   - Main conclusions

2. **Introduction** (1-2 sections):
   - Context and background
   - Scope of analysis
   - Methodology note (if relevant)

3. **Technical Architecture** (multiple subsections):
   - System components and their interactions
   - Data flow and processing pipelines
   - Core algorithms or approaches
   - Use technical diagrams in text if describing architecture

4. **Implementation Details** (deepest section):
   - Step-by-step procedures
   - Code examples (preserve exactly as found in evidence)
   - Configuration examples
   - API usage patterns
   - Command-line instructions
   - Integration patterns

5. **Technical Specifications**:
   - Performance characteristics
   - System requirements
   - Compatibility notes
   - Limitations and constraints

6. **Critical Analysis**:
   - Trade-offs and design decisions
   - Comparison with alternatives (if applicable)
   - Known issues or limitations
   - Best practices and recommendations

7. **Conclusion**:
   - Summary of key technical insights
   - Implementation readiness assessment
   - Future considerations

TECHNICAL WRITING RULES:

**Code Formatting**:
- Use code blocks with language tags: ```python, ```bash, ```json
- Preserve code exactly as it appears in evidence
- Include installation commands, imports, and configuration
- Show both minimal and complete examples when available

**Technical Precision**:
- Use exact terminology (don't paraphrase technical terms)
- Include version numbers when mentioned
- Specify parameter types and return values
- Reference specific functions, classes, modules by name
- Include error codes and messages if discussed

**Evidence Integration**:
- EVERY technical claim must cite evidence with footnote [^N]
- Group related citations: [^1, 2, 3]
- Prioritize primary sources (official docs, papers) over blogs
- If evidence contradicts, present both views with citations

**Depth vs Breadth**:
- For \"how to implement\" queries: Prioritize step-by-step detail
- For \"architecture\" queries: Focus on system design and component interaction
- For \"comparison\" queries: Provide detailed technical criteria
- Always include code/configuration examples if available in evidence

**Language Style**:
- Professional but accessible (explain acronyms on first use)
- Active voice for procedures: \"Install the library\" not \"The library should be installed\"
- Present tense for current state: \"The system uses\" not \"The system used\"
- Past tense for historical context or experiments

CITATION FORMAT:
- Each fact in the evidence is already assigned a citation number: [^N]
- Use these exact citation numbers when referencing facts
- You can combine multiple citations: [^1, 2, 3] or [^1][^2][^3]
- DO NOT create your own citation numbers - use only the ones provided with each fact
- DO NOT create a References section - it will be appended automatically

QUALITY CRITERIA:
 A developer could begin implementation using only this report
 Code examples are directly usable (copy-paste ready)
 Technical terminology is precise and consistent
 Architecture is explained at multiple levels (overview → detail)
 Every factual statement has a citation
 Report anticipates and answers technical \"how\" questions

OUTPUT FORMAT: Markdown with proper headings, code blocks, and citations.
"""

    prompt = f"""
--- RESEARCH TOPIC ---
{user_prompt}

--- AVAILABLE EVIDENCE ---
{evidence_text}

--- INSTRUCTIONS ---
Write the final technical report following the structure defined in the system instruction.

IMPORTANT CITATION RULES:
- Each fact includes its citation number: [^N]
- Use ONLY these pre-assigned citation numbers when referencing facts
- Example: If Fact 5 has "Citation: [^2]", use [^2] when citing that fact
- You can combine citations: [^1, 2, 3] for multiple sources supporting one claim
- DO NOT create a References section - it will be appended automatically

SPECIFIC GUIDANCE:
1. Start with an Executive Summary that captures the core technical insights
2. Include code examples verbatim from evidence - preserve formatting
3. Use proper section hierarchy: Overview before deep-dive details
4. If the topic involves implementation: Provide step-by-step procedures
5. If the topic involves architecture: Explain components and their interactions
6. Every technical claim must cite the provided evidence using the citation numbers
7. Do NOT create your own References section

Focus on technical depth and actionable information. A developer should be able to understand and implement based on this report alone.
"""

    try:
        print(" Attempting GPT-5 for high-quality synthesis... (This may take a moment)")
        report = gpt_manager.generate_content(
            system_instruction=writer_system_instruction,
            user_prompt=prompt,
            json_mode=False,
            temperature=0.7
        )
        print(" Used GPT-5 for synthesis")
        # Append deduplicated references section
        return report + references_text
        
    except Exception as gpt_error:
        # Fallback to Gemini if GPT-5 fails
        print(f"  GPT-5 unavailable ({str(gpt_error)[:60]}...)")
        print(" Falling back to Gemini 2.5 Flash for synthesis...\n")
        
        try:
            response = gemini_manager.generate_content(
                model_name="gemini-2.5-flash",
                system_instruction=writer_system_instruction,
                user_prompt=prompt,
                generation_config={"temperature": 0.7}
            )
            print(" Used Gemini Flash as fallback")
            # Append deduplicated references section
            return response.text + references_text
            
        except Exception as gemini_error:
            print(f" Both GPT-5 and Gemini failed for synthesis!")
            print(f"   GPT-5 error: {str(gpt_error)[:100]}")
            print(f"   Gemini error: {str(gemini_error)[:100]}")
            return f"Error generating report: Both models failed. Please try again later."



# --- TEST ZONE ---
if __name__ == "__main__":
    
    # Scenario: User asked about the future of Electric Vehicles
    topic = "What is the future outlook for Electric Vehicle (EV) adoption in India by 2030?"
    
    # Simulated "Verified Facts" collected by your agent
    mock_facts = [
        {
            "fact": "The Indian government aims for 30% EV penetration by 2030.", 
            "source": "https://niti.gov.in/ev-policy"
        },
        {
            "fact": "Tata Motors currently holds 70% of the EV market share in India.", 
            "source": "https://economictimes.indiatimes.com/tata-motors-ev-share"
        },
        {
            "fact": "Lack of charging infrastructure remains the primary bottleneck for adoption.", 
            "source": "https://www.mckinsey.com/industries/automotive-and-assembly/our-insights"
        },
        {
            "fact": "Battery costs are expected to fall by 40% over the next 5 years.", 
            "source": "https://bloombergnef.com/battery-prices"
        }
    ]
    
    report = generate_research_report(topic, mock_facts)
    
    print("\n" + "="*50)
    print(report)
    print("="*50)

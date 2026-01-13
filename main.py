"""
Research System - Main Orchestrator

This module coordinates all research components to perform comprehensive research
and generate detailed reports based on user prompts.
"""

import json
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from modules.Planner import planner
from modules.search import SearchEngine
from modules.scraper import scrape_with_timeout
from modules.extractor import extract_key_info
from modules.step_analyzer import analyze_step_fulfillment
from modules.sanity_checker import check_global_sufficiency
from modules.synthesizer import generate_research_report, generate_research_report_streaming
from modules.quality_evaluator import evaluate_research_quality, identify_knowledge_gaps
from utils.checkpoint_manager import CheckpointManager
from utils.metrics_tracker import MetricsTracker
from utils.source_cache import SourceCache
from utils.api_manager import set_global_metrics_tracker
from utils.gpt_manager import set_global_metrics_tracker as set_gpt_metrics_tracker
from config.config import AUTO_RESUME


class ResearchSystem:
    """Orchestrates the complete research pipeline."""
    
    def __init__(self, resume=False, enable_cache=True, enable_streaming=True, use_langgraph_planner=False, interactive=True):
        self.search_engine = SearchEngine()
        self.all_collected_facts = []
        self.max_queries_per_step = 5
        self.max_iterations_per_step = 3  # NEW: Recursive loop limit
        self.quality_threshold = 0.7  # NEW: Quality threshold for step completion
        self.checkpoint = CheckpointManager()
        self.scraped_urls = set()  # Track scraped URLs to avoid duplicates
        self.metrics = MetricsTracker()  # Track performance metrics
        self.facts_lock = threading.Lock()  # Thread-safe fact collection
        self.urls_lock = threading.Lock()  # Thread-safe URL tracking
        self.source_cache = SourceCache() if enable_cache else None  # Source caching
        self.enable_streaming = enable_streaming  # Streaming synthesis
        self.use_langgraph_planner = use_langgraph_planner  # Optional LangGraph for planning
        self.interactive = interactive  # Interactive mode for plan refinement
        
        # Set global metrics tracker for both API managers
        set_global_metrics_tracker(self.metrics)
        set_gpt_metrics_tracker(self.metrics)
        
        # Resume from checkpoint if requested
        if resume:
            self._load_checkpoint()
        
    def execute_research(self, user_prompt: str) -> str:
        """
        Execute the complete research pipeline with checkpoint support.
        
        Args:
            user_prompt (str): The research question or topic
            
        Returns:
            str: The final research report in Markdown format
        """
        print("\n" + "="*70)
        print(" RESEARCH SYSTEM INITIALIZED")
        print("="*70)
        
        # Step 1: Generate Research Plan
        print("\n Step 1: Creating Research Plan...")
        research_plan = self._create_plan(user_prompt)
        
        if not research_plan:
            return "Error: Failed to generate research plan."
        
        # Set total steps for metrics
        self.metrics.set_total_steps(len(research_plan.get('steps', [])))
        
        # Save checkpoint after planning
        self._save_checkpoint(user_prompt, research_plan, current_step=0)
        
        # Step 2: Execute Research Steps (with parallelization)
        print("\n Step 2: Executing Research Steps...")
        
        # Analyze dependencies and create execution batches
        execution_batches = self._create_execution_batches(research_plan['steps'])
        
        print(f"\n Execution Strategy: {len(execution_batches)} batch(es)")
        for batch_idx, batch in enumerate(execution_batches, 1):
            step_nums = [s['step_number'] for s in batch]
            if len(batch) > 1:
                print(f"   Batch {batch_idx}: Steps {step_nums} (parallel)")
            else:
                print(f"   Batch {batch_idx}: Step {step_nums[0]} (sequential)")
        
        # Execute batches sequentially, steps within batches in parallel
        for batch_idx, batch in enumerate(execution_batches, 1):
            if len(batch) == 1:
                # Single step - execute normally
                step = batch[0]
                self.metrics.start_step(step['step_number'])
                self._execute_step(step, user_prompt, research_plan)
                self.metrics.end_step(step['step_number'])
                self.metrics.increment_steps_completed()
            else:
                # Multiple independent steps - execute in parallel
                print(f"\n Executing Batch {batch_idx} ({len(batch)} steps in parallel)...")
                self._execute_parallel_batch(batch, user_prompt, research_plan)
        
        # Step 3: Sanity Check - Verify Completeness
        print("\n Step 3: Verifying Collected Data...")
        self._perform_sanity_check(user_prompt)
        
        # Save checkpoint before final synthesis
        self._save_checkpoint(user_prompt, research_plan, 
                            current_step=len(research_plan['steps']))
        
        # Step 4: Generate Final Report
        print("\n Step 4: Generating Final Report...")
        
        if self.enable_streaming:
            # Streaming synthesis with real-time output
            report = generate_research_report_streaming(user_prompt, self.all_collected_facts)
        else:
            # Traditional synthesis
            report = generate_research_report(user_prompt, self.all_collected_facts)
        
        # Clear checkpoint after successful completion
        self.checkpoint.clear()
        
        # Display cache and metrics
        if self.source_cache:
            self.source_cache.print_stats()
        
        print(self.metrics.get_summary())
        self.metrics.save_to_file()
        
        print("\n" + "="*70)
        print(" RESEARCH COMPLETE")
        print("="*70)
        
        return report
    
    def _create_execution_batches(self, steps: list) -> list:
        """
        Analyze step dependencies and group independent steps into parallel batches.
        
        Steps are considered dependent if:
        - A later step explicitly references an earlier step
        - Step actions contain keywords like "based on", "using results from", "compare findings"
        - Step reasoning mentions previous steps
        
        Args:
            steps (list): List of research steps
            
        Returns:
            list: List of batches, where each batch contains independent steps that can run in parallel
        """
        dependency_keywords = [
            'based on', 'using', 'compare', 'synthesize', 'combine',
            'previous', 'earlier', 'above', 'from step', 'after'
        ]
        
        batches = []
        remaining_steps = steps.copy()
        
        while remaining_steps:
            current_batch = []
            next_remaining = []
            
            for step in remaining_steps:
                step_text = f"{step.get('action', '')} {step.get('reasoning', '')}".lower()
                
                # Check if this step depends on any uncompleted step
                has_dependency = False
                
                # Simple heuristic: if step mentions synthesis/comparison or is the last step,
                # it likely depends on previous steps
                if any(keyword in step_text for keyword in dependency_keywords):
                    has_dependency = True
                
                # Last step is often synthesis - keep it sequential
                if step['step_number'] == len(steps):
                    has_dependency = True
                
                if has_dependency and current_batch:
                    # This step depends on previous work, save for next batch
                    next_remaining.append(step)
                else:
                    # Independent step, add to current batch
                    current_batch.append(step)
            
            if current_batch:
                batches.append(current_batch)
                remaining_steps = next_remaining
            else:
                # No progress made, avoid infinite loop - add remaining as single steps
                for step in remaining_steps:
                    batches.append([step])
                break
        
        return batches
    
    def _execute_parallel_batch(self, batch: list, user_prompt: str, research_plan: dict):
        """
        Execute a batch of independent steps in parallel.
        
        Args:
            batch (list): List of independent steps to execute in parallel
            user_prompt (str): Original user prompt
            research_plan (dict): Full research plan
        """
        with ThreadPoolExecutor(max_workers=len(batch)) as executor:
            # Submit all steps in batch
            future_to_step = {}
            for step in batch:
                self.metrics.start_step(step['step_number'])
                future = executor.submit(self._execute_step, step, user_prompt, research_plan)
                future_to_step[future] = step
            
            # Wait for completion
            for future in as_completed(future_to_step):
                step = future_to_step[future]
                try:
                    future.result()  # This will raise any exception from the step
                    self.metrics.end_step(step['step_number'])
                    self.metrics.increment_steps_completed()
                    print(f"\n    Step {step['step_number']} completed")
                except Exception as e:
                    print(f"\n    Step {step['step_number']} failed: {e}")
                    # Continue with other steps even if one fails
    
    def _create_plan(self, user_prompt: str) -> dict:
        """Generate a structured research plan using the Planner module."""
        
        if self.use_langgraph_planner:
            # Use LangGraph-based planner with state management
            try:
                from modules.planner_langgraph import interactive_planner
                print(" Using LangGraph-enhanced planner with state management\n")
                return interactive_planner(user_prompt)
            except ImportError:
                print("  LangGraph not installed. Install with: pip install langgraph langchain-core")
                print(" Falling back to original planner...\n")
                self.use_langgraph_planner = False
        
        # Use original planner (default)
        from modules.Planner import refine_plan
        
        # Generate initial plan
        research_plan = planner(user_prompt)
        
        if not research_plan:
            return None
        
        # Interactive refinement loop (only if interactive mode is enabled)
        if self.interactive:
            while True:
                print("\n" + "="*70)
                print("\n Would you like to modify this plan?")
                print("   - Type your feedback to refine the plan")
                print("   - Type 'start' or press Enter to begin research")
                print("   - Type 'quit' to exit")
                print("\n" + "="*70)
                
                user_input = input("\n Your response: ").strip()
                
                if not user_input or user_input.lower() == 'start':
                    print("\n Starting research with current plan...\n")
                    break
                elif user_input.lower() == 'quit':
                    print("\n Research cancelled by user.")
                    return None
                else:
                    # Refine the plan based on user feedback
                    research_plan = refine_plan(research_plan, user_input)
        else:
            print("\n Auto-starting research (non-interactive mode)...\n")
        
        return research_plan
    
    def _execute_step(self, step: dict, user_prompt: str, research_plan: dict):
        """
        Execute a single research step with recursive quality refinement.
        
        Args:
            step (dict): The step containing action, queries, and reasoning
            user_prompt (str): The original user prompt for context
            research_plan (dict): The full research plan for checkpointing
        """
        step_number = step['step_number']
        action = step['action']
        initial_queries = step['search_queries']
        
        print(f"\n Executing Step {step_number}: {action}")
        
        # Track step-level data
        step_facts_start = len(self.all_collected_facts)
        all_queries_tried = []
        step_sources = []
        
        # Recursive research loop
        iteration = 0
        quality_met = False
        
        while iteration < self.max_iterations_per_step and not quality_met:
            iteration += 1
            print(f"\n   Iteration {iteration}/{self.max_iterations_per_step}")
            
            # Determine queries for this iteration
            if iteration == 1:
                current_queries = initial_queries
            else:
                # Generate refined queries based on gaps
                step_facts = self.all_collected_facts[step_facts_start:]
                
                if not last_evaluation.get('missing_aspects'):
                    print(f"    No missing aspects identified, using fallback queries")
                    break
                
                refined_queries = identify_knowledge_gaps(
                    step_objective=action,
                    extracted_facts=step_facts,
                    missing_aspects=last_evaluation['missing_aspects'],
                    previous_queries=all_queries_tried
                )
                
                if not refined_queries:
                    print(f"    Could not generate refined queries")
                    break
                
                current_queries = refined_queries
                self.metrics.record_query_refinement()
            
            # Execute queries for this iteration - PARALLEL EXECUTION
            iteration_facts_start = len(self.all_collected_facts)
            
            # Process all queries in parallel
            with ThreadPoolExecutor(max_workers=min(len(current_queries[:self.max_queries_per_step]), 3)) as executor:
                query_futures = []
                
                for query_idx, query in enumerate(current_queries[:self.max_queries_per_step], 1):
                    all_queries_tried.append(query)
                    future = executor.submit(self._execute_query, query, query_idx, action, step_sources)
                    query_futures.append(future)
                
                # Wait for all queries to complete
                for future in as_completed(query_futures):
                    try:
                        future.result()
                    except Exception as e:
                        print(f"    Query execution error: {e}")
            
            # Evaluate quality after this iteration
            step_facts = self.all_collected_facts[step_facts_start:]
            
            if not step_facts:
                print(f"    No facts collected in iteration {iteration}")
                last_evaluation = {
                    'overall_score': 0.0,
                    'threshold_met': False,
                    'missing_aspects': ['No data collected']
                }
                self.metrics.record_iteration(step_number, 0.0)
                continue
            
            last_evaluation = evaluate_research_quality(
                step_objective=action,
                extracted_facts=step_facts,
                sources=step_sources,
                iteration=iteration
            )
            
            # Record iteration metrics
            quality_score = last_evaluation.get('overall_score', 0.0)
            self.metrics.record_iteration(step_number, quality_score)
            
            # Check if quality threshold is met
            if last_evaluation.get('threshold_met', False):
                print(f"   Quality threshold met! (Score: {quality_score:.2f})")
                quality_met = True
                break
            
            # Check for diminishing returns
            if iteration > 1:
                previous_score = self.metrics.metrics['quality_scores'][step_number][-2]
                improvement = quality_score - previous_score
                
                if improvement < 0.05:
                    print(f"    Diminishing returns (improvement: +{improvement:.3f})")
                    print(f"  → Stopping iterations for this step")
                    break
        
        # Final status
        if not quality_met:
            final_score = last_evaluation.get('overall_score', 0.0) if 'last_evaluation' in locals() else 0.0
            print(f"\n    Step {step_number} completed with quality score: {final_score:.2f}/{self.quality_threshold}")
            print(f"  → Used {iteration} iteration(s), collected {len(self.all_collected_facts[step_facts_start:])} facts")
        
        # Save checkpoint after each step
        self._save_checkpoint(user_prompt, research_plan, current_step=step_number)
    
    def _execute_query(self, query: str, query_idx: int, action: str, step_sources: list):
        """
        Execute a single search query with scraping and extraction.
        This method is designed to run in parallel with other queries.
        
        Args:
            query (str): Search query to execute
            query_idx (int): Query index for display
            action (str): Step action/objective
            step_sources (list): List to append sources to
        """
        print(f"\n   Query {query_idx}: '{query}'")
        
        # Search for URLs
        search_results = self.search_engine.search(query, num_results=5)
        
        if not search_results:
            print("   No results found.")
            return
        
        # Process URLs in parallel (limit to top 3)
        with ThreadPoolExecutor(max_workers=3) as executor:
            url_futures = []
            
            for idx, result in enumerate(search_results[:3], 1):
                url = result.get('link') or result.get('url')
                title = result.get('title', 'Unknown')
                
                # Skip already scraped URLs (thread-safe check)
                with self.urls_lock:
                    if url in self.scraped_urls:
                        print(f"    [{idx}] Skipping (already scraped): {title[:50]}...")
                        self.metrics.record_scraping(skipped=True)
                        continue
                    # Mark URL as being scraped
                    self.scraped_urls.add(url)
                
                # Submit URL processing
                future = executor.submit(
                    self._process_url, 
                    url, title, idx, action, step_sources
                )
                url_futures.append(future)
            
            # Wait for all URLs to be processed
            for future in as_completed(url_futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"      URL processing error: {e}")
    
    def _process_url(self, url: str, title: str, idx: int, action: str, step_sources: list):
        """
        Process a single URL: check cache, scrape if needed, extract facts.
        
        Args:
            url (str): URL to process
            title (str): Page title
            idx (int): Index for display
            action (str): Step action/objective
            step_sources (list): List to append sources to
        """
        is_pdf = url.lower().endswith('.pdf') or '.pdf?' in url.lower()
        
        # Check cache first
        scraped_content = None
        if self.source_cache and self.source_cache.should_cache(url):
            scraped_content = self.source_cache.get(url)
            if scraped_content:
                print(f"    [{idx}]  Cache hit: {title[:50]}...")
        
        # Scrape if not cached
        if not scraped_content:
            print(f"    [{idx}] {' PDF' if is_pdf else 'Scraping'}: {title[:50]}...")
            
            # Adjust timeout for PDFs (they take longer)
            timeout = 20 if is_pdf else 7
            scraped_content = scrape_with_timeout(url, timeout=timeout)
            
            # Cache the content if it's from a high-quality source
            if scraped_content and self.source_cache and self.source_cache.should_cache(url):
                self.source_cache.put(url, scraped_content)
        
        if scraped_content:
            step_sources.append(url)
            self.metrics.record_scraping(success=True, is_pdf=is_pdf)
            
            # Extract relevant facts
            facts = extract_key_info(action, scraped_content, url)
            
            if facts:
                # Record each fact with its source (thread-safe)
                for fact in facts:
                    self.metrics.record_fact(fact.get('source', url))
                
                # Thread-safe fact collection
                with self.facts_lock:
                    self.all_collected_facts.extend(facts)
                print(f"         Extracted {len(facts)} fact(s)")
        else:
            self.metrics.record_scraping(success=False, is_pdf=is_pdf)
    
    def _perform_sanity_check(self, user_prompt: str):
        """
        Verify that collected facts are sufficient to answer the user's question.
        If gaps exist, execute a rescue query.
        """
        print("\nRunning final data sufficiency check...")
        
        result = check_global_sufficiency(user_prompt, self.all_collected_facts)
        
        if result.get('pass'):
            print(" Data is sufficient for report generation.")
        else:
            print(f" Gap detected: {result.get('reason')}")
            rescue_query = result.get('rescue_query')
            
            if rescue_query:
                print(f" Executing rescue query: '{rescue_query}'")
                self.metrics.record_rescue_query()
                
                # Execute rescue query
                search_results = self.search_engine.search(rescue_query, num_results=3)
                
                for result in search_results[:2]:
                    url = result.get('link') or result.get('url')
                    scraped_content = scrape_with_timeout(url, timeout=7)
                    
                    if scraped_content:
                        self.metrics.record_scraping(success=True)
                        facts = extract_key_info(user_prompt, scraped_content, url)
                        if facts:
                            for fact in facts:
                                self.metrics.record_fact(fact.get('source', url))
                            self.all_collected_facts.extend(facts)
                            print(f"   Collected {len(facts)} additional fact(s)")
                    else:
                        self.metrics.record_scraping(success=False)
                
                print(" Rescue query completed.")
    
    def _save_checkpoint(self, user_prompt: str, research_plan: dict, current_step: int):
        """Save current research state to checkpoint."""
        state = {
            "user_prompt": user_prompt,
            "research_plan": research_plan,
            "current_step": current_step,
            "completed_steps": list(range(1, current_step + 1)),
            "all_collected_facts": self.all_collected_facts,
            "scraped_urls": list(self.scraped_urls)
        }
        self.checkpoint.save(state)
        self.metrics.record_checkpoint()
    
    def _load_checkpoint(self):
        """Load research state from checkpoint."""
        checkpoint_data = self.checkpoint.load()
        
        if checkpoint_data:
            self.all_collected_facts = checkpoint_data.get('all_collected_facts', [])
            self.scraped_urls = set(checkpoint_data.get('scraped_urls', []))
            print(f" Resumed: {len(self.all_collected_facts)} facts, "
                  f"{len(self.scraped_urls)} URLs")


def main():
    """Main entry point for the research system."""
    
    # Check for existing checkpoint
    checkpoint_manager = CheckpointManager()
    resume_mode = False
    
    if checkpoint_manager.exists() and AUTO_RESUME:
        print("\n" + "="*70)
        print(" CHECKPOINT FOUND")
        print("="*70)
        print(checkpoint_manager.get_summary())
        print("="*70)
        
        resume_choice = input("\nResume from checkpoint? (y/n): ").strip().lower()
        if resume_choice == 'y':
            resume_mode = True
        else:
            checkpoint_manager.clear()
    
    # Get user prompt
    if len(sys.argv) > 1:
        # Prompt provided as command-line argument
        user_prompt = ' '.join(sys.argv[1:])
    else:
        # Interactive mode
        print("\n" + "="*70)
        print(" RESEARCH SYSTEM")
        print("="*70)
        
        if resume_mode:
            # Load prompt from checkpoint
            checkpoint_data = checkpoint_manager.load()
            user_prompt = checkpoint_data.get('user_prompt', '')
            print(f"\nResuming: {user_prompt}")
        else:
            user_prompt = input("\nEnter your research question: ").strip()
    
    if not user_prompt:
        print("Error: No prompt provided.")
        return
    
    # Initialize and run research system
    research_system = ResearchSystem(resume=resume_mode)
    report = research_system.execute_research(user_prompt)
    
    # Display the report
    print("\n\n" + "="*70)
    print(" FINAL RESEARCH REPORT")
    print("="*70 + "\n")
    print(report)
    
    # Optionally save to file
    save_option = input("\n\nSave report to file? (y/n): ").strip().lower()
    if save_option == 'y':
        filename = input("Enter filename (default: report.md): ").strip() or "report.md"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f" Report saved to {filename}")


if __name__ == "__main__":
    main()

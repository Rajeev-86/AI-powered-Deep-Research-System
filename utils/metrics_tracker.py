"""
Metrics Tracker - Comprehensive performance and quality monitoring
"""
import time
import json
from datetime import datetime
from collections import defaultdict
from config.config import CHECKPOINT_DIR
import os


class MetricsTracker:
    """Tracks research quality, efficiency, and agentic behavior metrics."""
    
    def __init__(self):
        self.start_time = time.time()
        self.metrics = {
            # Quality metrics
            "sources": set(),
            "facts_extracted": 0,
            "steps_completed": 0,
            "total_steps": 0,
            
            # Efficiency metrics
            "api_calls": defaultdict(int),  # model_name: count
            "tokens_used": defaultdict(int),  # model_name: tokens
            "urls_scraped": {"success": 0, "failed": 0, "skipped": 0},
            "pdfs_parsed": {"success": 0, "failed": 0},  # NEW: Track PDF parsing
            
            # Agentic behavior metrics
            "query_refinements": 0,
            "rescue_queries": 0,
            "api_key_rotations": 0,
            "checkpoint_saves": 0,
            
            # Recursive loop metrics (NEW)
            "step_iterations": defaultdict(int),  # step_number: iteration_count
            "quality_scores": defaultdict(list),  # step_number: [scores per iteration]
            "quality_improvements": [],  # Track score deltas between iterations
            
            # Timing
            "step_times": [],
            "scraping_time": 0,
            "extraction_time": 0,
            "synthesis_time": 0
        }
        self.current_step_start = None
        self.sources_per_fact = defaultdict(int)  # Track citations per source
    
    # ===== Recording Methods =====
    
    def start_step(self, step_number: int):
        """Mark the start of a research step."""
        self.current_step_start = time.time()
        
    def end_step(self, step_number: int):
        """Mark the end of a research step."""
        if self.current_step_start:
            duration = time.time() - self.current_step_start
            self.metrics["step_times"].append(duration)
            self.current_step_start = None
    
    def record_api_call(self, model_name: str, tokens: int = 0):
        """Record an API call to a specific model."""
        self.metrics["api_calls"][model_name] += 1
        if tokens > 0:
            self.metrics["tokens_used"][model_name] += tokens
    
    def record_fact(self, source_url: str):
        """Record a fact extraction with its source."""
        self.metrics["facts_extracted"] += 1
        self.metrics["sources"].add(source_url)
        self.sources_per_fact[source_url] += 1
    
    def record_scraping(self, success: bool = True, skipped: bool = False, is_pdf: bool = False):
        """Record a scraping attempt."""
        if skipped:
            self.metrics["urls_scraped"]["skipped"] += 1
        elif success:
            self.metrics["urls_scraped"]["success"] += 1
            if is_pdf:
                self.metrics["pdfs_parsed"]["success"] += 1
        else:
            self.metrics["urls_scraped"]["failed"] += 1
            if is_pdf:
                self.metrics["pdfs_parsed"]["failed"] += 1
    
    def record_query_refinement(self):
        """Record when the agent refines a search query."""
        self.metrics["query_refinements"] += 1
    
    def record_rescue_query(self):
        """Record when sanity checker triggers a rescue query."""
        self.metrics["rescue_queries"] += 1
    
    def record_api_key_rotation(self):
        """Record when API key rotation occurs."""
        self.metrics["api_key_rotations"] += 1
    
    def record_checkpoint(self):
        """Record a checkpoint save."""
        self.metrics["checkpoint_saves"] += 1
    
    def set_total_steps(self, total: int):
        """Set the total number of research steps."""
        self.metrics["total_steps"] = total
    
    def increment_steps_completed(self):
        """Increment completed steps counter."""
        self.metrics["steps_completed"] += 1
    
    def record_iteration(self, step_number: int, quality_score: float):
        """Record a research iteration with its quality score."""
        self.metrics["step_iterations"][step_number] += 1
        self.metrics["quality_scores"][step_number].append(quality_score)
        
        # Calculate improvement from previous iteration
        scores = self.metrics["quality_scores"][step_number]
        if len(scores) > 1:
            improvement = scores[-1] - scores[-2]
            self.metrics["quality_improvements"].append(improvement)
    
    def get_avg_iterations_per_step(self) -> float:
        """Get average number of iterations per step."""
        if not self.metrics["step_iterations"]:
            return 0.0
        return sum(self.metrics["step_iterations"].values()) / len(self.metrics["step_iterations"])
    
    def get_avg_quality_improvement(self) -> float:
        """Get average quality improvement across all iterations."""
        if not self.metrics["quality_improvements"]:
            return 0.0
        return sum(self.metrics["quality_improvements"]) / len(self.metrics["quality_improvements"])
    
    # ===== Analysis Methods =====
    
    def get_citation_diversity(self) -> float:
        """Calculate average citations per source (lower = better diversity)."""
        if not self.metrics["sources"]:
            return 0.0
        return self.metrics["facts_extracted"] / len(self.metrics["sources"])
    
    def get_domain_diversity(self) -> dict:
        """Analyze domain diversity of sources."""
        domains = defaultdict(int)
        for url in self.metrics["sources"]:
            if ".edu" in url:
                domains["academic"] += 1
            elif ".org" in url:
                domains["organization"] += 1
            elif ".gov" in url:
                domains["government"] += 1
            elif "arxiv.org" in url:
                domains["research_papers"] += 1
            else:
                domains["commercial"] += 1
        return dict(domains)
    
    def get_total_time(self) -> float:
        """Get total elapsed time in seconds."""
        return time.time() - self.start_time
    
    def get_success_rate(self) -> float:
        """Calculate URL scraping success rate."""
        total = sum(self.metrics["urls_scraped"].values())
        if total == 0:
            return 0.0
        return (self.metrics["urls_scraped"]["success"] / total) * 100
    
    def get_step_completion_rate(self) -> float:
        """Calculate percentage of steps completed."""
        if self.metrics["total_steps"] == 0:
            return 0.0
        return (self.metrics["steps_completed"] / self.metrics["total_steps"]) * 100
    
    def estimate_cost(self) -> float:
        """Estimate API cost in USD (based on Gemini pricing)."""
        # Gemini Flash: $0.075 per 1M input tokens, $0.30 per 1M output tokens
        # Gemini Pro: $1.25 per 1M input tokens, $5.00 per 1M output tokens
        # Simplified: assume 70% input, 30% output, average cost
        
        flash_tokens = self.metrics["tokens_used"].get("gemini-2.5-flash", 0)
        pro_tokens = self.metrics["tokens_used"].get("gemini-2.5-pro", 0)
        
        flash_cost = (flash_tokens / 1_000_000) * 0.15  # Average of input/output
        pro_cost = (pro_tokens / 1_000_000) * 2.50  # Average of input/output
        
        return flash_cost + pro_cost
    
    # ===== Reporting Methods =====
    
    def get_summary(self) -> str:
        """Generate a human-readable metrics summary."""
        total_time = self.get_total_time()
        minutes = int(total_time // 60)
        seconds = int(total_time % 60)
        
        summary = []
        summary.append("\n" + "="*70)
        summary.append(" RESEARCH METRICS")
        summary.append("="*70)
        
        # Quality Metrics
        summary.append("\n Quality Metrics:")
        summary.append(f"  ├─ Unique sources: {len(self.metrics['sources'])}")
        summary.append(f"  ├─ Facts extracted: {self.metrics['facts_extracted']}")
        summary.append(f"  ├─ Citation diversity: {self.get_citation_diversity():.1f} facts/source")
        
        domains = self.get_domain_diversity()
        if domains:
            summary.append(f"  └─ Domain diversity: {', '.join([f'{k}: {v}' for k, v in domains.items()])}")
        
        # Efficiency Metrics
        summary.append("\n Efficiency Metrics:")
        summary.append(f"  ├─ Total time: {minutes}m {seconds}s")
        
        total_api_calls = sum(self.metrics["api_calls"].values())
        summary.append(f"  ├─ API calls: {total_api_calls}")
        for model, count in self.metrics["api_calls"].items():
            summary.append(f"  │  └─ {model}: {count}")
        
        cost = self.estimate_cost()
        if cost > 0:
            summary.append(f"  ├─ Estimated cost: ${cost:.4f}")
        
        total_urls = sum(self.metrics["urls_scraped"].values())
        success_rate = self.get_success_rate()
        summary.append(f"  ├─ URLs scraped: {total_urls} (success: {success_rate:.1f}%)")
        
        # PDF parsing stats
        pdf_total = sum(self.metrics["pdfs_parsed"].values())
        if pdf_total > 0:
            pdf_success = self.metrics["pdfs_parsed"]["success"]
            summary.append(f"  │  └─ PDFs parsed: {pdf_success}/{pdf_total} ({pdf_success*100/pdf_total:.1f}%)")
        
        summary.append(f"  └─ Steps: {len(self.metrics['step_times'])}")
        
        # Agentic Behavior Metrics
        summary.append("\n Agentic Intelligence:")
        completion_rate = self.get_step_completion_rate()
        summary.append(f"  ├─ Steps completed: {self.metrics['steps_completed']}/{self.metrics['total_steps']} ({completion_rate:.1f}%)")
        summary.append(f"  ├─ Query refinements: {self.metrics['query_refinements']}")
        summary.append(f"  ├─ Rescue queries: {self.metrics['rescue_queries']}")
        summary.append(f"  ├─ API key rotations: {self.metrics['api_key_rotations']}")
        summary.append(f"  └─ Checkpoints saved: {self.metrics['checkpoint_saves']}")
        
        # Recursive Loop Metrics (NEW)
        if self.metrics["step_iterations"]:
            avg_iterations = self.get_avg_iterations_per_step()
            avg_improvement = self.get_avg_quality_improvement()
            summary.append("\n Recursive Research:")
            summary.append(f"  ├─ Avg iterations/step: {avg_iterations:.1f}")
            if self.metrics["quality_improvements"]:
                summary.append(f"  ├─ Avg quality improvement: +{avg_improvement:.3f}")
            summary.append(f"  └─ Total iterations: {sum(self.metrics['step_iterations'].values())}")
        
        summary.append("="*70 + "\n")
        
        return "\n".join(summary)
    
    def save_to_file(self, filename: str = None):
        """Save metrics to JSON file for analysis."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"metrics_{timestamp}.json"
        
        metrics_dir = os.path.join(CHECKPOINT_DIR, "metrics")
        os.makedirs(metrics_dir, exist_ok=True)
        filepath = os.path.join(metrics_dir, filename)
        
        # Convert sets to lists for JSON serialization
        export_data = {
            "timestamp": datetime.now().isoformat(),
            "total_time_seconds": self.get_total_time(),
            "quality": {
                "unique_sources": len(self.metrics["sources"]),
                "sources_list": list(self.metrics["sources"]),
                "facts_extracted": self.metrics["facts_extracted"],
                "citation_diversity": self.get_citation_diversity(),
                "domain_diversity": self.get_domain_diversity(),
                "sources_per_fact": dict(self.sources_per_fact)
            },
            "efficiency": {
                "api_calls": dict(self.metrics["api_calls"]),
                "tokens_used": dict(self.metrics["tokens_used"]),
                "estimated_cost_usd": self.estimate_cost(),
                "urls_scraped": self.metrics["urls_scraped"],
                "pdfs_parsed": self.metrics["pdfs_parsed"],
                "success_rate": self.get_success_rate(),
                "step_times_seconds": self.metrics["step_times"]
            },
            "agentic_behavior": {
                "steps_completed": self.metrics["steps_completed"],
                "total_steps": self.metrics["total_steps"],
                "completion_rate": self.get_step_completion_rate(),
                "query_refinements": self.metrics["query_refinements"],
                "rescue_queries": self.metrics["rescue_queries"],
                "api_key_rotations": self.metrics["api_key_rotations"],
                "checkpoint_saves": self.metrics["checkpoint_saves"],
                "step_iterations": dict(self.metrics["step_iterations"]),
                "quality_scores": {k: v for k, v in self.metrics["quality_scores"].items()},
                "quality_improvements": self.metrics["quality_improvements"],
                "avg_iterations_per_step": self.get_avg_iterations_per_step(),
                "avg_quality_improvement": self.get_avg_quality_improvement()
            }
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        print(f" Metrics saved to: {filepath}")
        return filepath

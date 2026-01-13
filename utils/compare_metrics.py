"""
Metrics Comparison Tool - Compare research runs to track improvements
"""
import json
import os
import glob
from config.config import CHECKPOINT_DIR


def load_metrics(filepath):
    """Load metrics from a JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def compare_metrics(file1, file2):
    """Compare two metrics files and show improvements."""
    m1 = load_metrics(file1)
    m2 = load_metrics(file2)
    
    print("\n" + "="*70)
    print(" METRICS COMPARISON")
    print("="*70)
    print(f"\nRun 1: {os.path.basename(file1)}")
    print(f"Run 2: {os.path.basename(file2)}")
    print("="*70)
    
    # Quality comparison
    print("\n Quality Metrics:")
    compare_metric("Unique sources", 
                  m1['quality']['unique_sources'], 
                  m2['quality']['unique_sources'])
    compare_metric("Facts extracted", 
                  m1['quality']['facts_extracted'], 
                  m2['quality']['facts_extracted'])
    compare_metric("Citation diversity", 
                  m1['quality']['citation_diversity'], 
                  m2['quality']['citation_diversity'], 
                  lower_is_better=True)
    
    # Efficiency comparison
    print("\n Efficiency Metrics:")
    compare_metric("Total time (s)", 
                  m1['total_time_seconds'], 
                  m2['total_time_seconds'], 
                  lower_is_better=True)
    compare_metric("API calls", 
                  sum(m1['efficiency']['api_calls'].values()), 
                  sum(m2['efficiency']['api_calls'].values()), 
                  lower_is_better=True)
    compare_metric("Estimated cost ($)", 
                  m1['efficiency']['estimated_cost_usd'], 
                  m2['efficiency']['estimated_cost_usd'], 
                  lower_is_better=True)
    compare_metric("Success rate (%)", 
                  m1['efficiency']['success_rate'], 
                  m2['efficiency']['success_rate'])
    
    # Agentic behavior comparison
    print("\n Agentic Intelligence:")
    compare_metric("Completion rate (%)", 
                  m1['agentic_behavior']['completion_rate'], 
                  m2['agentic_behavior']['completion_rate'])
    compare_metric("Query refinements", 
                  m1['agentic_behavior']['query_refinements'], 
                  m2['agentic_behavior']['query_refinements'])
    compare_metric("API key rotations", 
                  m1['agentic_behavior']['api_key_rotations'], 
                  m2['agentic_behavior']['api_key_rotations'], 
                  lower_is_better=True)
    
    print("="*70 + "\n")


def compare_metric(name, val1, val2, lower_is_better=False):
    """Compare a single metric and show improvement."""
    diff = val2 - val1
    pct_change = (diff / val1 * 100) if val1 != 0 else 0
    
    if lower_is_better:
        improved = diff < 0
        symbol = "↓" if improved else "↑"
    else:
        improved = diff > 0
        symbol = "↑" if improved else "↓"
    
    emoji = "" if improved else ""
    
    print(f"  {emoji} {name}:")
    print(f"     Run 1: {val1:.2f}")
    print(f"     Run 2: {val2:.2f}")
    print(f"     Change: {symbol} {abs(pct_change):.1f}%")


def list_metrics_files():
    """List all available metrics files."""
    metrics_dir = os.path.join(CHECKPOINT_DIR, "metrics")
    if not os.path.exists(metrics_dir):
        return []
    
    files = glob.glob(os.path.join(metrics_dir, "metrics_*.json"))
    return sorted(files, reverse=True)  # Most recent first


def main():
    """Interactive comparison tool."""
    print("\n" + "="*70)
    print(" METRICS COMPARISON TOOL")
    print("="*70)
    
    files = list_metrics_files()
    
    if len(files) < 2:
        print("\nNeed at least 2 metrics files to compare.")
        print(f"Found {len(files)} file(s).")
        return
    
    print(f"\nFound {len(files)} metrics files:\n")
    for i, f in enumerate(files[:10], 1):  # Show last 10
        print(f"  [{i}] {os.path.basename(f)}")
    
    try:
        choice1 = int(input("\nSelect first file (number): ")) - 1
        choice2 = int(input("Select second file (number): ")) - 1
        
        if 0 <= choice1 < len(files) and 0 <= choice2 < len(files):
            compare_metrics(files[choice1], files[choice2])
        else:
            print("Invalid selection.")
    except (ValueError, KeyboardInterrupt):
        print("\nCancelled.")


if __name__ == "__main__":
    main()

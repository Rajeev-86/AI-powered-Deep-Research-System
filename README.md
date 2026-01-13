# AI Research System

An intelligent, autonomous research system that conducts comprehensive multi-step research using AI agents, producing professional reports with full citations.

## Table of Contents
- [Overview](#overview)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Reference](#api-reference)
- [System Components](#system-components)
- [Performance & Optimization](#performance--optimization)
- [Advanced Features](#advanced-features)
- [Frontend](#frontend)
- [Troubleshooting](#troubleshooting)

---

## Overview

The AI Research System is a production-ready research automation platform that:
- **Plans** multi-step research strategies using advanced AI models
- **Executes** comprehensive web searches and data extraction in parallel
- **Verifies** collected information for quality and completeness
- **Synthesizes** professional reports with proper citations
- **Adapts** dynamically based on data quality and research needs

**Perfect for:** Academic research, market analysis, technical documentation, competitive intelligence, and any task requiring comprehensive information gathering.

---

## Key Features

### Multi-Model AI Architecture
- **GPT-5 / GPT-4o** (via GitHub Models) - Strategic planning and synthesis
- **Gemini 2.5 Flash** (Multiple API keys) - Efficient extraction and analysis  
- **Gemini 2.5 Flash lite** - For faster fact extractions
- Automatic model selection based on task requirements
- Zero-cost planning via GitHub Models free tier

### Intelligent Research Pipeline
1. **Planning** - Generates structured multi-step research plan
2. **Execution** - Adaptive query refinement with parallel processing
3. **Sanity Checking** - Validates data quality, triggers rescue queries if needed
4. **Synthesis** - Creates markdown reports with footnote citations

### Performance Optimizations
- **Parallel Execution** - Concurrent query processing (2-3x faster)
- **Source Caching** - 24-hour TTL cache (20-40% fewer API calls)
- **Streaming Output** - Real-time report generation
- **Combined impact: 30-50% faster** than traditional sequential execution

### Enterprise-Grade Reliability
- **API Key Rotation** - Automatic failover across multiple Gemini keys
- **Checkpoint System** - Auto-save after each step, resume from failures
- **Multi-Provider Search** - Google Custom Search + Tavily fallback
- **Quality Control** - Sanity checker validates data completeness

### Adaptive Intelligence
- **Recursive Quality Loops** - Iteratively improves research quality
- **Dynamic Query Refinement** - Adapts search strategy based on results
- **Rescue Queries** - Automatically fills gaps in data coverage
- **Citation Deduplication** - Intelligent source management

### Agentic Behavior Metrics
Tracks sophisticated research behaviors:
- Query refinements and iterations
- API key rotations
- Rescue query triggers
- Quality score improvements
- Checkpoint saves

---

## Architecture

### High-Level Flow
```
User Query
    ↓
┌─────────────────────────────────────────┐
│  1. PLANNING (Planner.py)               │
│     - GPT-5 generates research strategy │
│     - Multi-step breakdown              │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│  2. EXECUTION (step_analyzer.py)        │
│     - Parallel query execution          │
│     - Web scraping with cache           │
│     - Fact extraction (Gemini Flash)    │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│  3. VERIFICATION (sanity_checker.py)    │
│     - Data quality assessment           │
│     - Gap detection & rescue queries    │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│  4. SYNTHESIS (synthesizer.py)          │
│     - GPT-5 generates report            │
│     - Streaming output                  │
│     - Citation management               │
└─────────────────────────────────────────┘
    ↓
Markdown Report with Citations
```

### Core Components

| Component | File | Purpose |
|-----------|------|---------|
| **Main Orchestrator** | `main.py` | Coordinates entire research pipeline |
| **Planner** | `modules/Planner.py` | Generates multi-step research plans |
| **Step Analyzer** | `modules/step_analyzer.py` | Executes research steps in parallel |
| **Scraper** | `modules/scraper.py` | Web content extraction with PDF support |
| **Extractor** | `modules/extractor.py` | AI-powered fact extraction |
| **Sanity Checker** | `modules/sanity_checker.py` | Quality control and gap detection |
| **Synthesizer** | `modules/synthesizer.py` | Report generation with citations |
| **Search** | `modules/search.py` | Multi-provider search orchestration |

### Utility Modules

| Utility | File | Purpose |
|---------|------|---------|
| **API Manager** | `utils/api_manager.py` | Gemini API key rotation |
| **GPT Manager** | `utils/gpt_manager.py` | GitHub Models GPT interface |
| **Metrics Tracker** | `utils/metrics_tracker.py` | Comprehensive performance metrics |
| **Source Cache** | `utils/source_cache.py` | 24hr TTL cache for scraped content |

---

## Installation

### Prerequisites
- Python 3.10+
- Node.js 20+ (for frontend only)
- API Keys (see Configuration)

### Backend Setup
```bash
# Clone repository
git clone <your-repo>
cd Research_System

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements-api.txt
```

### Frontend Setup (Optional)
```bash
# Install Node.js 20+
./setup_node.sh

# Install frontend dependencies
cd frontend
npm install
```

---

## Configuration

### 1. API Keys Setup

Edit `config/config.yaml`:

```yaml
api_keys:
  # GitHub Models (Free tier - for GPT-5/4o)
  GITHUB_TOKEN: "ghp_your_github_token_here"
  
  # Google AI Studio (25 free API keys recommended)
  android_studio:
    keys: 
      - "AIzaSyXXXXXXXXXXXXXXXXXXXXXX"  # Key 1
      - "AIzaSyYYYYYYYYYYYYYYYYYYYYYY"  # Key 2
      # ... add multiple keys for best reliability
  
  # Google Custom Search (recommended 2 free tier keys for rotation)
  google_search:
    keys: 
      - "YOUR_GOOGLE_API_KEY_1"
      - "YOUR_GOOGLE_API_KEY_2"
    Engine_id: 
      - "YOUR_CX_ID_1"
      - "YOUR_CX_ID_2"
  
  # Tavily Search (fallback)
  tavily:
    api_key: "tvly-XXXXXXXXXXXXXXXX"
```

### 2. System Settings

Edit `config/config.py`:

```python
# API Configuration
MAX_RETRIES = 3
CHECKPOINT_DIR = "checkpoints"
AUTO_RESUME = True

# Performance
ENABLE_CACHE = True
CACHE_TTL_HOURS = 24
ENABLE_PARALLEL = True
MAX_WORKERS = 5

# Quality Control
QUALITY_THRESHOLD = 0.4
MAX_ITERATIONS_PER_STEP = 3
```

### 3. Optional: LangGraph Integration

Install LangGraph for advanced state management:
```bash
pip install langgraph langchain-core
```

---

## Usage

### Command Line (Terminal)

**Basic Usage:**
```bash
python main.py "What are the latest developments in quantum computing?"
```

**With Custom Settings:**
```bash
# Disable caching
python main.py "AI research" --no-cache

# Disable streaming
python main.py "Climate change impacts" --no-streaming

# Use LangGraph planner
python main.py "Blockchain trends" --use-langgraph
```

**Interactive Mode:**
```bash
python main.py
# Then enter your query when prompted
```

### API Server

**Start the server:**
```bash
python api_server.py
# Server runs at http://localhost:8000
```

**API Documentation:**
Visit http://localhost:8000/docs for interactive Swagger documentation.

### Full Stack (Backend + Frontend)

**Quick Start:**
```bash
./start.sh
# Backend: http://localhost:8000
# Frontend: http://localhost:3000
```

---

## API Reference

### Core Endpoints

#### 1. Chat / Plan Generation
```http
POST /api/chat
Content-Type: application/json

{
  "message": "your research query",
  "deep_research": true,
  "thread_id": "optional-session-id"
}
```

**Response when `deep_research=true`:**
```json
{
  "response": "## Research Plan\n\n**Objective:** ...",
  "intent": "plan_review",
  "timestamp": "2026-01-13T10:00:00",
  "plan": {
    "main_objective": "Research latest AI developments",
    "steps": [
      {
        "step_number": 1,
        "action": "Search for recent AI breakthroughs",
        "reasoning": "Establish current state of the art",
        "search_queries": ["AI breakthrough 2025", "latest AI research"]
      }
    ]
  }
}
```

#### 2. Execute Research
```http
POST /api/research/execute
Content-Type: application/json

{
  "query": "your research query",
  "plan": { /* plan object from step 1 */ },
  "enable_cache": true
}
```

**Response:**
```json
{
  "report": "# Research Report\n\n## Executive Summary...",
  "query": "your research query",
  "timestamp": "2026-01-13T10:15:00",
  "metrics": {
    "total_api_calls": 45,
    "total_tokens": 125000,
    "total_cost": 0.0234
  }
}
```

#### 3. Refine Plan
```http
POST /api/research/refine
Content-Type: application/json

{
  "query": "original query",
  "plan": { /* current plan */ },
  "feedback": "Add more focus on recent patents"
}
```

#### 4. Health Check
```http
GET /
```

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "services": {
    "chatbot": "active",
    "research_system": "active",
    "websocket": "active"
  }
}
```

### WebSocket Support

**Chat Streaming:**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/chat/session-id');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data.content);
};

ws.send(JSON.stringify({
  message: "your query",
  deep_research: false
}));
```

---

## System Components

### 1. Planner (`modules/Planner.py`)

**Purpose:** Generates structured, multi-step research plans

**AI Models Used:**
- Primary: GPT-5 / GPT-4o
- Fallback: Gemini 2.5 Flash
**Output Format:**
```python
{
  "main_objective": "Research AI advancements in 2025",
  "steps": [
    {
      "step_number": 1,
      "action": "Identify breakthrough AI models",
      "reasoning": "Establish baseline of current capabilities",
      "search_queries": [
        "AI models released 2025",
        "breakthrough AI architectures 2025"
      ]
    }
  ]
}
```

### 2. Step Analyzer (`modules/step_analyzer.py`)

**Purpose:** Executes research steps with parallel query processing

**Key Features:**
- Parallel search query execution
- Dynamic query refinement based on results
- URL deduplication across steps
- Integrated with source cache

**Execution Flow:**
```
Search Queries → Parallel Search → Scraping → Fact Extraction → Quality Check
```

### 3. Scraper (`modules/scraper.py`)

**Purpose:** Extracts content from web pages and PDFs

**Supported Formats:**
- HTML (via trafilatura)
- PDF (via pdfplumber)
- Automatic format detection

**Features:**
- Robust error handling
- Content cleaning
- Metadata extraction

### 4. Extractor (`modules/extractor.py`)

**Purpose:** AI-powered fact extraction from scraped content

**AI Model:** Gemini 2.5 Flash lite

**Extraction Strategy:**
- Structured prompting for fact identification
- Citation tracking
- Relevance filtering

**Output Format:**
```python
[
  {
    "fact": "GPT-5 was released in January 2025",
    "source": "https://openai.com/blog/gpt-5-release"
  }
]
```

### 5. Sanity Checker (`modules/sanity_checker.py`)

**Purpose:** Validates research quality and triggers rescue queries

**Quality Metrics:**
- Source diversity
- Fact count
- Citation coverage

**Rescue Query Logic:**
```python
if quality_score < QUALITY_THRESHOLD:
    rescue_queries = generate_rescue_queries(gaps)
    execute_rescue_queries(rescue_queries)
```

### 6. Synthesizer (`modules/synthesizer.py`)

**Purpose:** Generates professional markdown reports

**AI Model:** GPT-5 / GPT-4o

**Report Structure:**
- Executive Summary
- Detailed Analysis
- Technical Deep Dives
- Conclusion
- References (auto-generated)

**Citation Format:**
```markdown
AI models have improved significantly[^1, 2, 3].

## References
[^1]: https://arxiv.org/paper1
[^2]: https://openai.com/research
[^3]: https://deepmind.google/papers
```

### 7. Search (`modules/search.py`)

**Purpose:** Multi-provider search orchestration

**Providers:**
1. **Google Custom Search** (Primary)
   - multiple API keys with rotation
   - 100 queries/day per key for free tier
2. **Tavily Search** (Fallback)
   - Activates when Google quota exhausted

**Search Strategy:**
- Query optimization
- Result deduplication
- Automatic provider switching

---

## Performance & Optimization

### Parallel Execution

**Implementation:**
```python
with ThreadPoolExecutor(max_workers=5) as executor:
    futures = [executor.submit(search, query) for query in queries]
    results = [f.result() for f in as_completed(futures)]
```

**Benefits:**
- 2-3x faster query execution
- Better resource utilization
- Maintains result quality

### Source Caching

**Cache Strategy:**
- 24-hour TTL (configurable)
- URL-based keys
- Content + metadata storage

**Cache Hit Example:**
```
[1] Cache hit: https://arxiv.org/paper1 (saved 2.3s)
[2] Scraping: https://newsite.com/article
[3] Cache hit: https://github.com/repo (saved 1.8s)
```

**Performance Impact:**
- 20-40% fewer web requests
- Faster repeated research
- Reduced API costs

### Streaming Synthesis

**Real-time Output:**
```python
for chunk in synthesis_stream():
    print(chunk, end='', flush=True)
```

**User Experience:**
- Instant feedback
- Perceived performance improvement
- Progress visibility

### Metrics Tracking

**Comprehensive Metrics:**
```json
{
  "quality": {
    "unique_sources": 42,
    "facts_extracted": 156,
    "citation_diversity": 3.7
  },
  "efficiency": {
    "total_time_seconds": 287,
    "api_calls": 45,
    "cache_hit_rate": 34.2,
    "estimated_cost_usd": 0.0234
  },
  "agentic_behavior": {
    "query_refinements": 12,
    "rescue_queries": 2,
    "api_key_rotations": 3,
    "avg_iterations_per_step": 2.4
  }
}
```

---

## Advanced Features

### Checkpoint System

**Auto-Save:**
```python
# Automatically saves after each step
checkpoint_file = f"checkpoints/research_{timestamp}.json"
```

**Resume:**
```bash
# Detects existing checkpoint on startup
Found checkpoint: checkpoints/research_20260113_100530.json
Resume from Step 3? (y/n):
```

**Benefits:**
- No lost work on failures
- Pause/resume research
- Avoids re-scraping URLs

### Recursive Quality Loops

**Quality Improvement:**
```python
for iteration in range(MAX_ITERATIONS):
    quality_score = evaluate_quality(data)
    if quality_score >= THRESHOLD:
        break
    data = refine_research(data, quality_score)
```

**Tracking:**
- Quality scores per iteration
- Improvement deltas
- Iteration counts

### API Key Rotation

**Automatic Failover:**
```python
# Gemini API Manager
keys = load_gemini_keys()
current_key = 0

def get_next_key():
    global current_key
    current_key = (current_key + 1) % len(keys)
    return keys[current_key]
```

**Benefits:**
- Zero downtime on rate limits
- Transparent to research process
- Logs rotation events

### LangGraph Integration (Optional)

**State Management:**
```python
from langgraph.graph import StateGraph

# Define research state
class ResearchState(TypedDict):
    query: str
    plan: dict
    data: list
    report: str

# Build graph
graph = StateGraph(ResearchState)
graph.add_node("plan", planning_node)
graph.add_node("execute", execution_node)
```

**When to Use:**
- Complex multi-turn conversations
- State-dependent planning
- Advanced workflow orchestration

---

## Frontend

The system includes an optional Next.js 16 frontend for web-based access.

**Features:**
- Chat interface with markdown rendering
- Deep research mode toggle
- Plan review workflow (Start/Modify/Cancel)
- Real-time progress updates
- Citation viewing with collapsible references

**Quick Start:**
```bash
./start.sh
# Frontend: http://localhost:3000
```

**Tech Stack:**
- Next.js 16 with App Router
- TypeScript
- Tailwind CSS v3
- React Markdown
- Radix UI components

For detailed frontend documentation, see `/frontend/README.md`.

---

## Troubleshooting

### Common Issues

**1. API Rate Limits**
```
Error: 429 Too Many Requests
```
**Solution:** Add more Gemini API keys in `config/config.yaml`

**2. GitHub Models Rate Limit**
```
Error: GitHub Models rate limit exceeded
```
**Solution:** System auto-switches to Gemini for planning

**3. Search Quota Exhausted**
```
Warning: Google Search quota exhausted
```
**Solution:** System auto-switches to Tavily. Add more Google API keys.

**4. Cache Issues**
```
Error: Cannot write to cache
```
**Solution:** Check write permissions on `cache/` directory

**5. Checkpoint Resume Fails**
```
Error: Invalid checkpoint format
```
**Solution:** Delete corrupted checkpoint file in `checkpoints/`

### Debug Mode

**Enable verbose logging:**
```python
# In config/config.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Check backend logs:**
```bash
tail -f backend.log
```

### Performance Issues

**Slow research execution:**
1. Enable parallel execution (default)
2. Enable caching (default)
3. Add more Gemini API keys
4. Check internet connection speed

**High API costs:**
1. Enable caching to reduce duplicate requests
2. Use GitHub Models (free tier) for planning
3. Optimize search queries

---

## Project Structure

```
Research_System/
├── main.py                 # Main orchestrator
├── api_server.py           # FastAPI server
├── chatbot_integration.py  # LangGraph chatbot
├── start.sh               # Full-stack launcher
├── setup_node.sh          # Node.js installer
│
├── config/
│   ├── config.yaml        # API keys & settings
│   └── config.py          # System configuration
│
├── modules/
│   ├── Planner.py         # Research planning
│   ├── step_analyzer.py   # Step execution
│   ├── scraper.py         # Web scraping
│   ├── extractor.py       # Fact extraction
│   ├── sanity_checker.py  # Quality control
│   ├── synthesizer.py     # Report generation
│   └── search.py          # Search orchestration
│
├── utils/
│   ├── api_manager.py     # Gemini key rotation
│   ├── gpt_manager.py     # GitHub Models interface
│   ├── metrics_tracker.py # Performance tracking
│   └── source_cache.py    # Content caching
│
├── frontend/              # Next.js UI (optional)
│   ├── app/
│   ├── components/
│   └── lib/
│
├── checkpoints/           # Auto-saved progress
├── reports/              # Generated reports
└── cache/                # Scraped content cache
```

---

## Credits & License

Built with cutting-edge AI technologies:
- OpenAI GPT-5 / GPT-4o (via GitHub models)
- Google Gemini 2.5 Flash / 2.0 Flash Exp (via Google AI studio)
- LangGraph (optional)
- FastAPI
- Next.js

---

## Support

For issues, questions, or contributions, please open an issue on GitHub.

**Happy Researching!**

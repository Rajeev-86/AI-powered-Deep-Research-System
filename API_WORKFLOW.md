# Deep Research API Workflow

## Overview
The deep research feature follows a 3-step workflow matching the terminal experience:

1. **Generate Plan** → User reviews
2. **User Decision** → Start, Modify, or Cancel
3. **Execute Research** → Return final report

---

## Step 1: Request Research Plan

**Endpoint:** `POST /api/chat`

**Request:**
```json
{
  "message": "your research topic",
  "deep_research": true,
  "thread_id": "optional-thread-id"
}
```

**Response:**
```json
{
  "response": "## Research Plan\n\n**Objective:**...\n\n### Steps:...",
  "intent": "plan_review",
  "timestamp": "2025-12-14T10:00:00",
  "plan": {
    "main_objective": "...",
    "steps": [
      {
        "step_number": 1,
        "action": "...",
        "reasoning": "...",
        "search_queries": ["query1", "query2"]
      }
    ]
  }
}
```

**Frontend Action:**
- Display `response` (formatted markdown plan)
- Store `plan` object for Step 3
- Show buttons: **Start**, **Modify**, **Cancel**

---

## Step 2A: User Clicks "Start"

Proceed to Step 3 (Execute Research)

---

## Step 2B: User Clicks "Modify"

**Endpoint:** `POST /api/research/refine`

**Request:**
```json
{
  "plan": { /* the plan object from Step 1 */ },
  "feedback": "user's modification request"
}
```

**Response:**
```json
{
  "plan": { /* refined plan */ },
  "timestamp": "..."
}
```

**Frontend Action:**
- Update displayed plan
- Continue showing Start/Modify/Cancel buttons

---

## Step 2C: User Clicks "Cancel"

Simply close/hide the research interface. No API call needed.

---

## Step 3: Execute Approved Research

**Endpoint:** `POST /api/research/execute`

**Request:**
```json
{
  "query": "original research topic",
  "plan": { /* the approved plan object */ },
  "enable_cache": true
}
```

**Response:**
```json
{
  "report": "# Full Research Report\n\n## Section 1...",
  "query": "...",
  "timestamp": "...",
  "metrics": {
    "total_api_calls": 156,
    "total_tokens": 89432,
    "total_cost": 0.245
  }
}
```

**Frontend Action:**
- Display `report` as markdown
- Show metrics (optional)
- Research complete!

---

## Alternative: Direct Research (No Plan Review)

For automated/background research without user interaction:

**Endpoint:** `POST /api/research/plan` then `POST /api/research/execute`

Or use the legacy endpoint:

**Endpoint:** `POST /api/research`

**Request:**
```json
{
  "query": "research topic",
  "enable_cache": true,
  "enable_streaming": false
}
```

This executes research immediately without showing the plan.

---

## Frontend Implementation Example

```typescript
// Step 1: Get research plan
async function requestResearchPlan(topic: string) {
  const response = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message: topic,
      deep_research: true
    })
  });
  
  const data = await response.json();
  
  if (data.intent === 'plan_review') {
    // Show plan and buttons
    displayPlan(data.response); // Markdown formatted plan
    showButtons(['Start', 'Modify', 'Cancel']);
    storePlan(data.plan); // Save for Step 3
  }
}

// Step 3: Execute research
async function executeResearch(query: string, plan: any) {
  showLoading("Executing research... This may take several minutes");
  
  const response = await fetch('/api/research/execute', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      query: query,
      plan: plan,
      enable_cache: true
    })
  });
  
  const data = await response.json();
  displayReport(data.report); // Show final markdown report
  showMetrics(data.metrics); // Optional
}
```

---

## Notes

- Research execution can take 3-10 minutes depending on complexity
- The frontend should show a loading indicator during execution
- Plan uses **GPT-5/4o** for smart planning
- Research uses **Gemini 2.0 Flash /Flash lite** for extraction (rate-limit friendly)
- All responses include proper CORS headers for localhost:3000

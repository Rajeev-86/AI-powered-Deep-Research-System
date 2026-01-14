"""
FastAPI Server for Research System
Provides REST API endpoints for the Next.js frontend
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import json
from datetime import datetime
import sys
import logging

# Configure logging to show in terminal
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('backend.log')
    ]
)
logger = logging.getLogger(__name__)

# Try to import ChatBot with LangGraph, fallback to direct implementation
try:
    import langgraph
    import langchain_core
    from chatbot_integration import ChatBot
    LANGGRAPH_AVAILABLE = True
except Exception as e:
    LANGGRAPH_AVAILABLE = False
    ChatBot = None
    print(f"  LangGraph not available ({type(e).__name__}: {str(e)[:50]}), using direct implementation")

from main import ResearchSystem
from utils.gpt_manager import GPTManager

# Initialize GPT manager for chat responses
gpt_manager = GPTManager()

app = FastAPI(title="Research System API", version="1.0.0")

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for production deployment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the chatbot (with or without LangGraph)
if LANGGRAPH_AVAILABLE:
    chatbot = ChatBot(enable_research=True)
else:
    chatbot = None  # Will use direct implementation

# Models
class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = "default"
    deep_research: bool = False

class ChatResponse(BaseModel):
    response: str
    intent: str
    timestamp: str
    plan: Optional[Dict[str, Any]] = None  # Include plan when generating research plan

class ResearchRequest(BaseModel):
    query: str
    enable_cache: bool = True
    enable_streaming: bool = True

class PlanRequest(BaseModel):
    query: str

class PlanResponse(BaseModel):
    plan: Dict[str, Any]
    query: str
    timestamp: str

class ExecutePlanRequest(BaseModel):
    query: str
    plan: Dict[str, Any]
    enable_cache: bool = True

class HealthResponse(BaseModel):
    status: str
    version: str
    services: dict


@app.get("/", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "services": {
            "chatbot": "active" if LANGGRAPH_AVAILABLE else "direct",
            "research_system": "active",
            "websocket": "active"
        }
    }


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Handle chat requests with optional deep research
    
    If deep_research=true, returns the research plan for user approval
    User must then call /api/research/execute to run the actual research
    """
    try:
        logger.info(f" Chat request: message='{request.message}', deep_research={request.deep_research}")
        
        if request.deep_research:
            logger.info(" Generating research plan...")
            # Generate and return plan for user review
            from modules.Planner import planner
            
            research_plan = planner(request.message)
            
            if not research_plan:
                logger.error(" Failed to generate research plan")
                raise HTTPException(status_code=500, detail="Failed to generate research plan")
            
            logger.info(f" Plan generated with {len(research_plan['steps'])} steps")
            
            # Format plan as markdown for display
            plan_text = f"##  Research Plan\n\n**Objective:** {research_plan['main_objective']}\n\n"
            plan_text += "### Steps:\n\n"
            
            for step in research_plan['steps']:
                # Keep step number and action on same line
                plan_text += f"{step['step_number']}. {step['action']}\n"
            
            plan_text += "\n---\n\n"
            plan_text += " Click **Start Research** to begin\n"
            plan_text += " Click **Modify Plan** to refine the approach\n"
            plan_text += " Click **Cancel** to abort\n"
            
            logger.info(" Sending plan to frontend for review")
            
            return {
                "response": plan_text,
                "intent": "plan_review",
                "timestamp": datetime.now().isoformat(),
                "plan": research_plan  # Include plan data for frontend
            }
        
        elif LANGGRAPH_AVAILABLE and chatbot:
            logger.info(" Processing normal chat with LangGraph ChatBot")
            # Use LangGraph ChatBot for normal chat
            response = chatbot.chat(request.message, thread_id=request.thread_id)
            intent = "chat"
            logger.info(" Chat response generated")
        else:
            # Direct implementation without LangGraph
            if request.deep_research:
                # Execute deep research
                research_system = ResearchSystem(
                    enable_cache=True,
                    enable_streaming=False,
                    use_langgraph_planner=False
                )
                response = research_system.research(request.message)
                intent = "research"
            else:
                # Normal chat using GPT
                system_instruction = "You are a helpful AI assistant with access to a deep research capability. If the user needs comprehensive research with multiple sources and detailed analysis, mention they can enable 'Deep Research' mode."
                response = gpt_manager.generate_content(
                    system_instruction=system_instruction,
                    user_prompt=request.message,
                    json_mode=False,
                    temperature=0.7
                )
                intent = "chat"
        
        return {
            "response": response,
            "intent": intent,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/research")
async def research(request: ResearchRequest):
    """
    Direct research endpoint for comprehensive research
    Returns the complete research report
    """
    try:
        research_system = ResearchSystem(
            enable_cache=request.enable_cache,
            enable_streaming=False,  # No streaming for API
            use_langgraph_planner=False
        )
        
        report = research_system.research(request.query)
        
        return {
            "report": report,
            "query": request.query,
            "timestamp": datetime.now().isoformat(),
            "metrics": {
                "total_api_calls": research_system.metrics.total_api_calls,
                "total_tokens": research_system.metrics.total_tokens,
                "total_cost": research_system.metrics.total_cost
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/research/plan", response_model=PlanResponse)
async def create_research_plan(request: PlanRequest):
    """
    Step 1: Generate research plan for user review
    Returns the plan WITHOUT executing research
    """
    try:
        logger.info(f" Creating research plan for: '{request.query}'")
        from modules.Planner import planner
        
        # Generate plan
        research_plan = planner(request.query)
        
        if not research_plan:
            logger.error(" Failed to generate research plan")
            raise HTTPException(status_code=500, detail="Failed to generate research plan")
        
        logger.info(f" Plan created with {len(research_plan['steps'])} steps")
        
        return {
            "plan": research_plan,
            "query": request.query,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f" Error creating plan: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/research/execute")
async def execute_research_plan(request: ExecutePlanRequest):
    """
    Step 2: Execute approved research plan
    This runs the actual research and returns the report
    """
    try:
        logger.info("="*70)
        logger.info(f" STARTING RESEARCH EXECUTION")
        logger.info(f" Query: {request.query}")
        logger.info(f" Plan has {len(request.plan.get('steps', []))} steps")
        logger.info("="*70)
        
        # Create research system with non-interactive mode
        research_system = ResearchSystem(
            enable_cache=request.enable_cache,
            enable_streaming=False,
            use_langgraph_planner=False,
            interactive=False
        )
        
        logger.info(" Research system initialized")
        logger.info("  Cache enabled: %s", request.enable_cache)
        logger.info(" Interactive mode: False (API mode)")
        
        # Execute research
        logger.info("\n  Executing research...\n")
        report = research_system.execute_research(request.query)
        
        logger.info("\n" + "="*70)
        logger.info(" RESEARCH COMPLETED SUCCESSFULLY")
        logger.info(f" Report length: {len(report)} characters")
        
        # Calculate metrics from MetricsTracker
        total_api_calls = sum(research_system.metrics.metrics["api_calls"].values())
        total_tokens = sum(research_system.metrics.metrics["tokens_used"].values())
        total_cost = research_system.metrics.estimate_cost()
        
        logger.info(f" API calls: {total_api_calls}")
        logger.info(f" Tokens used: {total_tokens}")
        logger.info(f" Estimated cost: ${total_cost:.4f}")
        logger.info("="*70 + "\n")
        
        return {
            "report": report,
            "query": request.query,
            "timestamp": datetime.now().isoformat(),
            "metrics": {
                "total_api_calls": total_api_calls,
                "total_tokens": total_tokens,
                "total_cost": total_cost
            }
        }
    
    except Exception as e:
        logger.error(f"\n RESEARCH EXECUTION FAILED")
        logger.error(f"Error: {str(e)}")
        logger.error("="*70 + "\n")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/research/refine")
async def refine_research_plan(request: dict):
    """
    Optional: Refine research plan based on user feedback
    """
    try:
        logger.info(" Refining plan based on user feedback...")
        from modules.Planner import refine_plan
        
        original_plan = request.get("plan")
        feedback = request.get("feedback")
        query = request.get("query")
        
        if not original_plan or not feedback:
            raise HTTPException(status_code=400, detail="Missing plan or feedback")
        
        refined_plan = refine_plan(original_plan, feedback)
        
        logger.info(f" Plan refined with {len(refined_plan.get('steps', []))} steps")
        
        # Format plan as markdown for display
        plan_text = f"##  Revised Research Plan\n\n**Objective:** {refined_plan['main_objective']}\n\n"
        plan_text += "### Steps:\n\n"
        
        for step in refined_plan['steps']:
            plan_text += f"{step['step_number']}. {step['action']}\n"
        
        plan_text += "\n---\n\n"
        plan_text += " Click **Start Research** to begin\n"
        plan_text += " Click **Modify Plan** to refine further\n"
        plan_text += " Click **Cancel** to abort\n"
        
        return {
            "response": plan_text,
            "plan": refined_plan,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f" Error refining plan: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws/chat/{thread_id}")
async def websocket_chat(websocket: WebSocket, thread_id: str):
    """
    WebSocket endpoint for real-time streaming chat
    Provides token-by-token streaming for better UX
    """
    await websocket.accept()
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            user_message = message_data.get("message", "")
            deep_research = message_data.get("deep_research", False)
            
            # Send acknowledgment
            await websocket.send_json({
                "type": "ack",
                "message": "Processing your request..."
            })
            
            # For deep research, send progress updates
            if deep_research or "deep research" in user_message.lower():
                await websocket.send_json({
                    "type": "status",
                    "message": " Initiating deep research..."
                })
            
            # Get response
            if LANGGRAPH_AVAILABLE and chatbot:
                # Use LangGraph ChatBot
                if deep_research and not user_message.lower().startswith("deep research"):
                    user_message = f"deep research {user_message}"
                response = chatbot.chat(user_message, thread_id=thread_id)
            else:
                # Direct implementation
                if deep_research:
                    research_system = ResearchSystem(
                        enable_cache=True,
                        enable_streaming=False,
                        use_langgraph_planner=False
                    )
                else:
                    response = gpt_manager.generate_content(
                        system_instruction="You are a helpful AI assistant.",
                        user_prompt=user_message,
                        json_mode=False,
                        temperature=0.7
                    )
            
            # Send complete response
            await websocket.send_json({
                "type": "message",
                "content": response,
                "timestamp": datetime.now().isoformat()
            })
            
            # Send completion signal
            await websocket.send_json({
                "type": "done"
            })
    
    except WebSocketDisconnect:
        print(f"Client {thread_id} disconnected")
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })
        await websocket.close()


@app.websocket("/ws/research")
async def websocket_research(websocket: WebSocket):
    """
    WebSocket endpoint for streaming research progress
    Provides real-time updates during research execution
    """
    await websocket.accept()
    
    try:
        # Receive research query
        data = await websocket.receive_text()
        query_data = json.loads(data)
        query = query_data.get("query", "")
        
        # Initialize research system with streaming
        research_system = ResearchSystem(
            enable_cache=True,
            enable_streaming=True,
            use_langgraph_planner=False
        )
        
        # Send status updates
        await websocket.send_json({
            "type": "status",
            "step": "planning",
            "message": "Creating research plan..."
        })
        
        # Execute research
        report = research_system.research(query)
        
        # Send final report
        await websocket.send_json({
            "type": "report",
            "content": report,
            "metrics": {
                "total_api_calls": research_system.metrics.total_api_calls,
                "total_tokens": research_system.metrics.total_tokens,
                "total_cost": research_system.metrics.total_cost
            }
        })
        
        await websocket.send_json({"type": "done"})
    
    except WebSocketDisconnect:
        print("Research client disconnected")
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })
        await websocket.close()


@app.get("/api/metrics")
async def get_metrics():
    """Get current system metrics"""
    return {
        "status": "active",
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    
    print("\n" + "="*70)
    print(" Research System API Server")
    print("="*70)
    print(f"\nMode: {'LangGraph' if LANGGRAPH_AVAILABLE else 'Direct'}")
    print("\nEndpoints:")
    print("  • REST API: http://localhost:8000")
    print("  • WebSocket: ws://localhost:8000/ws/chat/{thread_id}")
    print("  • Docs: http://localhost:8000/docs")
    print("  • Health: http://localhost:8000/")
    if not LANGGRAPH_AVAILABLE:
        print("\n Tip: Install LangGraph for enhanced features:")
        print("   pip install langgraph langchain-core")
    print("="*70 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

"""
ChatBot Integration with LangGraph

This module demonstrates how to integrate the Research System into a chatbot
interface using LangGraph for state management and routing.

Architecture:
- LangGraph StateGraph for conversation flow
- Intent classification to detect deep research requests
- Seamless routing between normal chat and deep research
- Maintains conversation history and context
"""

from typing import TypedDict, Annotated, Literal
import operator
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from main import ResearchSystem
import os


class ChatState(TypedDict):
    """State schema for the chatbot conversation."""
    messages: Annotated[list, operator.add]  # Conversation history
    user_input: str  # Current user message
    intent: str  # Classified intent: "chat" or "research"
    research_query: str  # Extracted research query if intent is research
    response: str  # Bot's response
    research_mode: bool  # Whether deep research is enabled


class ChatBot:
    """LangGraph-based chatbot with integrated deep research capability."""
    
    def __init__(self, enable_research=True):
        """
        Initialize the chatbot.
        
        Args:
            enable_research: Whether to enable deep research mode
        """
        self.enable_research = enable_research
        self.research_system = None
        self.memory = MemorySaver()
        self.graph = self._create_graph()
        
    def _create_graph(self) -> StateGraph:
        """Create the LangGraph state machine for the chatbot."""
        workflow = StateGraph(ChatState)
        
        # Add nodes
        workflow.add_node("classify_intent", self._classify_intent)
        workflow.add_node("normal_chat", self._normal_chat)
        workflow.add_node("deep_research", self._deep_research)
        workflow.add_node("format_response", self._format_response)
        
        # Define edges
        workflow.set_entry_point("classify_intent")
        
        # Conditional routing based on intent
        workflow.add_conditional_edges(
            "classify_intent",
            self._route_by_intent,
            {
                "chat": "normal_chat",
                "research": "deep_research"
            }
        )
        
        workflow.add_edge("normal_chat", "format_response")
        workflow.add_edge("deep_research", "format_response")
        workflow.add_edge("format_response", END)
        
        return workflow.compile(checkpointer=self.memory)
    
    def _classify_intent(self, state: ChatState) -> ChatState:
        """
        Classify user intent: normal chat or deep research request.
        
        Uses Gemini-2.5-flash for fast intent classification.
        """
        from utils.api_manager import gemini_manager
        
        user_input = state["user_input"]
        
        # If research mode is disabled, always route to chat
        if not self.enable_research or not state.get("research_mode", True):
            state["intent"] = "chat"
            state["research_query"] = ""
            return state
        
        # Check for explicit research triggers
        research_keywords = [
            "deep research", "comprehensive research", "detailed analysis",
            "research about", "investigate", "comprehensive report",
            "detailed report", "in-depth study"
        ]
        
        if any(keyword in user_input.lower() for keyword in research_keywords):
            state["intent"] = "research"
            # Extract the actual query (remove the trigger phrase)
            query = user_input.lower()
            for keyword in research_keywords:
                query = query.replace(keyword, "").strip()
            state["research_query"] = query if query else user_input
            return state
        
        # Use Gemini Flash for more nuanced intent classification
        classification_prompt = f"""You are an intent classifier for a chatbot.
Determine if the user wants:
1. "chat" - Normal conversation, quick answer, or simple question
2. "research" - Comprehensive research with multiple sources and detailed report

User message: "{user_input}"

Respond with ONLY one word: "chat" or "research"

Examples:
- "What is quantum computing?" -> chat
- "Give me a comprehensive analysis of quantum computing developments" -> research
- "How are you?" -> chat
- "Research the latest AI regulations and provide a detailed report" -> research
"""
        
        try:
            response = gemini_manager.generate_content(
                model_name="gemini-2.5-flash",
                system_instruction="You are an intent classifier. Respond with ONLY 'chat' or 'research'.",
                user_prompt=classification_prompt,
                generation_config={"temperature": 0.3, "max_output_tokens": 10}
            )
            intent = response.text.strip().lower()
            
            if intent not in ["chat", "research"]:
                intent = "chat"  # Default to chat if unclear
            
            state["intent"] = intent
            state["research_query"] = user_input if intent == "research" else ""
            
        except Exception as e:
            print(f"Intent classification error: {e}")
            state["intent"] = "chat"  # Safe fallback
            state["research_query"] = ""
        
        return state
    
    def _route_by_intent(self, state: ChatState) -> Literal["chat", "research"]:
        """Route to appropriate handler based on classified intent."""
        return state["intent"]
    
    def _normal_chat(self, state: ChatState) -> ChatState:
        """Handle normal chat conversation using Gemini-2.5-flash for speed."""
        from utils.api_manager import gemini_manager
        
        user_input = state["user_input"]
        messages = state.get("messages", [])
        
        # Build conversation context
        context = "\n".join([
            f"{'User' if i % 2 == 0 else 'Assistant'}: {msg}" 
            for i, msg in enumerate(messages[-6:])  # Last 3 exchanges
        ])
        
        chat_prompt = f"""Conversation history:
{context}

User: {user_input}

Provide a helpful, concise response."""
        
        try:
            response = gemini_manager.generate_content(
                model_name="gemini-2.5-flash",
                system_instruction="You are a helpful AI assistant with access to a deep research capability. If the user asks for comprehensive research, suggest they use the 'deep research' command.",
                user_prompt=chat_prompt,
                generation_config={"temperature": 0.7, "max_output_tokens": 1024}
            )
            state["response"] = response.text
        except Exception as e:
            state["response"] = f"I apologize, but I encountered an error: {str(e)}"
        
        return state
    
    def _deep_research(self, state: ChatState) -> ChatState:
        """
        Execute deep research using the ResearchSystem.
        
        This is where your comprehensive research engine is invoked.
        """
        research_query = state["research_query"]
        
        print(f"\n Initiating deep research on: '{research_query}'")
        print("=" * 70)
        print("This will perform comprehensive multi-source research...")
        print("=" * 70 + "\n")
        
        try:
            # Initialize ResearchSystem with all optimizations
            if self.research_system is None:
                self.research_system = ResearchSystem(
                    enable_cache=True,
                    enable_streaming=True,
                    use_langgraph_planner=False,  # Keep planning direct for performance
                    interactive=False  # Disable interactive mode for chatbot
                )
            
            # Execute research
            report = self.research_system.execute_research(research_query)
            
            # Format the response
            state["response"] = f"""I've completed comprehensive research on your query.

{report}

---
*This report was generated using deep research with multi-source verification.*
"""
        
        except Exception as e:
            state["response"] = f"""I encountered an error during deep research: {str(e)}

Would you like me to try a simpler search instead?"""
        
        return state
    
    def _format_response(self, state: ChatState) -> ChatState:
        """Format and finalize the response."""
        # Add response to message history
        state["messages"].append(state["user_input"])
        state["messages"].append(state["response"])
        
        return state
    
    def chat(self, user_input: str, thread_id: str = "default") -> str:
        """
        Process a user message and return the bot's response.
        
        Args:
            user_input: The user's message
            thread_id: Conversation thread identifier for multi-user support
            
        Returns:
            The chatbot's response
        """
        # Initialize state
        initial_state = {
            "messages": [],
            "user_input": user_input,
            "intent": "",
            "research_query": "",
            "response": "",
            "research_mode": self.enable_research
        }
        
        # Configure for this thread
        config = {"configurable": {"thread_id": thread_id}}
        
        # Execute the graph
        final_state = self.graph.invoke(initial_state, config)
        
        return final_state["response"]
    
    def interactive_mode(self):
        """Run the chatbot in interactive console mode."""
        print("=" * 70)
        print(" AI ChatBot with Deep Research")
        print("=" * 70)
        print("\nCommands:")
        print("  - Type your message normally for quick responses")
        print("  - Use 'deep research <topic>' for comprehensive research")
        print("  - Type 'exit' or 'quit' to end")
        print("=" * 70 + "\n")
        
        thread_id = "interactive_session"
        
        while True:
            try:
                user_input = input("\n You: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ["exit", "quit", "bye"]:
                    print("\n Goodbye!\n")
                    break
                
                # Get response
                response = self.chat(user_input, thread_id)
                
                print(f"\n Assistant:\n{response}\n")
                
            except KeyboardInterrupt:
                print("\n\n Goodbye!\n")
                break
            except Exception as e:
                print(f"\n Error: {e}\n")


def demo_chatbot():
    """Demonstration of the chatbot integration."""
    print("\n" + "=" * 70)
    print("CHATBOT INTEGRATION DEMO")
    print("=" * 70 + "\n")
    
    # Initialize chatbot
    bot = ChatBot(enable_research=True)
    
    # Demo scenarios
    test_queries = [
        "Hello! How are you?",
        "What is machine learning?",
        "Deep research: What are the latest developments in quantum computing?",
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*70}")
        print(f"Demo Query {i}: {query}")
        print('='*70)
        
        response = bot.chat(query, thread_id=f"demo_{i}")
        print(f"\nResponse:\n{response}\n")
        
        if i < len(test_queries):
            input("Press Enter to continue to next demo...")
    
    print("\n" + "=" * 70)
    print("Demo complete! The chatbot can:")
    print("   Handle normal conversational queries")
    print("   Classify intent automatically")
    print("   Route to deep research when needed")
    print("   Maintain conversation context")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    import sys
    
    # Check if LangGraph is installed
    try:
        import langgraph
        import langchain_core
    except ImportError:
        print("\n  LangGraph not installed!")
        print("\nInstall with: pip install langgraph langchain-core")
        print("Or run: pip install -r requirements.txt\n")
        sys.exit(1)
    
    # Run based on command line args
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        demo_chatbot()
    else:
        # Interactive mode
        bot = ChatBot(enable_research=True)
        bot.interactive_mode()

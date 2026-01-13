"use client"

import type React from "react"

import { useState, useRef, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Menu, Send, Plus, MessageSquare, Sparkles } from "lucide-react"
import { cn } from "@/lib/utils"
import ChatMessage from "@/components/chat-message"
import TypingIndicator from "@/components/typing-indicator"
import { sendChatMessage } from "@/lib/api"

type Message = {
  id: string
  role: "user" | "assistant"
  content: string
  timestamp: Date
}

type ChatHistory = {
  id: string
  title: string
  messages: Message[]
  timestamp: Date
}

export default function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [isTyping, setIsTyping] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [chatHistory, setChatHistory] = useState<ChatHistory[]>([])
  const [currentChatId, setCurrentChatId] = useState<string | null>(null)
  const [isUserScrolling, setIsUserScrolling] = useState(false)
  const [deepResearchMode, setDeepResearchMode] = useState(false)
  const [pendingPlan, setPendingPlan] = useState<any | null>(null)
  const [currentQuery, setCurrentQuery] = useState<string>("")

  const chatContainerRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const scrollTimeoutRef = useRef<NodeJS.Timeout | null>(null)

  useEffect(() => {
    if (!isUserScrolling && chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight
    }
  }, [messages, isTyping, isUserScrolling])

  const handleScroll = () => {
    if (!chatContainerRef.current) return

    const { scrollTop, scrollHeight, clientHeight } = chatContainerRef.current
    const isAtBottom = Math.abs(scrollHeight - scrollTop - clientHeight) < 50

    setIsUserScrolling(!isAtBottom)

    if (scrollTimeoutRef.current) {
      clearTimeout(scrollTimeoutRef.current)
    }

    if (isAtBottom) {
      scrollTimeoutRef.current = setTimeout(() => {
        setIsUserScrolling(false)
      }, 100)
    }
  }

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto"
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`
    }
  }, [input])

  const handleSend = async () => {
    if (!input.trim() || isTyping) return

    const userInput = input.trim().toLowerCase()
    
    // Handle plan review state
    if (pendingPlan) {
      const userMessage: Message = {
        id: Date.now().toString(),
        role: "user",
        content: input,
        timestamp: new Date(),
      }
      
      setMessages((prev) => [...prev, userMessage])
      setInput("")
      setIsTyping(true)
      setIsUserScrolling(false)

      try {
        // Handle the three options
        if (userInput === "Start Research" || userInput === "start") {
          // Execute the research
          const response = await fetch("http://localhost:8000/api/research/execute", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              query: currentQuery,
              plan: pendingPlan,
              enable_cache: true,
            }),
          })

          if (!response.ok) throw new Error("Failed to execute research")

          const data = await response.json()
          
          const aiMessage: Message = {
            id: (Date.now() + 1).toString(),
            role: "assistant",
            content: `# Research Report\n\n${data.report}\n\n---\n\n**Metrics:**\n- API Calls: ${data.metrics?.total_api_calls || "N/A"}\n- Tokens: ${data.metrics?.total_tokens || "N/A"}\n- Cost: $${data.metrics?.total_cost?.toFixed(4) || "N/A"}`,
            timestamp: new Date(),
          }
          
          setMessages((prev) => [...prev, aiMessage])
          setPendingPlan(null)
          setCurrentQuery("")
          
        } else if (userInput === "quit" || userInput === "cancel") {
          // Cancel the research
          const aiMessage: Message = {
            id: (Date.now() + 1).toString(),
            role: "assistant",
            content: "Research cancelled. Feel free to start a new query!",
            timestamp: new Date(),
          }
          
          setMessages((prev) => [...prev, aiMessage])
          setPendingPlan(null)
          setCurrentQuery("")
          
        } else {
          // Modify the plan with user feedback
          const response = await fetch("http://localhost:8000/api/research/refine", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              query: currentQuery,
              plan: pendingPlan,
              feedback: input,
            }),
          })

          if (!response.ok) throw new Error("Failed to refine plan")

          const data = await response.json()
          
          const aiMessage: Message = {
            id: (Date.now() + 1).toString(),
            role: "assistant",
            content: data.response,
            timestamp: new Date(),
          }
          
          setMessages((prev) => [...prev, aiMessage])
          setPendingPlan(data.plan)
        }
      } catch (error) {
        console.error("Error:", error)
        const errorMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content: "An error occurred. Please try again.",
          timestamp: new Date(),
        }
        setMessages((prev) => [...prev, errorMessage])
      } finally {
        setIsTyping(false)
      }
      return
    }

    // Normal chat flow
    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input,
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInput("")
    setIsTyping(true)
    setIsUserScrolling(false)

    try {
      // Call the backend API
      const response = await sendChatMessage({
        message: input,
        thread_id: currentChatId || "default",
        deep_research: deepResearchMode,
      })

      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: response.response,
        timestamp: new Date(),
      }

      setMessages((prev) => [...prev, aiMessage])
      
      // Check if we got a plan for review
      if (response.intent === "plan_review" && response.plan) {
        setPendingPlan(response.plan)
        setCurrentQuery(input)
        setInput("Start Research")  // Pre-fill with default action
      }
    } catch (error) {
      console.error("Error sending message:", error)
      
      // Fallback to mock response if API is unavailable
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: "Unable to connect to the research backend. Please ensure the API server is running at http://localhost:8000\n\nTo start the backend:\n```bash\npython api_server.py\n```",
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setIsTyping(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const startNewChat = () => {
    if (messages.length > 0 && currentChatId) {
      const chatTitle = messages[0]?.content.slice(0, 50) || "New Chat"
      setChatHistory((prev) => [
        {
          id: currentChatId,
          title: chatTitle,
          messages,
          timestamp: new Date(),
        },
        ...prev,
      ])
    }
    setMessages([])
    setCurrentChatId(Date.now().toString())
  }

  const loadChat = (chat: ChatHistory) => {
    if (messages.length > 0 && currentChatId && currentChatId !== chat.id) {
      const chatTitle = messages[0]?.content.slice(0, 50) || "New Chat"
      setChatHistory((prev) => [
        {
          id: currentChatId,
          title: chatTitle,
          messages,
          timestamp: new Date(),
        },
        ...prev.filter((c) => c.id !== currentChatId),
      ])
    }
    setMessages(chat.messages)
    setCurrentChatId(chat.id)
    setSidebarOpen(false)
  }

  return (
    <div className="flex h-screen overflow-hidden">
      <aside
        className={cn(
          "fixed lg:static inset-y-0 left-0 z-50 w-72 transform transition-transform duration-300 ease-in-out lg:transform-none",
          sidebarOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0",
        )}
      >
        <div className="h-full backdrop-blur-md bg-white/[0.08] border-r border-white/20 flex flex-col">
          <div className="p-4 border-b border-white/20">
            <Button
              onClick={startNewChat}
              className="w-full bg-primary/80 hover:bg-primary text-primary-foreground rounded-full shadow-[0_0_20px_rgba(59,130,246,0.5)] hover:shadow-[0_0_30px_rgba(59,130,246,0.7)] transition-all"
            >
              <Plus className="w-4 h-4 mr-2" />
              New Chat
            </Button>
          </div>

          <div className="flex-1 overflow-y-auto p-3 space-y-2">
            {chatHistory.length === 0 ? (
              <div className="text-center text-muted-foreground py-8 px-4">
                <MessageSquare className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm">No chat history yet</p>
              </div>
            ) : (
              chatHistory.map((chat) => (
                <button
                  key={chat.id}
                  onClick={() => loadChat(chat)}
                  className={cn(
                    "w-full text-left p-3 rounded-2xl transition-all backdrop-blur-md",
                    "hover:bg-white/[0.12] border border-transparent hover:border-white/20",
                    "hover:shadow-[0_0_15px_rgba(59,130,246,0.3)]",
                    currentChatId === chat.id && "bg-white/[0.12] border-white/20",
                  )}
                >
                  <p className="text-sm font-medium truncate text-foreground">{chat.title}</p>
                  <p className="text-xs text-muted-foreground mt-1">{chat.messages.length} messages</p>
                </button>
              ))
            )}
          </div>
        </div>
      </aside>

      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden backdrop-blur-sm"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <main className="flex-1 flex flex-col h-screen">
        <header className="backdrop-blur-md bg-white/[0.08] border-b border-white/20 p-4">
          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="lg:hidden rounded-full hover:bg-white/10"
            >
              <Menu className="w-5 h-5" />
            </Button>
            <h1 className="text-lg font-semibold text-balance">AI Chat Assistant</h1>
            <div className="ml-auto">
              <Button
                onClick={() => setDeepResearchMode(!deepResearchMode)}
                className={cn(
                  "rounded-full transition-all backdrop-blur-md",
                  deepResearchMode
                    ? "bg-accent/80 hover:bg-accent text-accent-foreground shadow-[0_0_20px_rgba(59,130,246,0.6)]"
                    : "bg-white/[0.08] hover:bg-white/[0.12] text-foreground border border-white/20",
                )}
              >
                <Sparkles className="w-4 h-4 mr-2" />
                Deep Research
              </Button>
            </div>
          </div>
        </header>

        <div ref={chatContainerRef} onScroll={handleScroll} className="flex-1 overflow-y-auto px-4 py-6 space-y-6">
          {messages.length === 0 ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center max-w-md">
                <div className="w-16 h-16 rounded-full bg-primary/20 flex items-center justify-center mx-auto mb-4 shadow-[0_0_30px_rgba(59,130,246,0.4)]">
                  <MessageSquare className="w-8 h-8 text-primary" />
                </div>
                <h2 className="text-2xl font-semibold mb-2 text-balance">Start a conversation</h2>
                <p className="text-muted-foreground text-balance">
                  Ask me anything and I'll help you with detailed responses
                </p>
              </div>
            </div>
          ) : (
            <>
              {messages.map((message) => (
                <ChatMessage key={message.id} message={message} />
              ))}
              {isTyping && <TypingIndicator />}
            </>
          )}
        </div>

        <div className="p-4 border-t border-white/10">
          <div className="max-w-3xl mx-auto">
            <div className="backdrop-blur-md bg-white/[0.08] border border-white/20 rounded-[2rem] shadow-[0_0_30px_rgba(59,130,246,0.3)] hover:shadow-[0_0_40px_rgba(59,130,246,0.4)] transition-all p-2">
              <div className="flex items-end gap-2">
                <Textarea
                  ref={textareaRef}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder={
                    pendingPlan 
                      ? "Type 'Start Research' to begin, or provide feedback to modify the plan, or type 'quit' to cancel" 
                      : deepResearchMode 
                        ? "What do you want to Research?" 
                        : "Type your message..."
                  }
                  className="flex-1 min-h-[56px] max-h-[200px] resize-none bg-transparent border-0 focus-visible:ring-0 focus-visible:ring-offset-0 px-4 py-4 text-foreground placeholder:text-muted-foreground"
                  rows={1}
                />
                <Button
                  onClick={handleSend}
                  disabled={!input.trim() || isTyping}
                  size="icon"
                  className="rounded-full w-12 h-12 bg-primary hover:bg-primary/90 disabled:opacity-50 shadow-[0_0_20px_rgba(59,130,246,0.5)] hover:shadow-[0_0_30px_rgba(59,130,246,0.7)] transition-all flex-shrink-0"
                >
                  <Send className="w-5 h-5" />
                </Button>
              </div>
            </div>
            <p className="text-xs text-muted-foreground text-center mt-2">
              Press Enter to send, Shift+Enter for new line
            </p>
          </div>
        </div>
      </main>
    </div>
  )
}

function generateAIResponse(input: string, deepResearchMode: boolean): string {
  const responses = [
    `# Great question!

Here's a detailed response to your query: **${input}**

## Key Points

1. First important consideration
2. Second key aspect
3. Third critical element

\`\`\`javascript
// Here's a code example
function example() {
  console.log("This is a code block with syntax highlighting");
  return true;
}
\`\`\`

> This is an important note to remember!

Let me know if you need more details on any of these points.`,

    `I understand you're asking about: **${input}**

### Analysis

This is a fascinating topic! Here are some thoughts:

- **Point A**: First consideration with detailed explanation
- **Point B**: Second important aspect
- **Point C**: Third critical factor

\`\`\`typescript
interface Response {
  status: 'success' | 'error';
  data: string;
}
\`\`\`

Feel free to ask follow-up questions!`,

    `Thanks for your question about **${input}**!

## Here's what I found:

The answer involves several components:

1. **Primary Factor**: Main consideration here
2. **Secondary Aspect**: Additional details
3. **Conclusion**: Final thoughts

\`\`\`python
def process_data(input):
    # Process the input
    result = transform(input)
    return result
\`\`\`

Would you like me to elaborate on any specific part?`,
  ]

  return deepResearchMode ? responses[0] : responses[Math.floor(Math.random() * 2)]
}

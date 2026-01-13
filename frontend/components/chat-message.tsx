"use client"

import { cn } from "@/lib/utils"
import ReactMarkdown from "react-markdown"
import { User, Bot, ExternalLink } from "lucide-react"
import { useState } from "react"

type Message = {
  id: string
  role: "user" | "assistant"
  content: string
  timestamp: Date
}

export default function ChatMessage({ message }: { message: Message }) {
  const isUser = message.role === "user"
  const [referencesExpanded, setReferencesExpanded] = useState(false)

  // Extract references from the content
  const extractReferences = (content: string) => {
    const refSection = content.match(/## References\n\n([\s\S]*?)(?=\n\n##|\n\n```|$)/);
    if (!refSection) return null;
    
    const refs: { num: string; url: string }[] = [];
    const refLines = refSection[1].split('\n');
    
    refLines.forEach(line => {
      const match = line.match(/\[\^(\d+)\]:\s*(.+)/);
      if (match) {
        refs.push({ num: match[1], url: match[2].trim() });
      }
    });
    
    return refs.length > 0 ? refs : null;
  }

  // Replace citation syntax with superscript
  const formatCitations = (content: string) => {
    // First, remove the References section from main content
    content = content.replace(/## References\n\n[\s\S]*?(?=\n\n##|\n\n```|$)/, '');
    
    return content;
  }

  // Component to render text with citations as superscript
  const CitationText = ({ children }: { children: any }) => {
    const processText = (text: string) => {
      const parts = [];
      let lastIndex = 0;
      const regex = /\[\^([\d\s,]+)\]/g;
      let match;
      
      while ((match = regex.exec(text)) !== null) {
        // Add text before citation
        if (match.index > lastIndex) {
          parts.push(text.substring(lastIndex, match.index));
        }
        
        // Add citation as superscript
        const numbers = match[1].split(',').map((n: string) => n.trim());
        numbers.forEach((num: string, idx: number) => {
          parts.push(
            <sup key={`${match.index}-${idx}`} className="text-blue-400 font-semibold mx-0.5">
              [{num}]
            </sup>
          );
        });
        
        lastIndex = regex.lastIndex;
      }
      
      // Add remaining text
      if (lastIndex < text.length) {
        parts.push(text.substring(lastIndex));
      }
      
      return parts.length > 0 ? parts : text;
    };

    // Handle different types of children
    if (typeof children === 'string') {
      return <>{processText(children)}</>;
    }
    
    if (Array.isArray(children)) {
      return <>{children.map((child, idx) => {
        if (typeof child === 'string') {
          return <span key={idx}>{processText(child)}</span>;
        }
        return <span key={idx}>{child}</span>;
      })}</>;
    }
    
    return <>{children}</>;
  }

  const references = !isUser ? extractReferences(message.content) : null;
  const formattedContent = !isUser ? formatCitations(message.content) : message.content;

  return (
    <div className={cn("flex gap-4 items-start", isUser ? "justify-end" : "justify-start")}>
      {!isUser && (
        <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center flex-shrink-0 shadow-[0_0_20px_rgba(147,51,234,0.4)] border border-primary/30">
          <Bot className="w-5 h-5 text-primary" />
        </div>
      )}

      <div
        className={cn(
          "max-w-[80%] rounded-3xl backdrop-blur-md border px-5 py-4 transition-all",
          isUser
            ? "bg-primary/80 text-primary-foreground border-primary/50 shadow-[0_0_20px_rgba(147,51,234,0.5)]"
            : "bg-white/[0.08] text-foreground border-white/20 shadow-[0_0_20px_rgba(147,51,234,0.2)]",
        )}
      >
        {isUser ? (
          <p className="leading-relaxed text-pretty">{message.content}</p>
        ) : (
          <>
            <div className="prose prose-invert prose-sm max-w-none">
              <ReactMarkdown
                components={{
                  code({ node, className, children, ...props }: any) {
                    const match = /language-(\w+)/.exec(className || "")
                    const language = match ? match[1] : ""
                    const inline = !className

                    return !inline ? (
                      <div className="relative my-4 rounded-2xl bg-white/[0.05] border border-white/10 overflow-hidden">
                        {language && (
                          <div className="px-4 py-2 bg-white/[0.03] border-b border-white/10 text-xs text-muted-foreground font-mono">
                            {language}
                          </div>
                        )}
                        <pre className="p-4 overflow-x-auto">
                          <code className="text-sm font-mono text-foreground leading-relaxed" {...props}>
                            {children}
                          </code>
                        </pre>
                      </div>
                    ) : (
                      <code className="bg-white/10 px-1.5 py-0.5 rounded text-accent font-mono text-sm" {...props}>
                        {children}
                      </code>
                    )
                  },
                  h1: ({ children }) => (
                    <h1 className="text-xl font-bold mt-4 mb-2 text-white text-balance">
                      <CitationText>{children}</CitationText>
                    </h1>
                  ),
                  h2: ({ children }) => (
                    <h2 className="text-lg font-semibold mt-3 mb-2 text-white text-balance">
                      <CitationText>{children}</CitationText>
                    </h2>
                  ),
                  h3: ({ children }) => (
                    <h3 className="text-base font-semibold mt-2 mb-1 text-white text-balance">
                      <CitationText>{children}</CitationText>
                    </h3>
                  ),
                  p: ({ children }) => (
                    <p className="leading-relaxed mb-3 text-gray-100 text-pretty">
                      <CitationText>{children}</CitationText>
                    </p>
                  ),
                  ul: ({ children }) => (
                    <ul className="list-disc list-inside mb-3 space-y-1 text-gray-100">{children}</ul>
                  ),
                  ol: ({ children }) => (
                    <ol className="list-decimal list-inside mb-3 space-y-1 text-white">{children}</ol>
                  ),
                  li: ({ children }) => (
                    <li className="text-gray-100">
                      <CitationText>{children}</CitationText>
                    </li>
                  ),
                  blockquote: ({ children }) => (
                    <blockquote className="border-l-4 border-accent pl-4 italic my-3 text-gray-300">
                      <CitationText>{children}</CitationText>
                    </blockquote>
                  ),
                  strong: ({ children }) => (
                    <strong className="font-semibold text-white">
                      <CitationText>{children}</CitationText>
                    </strong>
                  ),
                  em: ({ children }) => (
                    <em>
                      <CitationText>{children}</CitationText>
                    </em>
                  ),
                }}
              >
                {formattedContent}
              </ReactMarkdown>
            </div>

            {references && references.length > 0 && (
              <div className="mt-4 border-t border-white/10 pt-4">
                <button
                  onClick={() => setReferencesExpanded(!referencesExpanded)}
                  className="flex items-center gap-2 text-sm font-semibold text-white hover:text-accent transition-colors mb-2"
                >
                  <span> References ({references.length})</span>
                  <span className="text-xs">{referencesExpanded ? '▼' : '▶'}</span>
                </button>
                
                {referencesExpanded && (
                  <div className="space-y-2 max-h-64 overflow-y-auto">
                    {references.map((ref) => (
                      <div key={ref.num} className="flex gap-2 text-xs">
                        <span className="text-blue-400 font-semibold font-mono flex-shrink-0">[{ref.num}]</span>
                        <a
                          href={ref.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-gray-300 hover:text-white break-all flex items-start gap-1 group"
                        >
                          <span className="flex-1">{ref.url}</span>
                          <ExternalLink className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0 mt-0.5" />
                        </a>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </>
        )}
      </div>

      {isUser && (
        <div className="w-10 h-10 rounded-full bg-accent/20 flex items-center justify-center flex-shrink-0 shadow-[0_0_20px_rgba(192,132,252,0.4)] border border-accent/30">
          <User className="w-5 h-5 text-accent" />
        </div>
      )}
    </div>
  )
}

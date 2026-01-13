import { Bot } from "lucide-react"

export default function TypingIndicator() {
  return (
    <div className="flex gap-4 items-start">
      <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center flex-shrink-0 shadow-[0_0_20px_rgba(147,51,234,0.4)] border border-primary/30">
        <Bot className="w-5 h-5 text-primary" />
      </div>

      <div className="max-w-[80%] rounded-3xl backdrop-blur-md border bg-white/[0.08] border-white/20 shadow-[0_0_20px_rgba(147,51,234,0.2)] px-5 py-4">
        <div className="flex items-center gap-2">
          <div className="flex gap-1">
            <div className="w-2 h-2 rounded-full bg-primary animate-bounce [animation-delay:0ms]" />
            <div className="w-2 h-2 rounded-full bg-primary animate-bounce [animation-delay:150ms]" />
            <div className="w-2 h-2 rounded-full bg-primary animate-bounce [animation-delay:300ms]" />
          </div>
          <span className="text-sm text-muted-foreground">Thinking...</span>
        </div>
      </div>
    </div>
  )
}

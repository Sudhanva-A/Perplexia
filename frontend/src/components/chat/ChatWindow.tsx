// src/components/ChatWindow.tsx
import { useEffect, useRef } from "react";
import { ChatMessage as ChatMessageComponent } from "./ChatMessage";
import { ChatInput } from "./ChatInput";
import { ChatMessage } from "../../types";

interface ChatWindowProps {
  messages: ChatMessage[];
  onSendMessage: (message: string) => void;
  isLoading: boolean;
  sessionId?: number;
  isSearchMode: boolean;
  toggleSearchMode: () => void;
}

export function ChatWindow({
  messages,
  onSendMessage,
  isLoading,
  sessionId,
  isSearchMode,
  toggleSearchMode,
}: ChatWindowProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="flex h-full w-full flex-col items-center">
      <div className="flex-1 w-full max-w-3xl">
        {messages.length === 0 ? (
          <div className="flex h-full items-center justify-center">
            <div className="max-w-md text-center">
              <h2 className="text-2xl font-bold">Welcome to Perplexia</h2>
              <p className="mt-2 text-muted-foreground">
                Start a conversation by typing a message below.
              </p>
            </div>
          </div>
        ) : (
          <>
            <div className="h-12 lg:h-0 bg-neutral-800 md:bg-[#191a1a] flex justify-center p-2 fixed top-0 w-full max-w-3xl z-10">
              <h2 className="text-2xl lg:hidden font-semibold font-mono">
                Perplexia
              </h2>
            </div>
            <div className="w-full mb-24 mt-12 lg:mt-4">
              {messages.map((message) => (
                <ChatMessageComponent key={message.id} message={message} />
              ))}
              <div ref={messagesEndRef} />
            </div>
          </>
        )}
      </div>

      <ChatInput
        messages={messages}
        onSendMessage={onSendMessage}
        isLoading={isLoading}
        sessionId={sessionId}
        isSearchMode={isSearchMode}
        toggleSearchMode={toggleSearchMode}
      />
    </div>
  );
}

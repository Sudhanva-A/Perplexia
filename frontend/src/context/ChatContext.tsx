// src/contexts/ChatContext.tsx
import { createContext, useContext, ReactNode } from "react";
import { useChat as useChatHook } from "../hooks/useChat";
import { ChatMessage, ChatSession } from "../types";

// Define the type for the context value
interface ChatContextType {
  messages: ChatMessage[];
  sessions: ChatSession[];
  currentSession: ChatSession | null;
  isLoading: boolean;
  messageCount: number;
  sessionId: number | undefined;
  isSearchMode: boolean;
  switchSession: (id?: number) => void;
  sendMessage: (message: string) => Promise<void>;
  createSession: (name?: string) => Promise<any>;
  deleteSession: (id: number) => Promise<void>;
  renameSession: (id: number, name: string) => Promise<void>;
  fetchSessions: () => Promise<void>;
  fetchSession: (id: number) => Promise<void>;
  toggleSearchMode: () => void;
}

// Create the context
const ChatContext = createContext<ChatContextType | null>(null);

// Provider component
export function ChatProvider({
  children,
  sessionId,
}: {
  children: ReactNode;
  sessionId?: number;
}) {
  const chatState = useChatHook(sessionId);

  return (
    <ChatContext.Provider value={chatState}>{children}</ChatContext.Provider>
  );
}

// Custom hook to use the chat context
export function useChat() {
  const context = useContext(ChatContext);
  if (context === null) {
    throw new Error("useChat must be used within a ChatProvider");
  }
  return context;
}

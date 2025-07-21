// src/routes/chat/$sessionId.tsx
import { createFileRoute, redirect } from "@tanstack/react-router";
import { Layout } from "../../components/Layout";
import { ChatWindow } from "../../components/chat/ChatWindow";
import { useChat } from "../../context/ChatContext";
import { useAuth } from "../../context/AuthContext";
import { useEffect } from "react";

export const Route = createFileRoute("/chat/$sessionId")({
  component: ChatSessionPage,
  beforeLoad: async ({ params }) => {
    // Verify user is authenticated
    const token = localStorage.getItem("clerk-token");
    if (!token) {
      throw redirect({ to: "/login" });
    }

    // Validate the session ID is a number
    if (isNaN(Number(params.sessionId))) {
      throw redirect({ to: "/chat" });
    }
  },
});

function ChatSessionPage() {
  const { sessionId } = Route.useParams();
  const sessionIdNum = parseInt(sessionId);

  const {
    messages,
    sendMessage,
    isLoading,
    switchSession,
    isSearchMode,
    toggleSearchMode,
  } = useChat();

  const { isAuthenticated, isLoading: authLoading } = useAuth();

  // When the route parameter changes, update the current session
  useEffect(() => {
    switchSession(sessionIdNum);
  }, [sessionIdNum, switchSession]);

  // If still checking auth, show loading
  if (authLoading) {
    return (
      <Layout>
        <div className="flex h-screen items-center justify-center">
          <div className="flex flex-col items-center gap-4">
            <div className="h-12 w-12 animate-spin rounded-full border-4 border-primary border-t-transparent"></div>
            <p className="text-sm text-muted-foreground">Loading Chat</p>
          </div>
        </div>
      </Layout>
    );
  }

  // If not authenticated, user should have been redirected by beforeLoad
  if (!isAuthenticated) {
    return null;
  }

  return (
    <Layout sessionId={sessionIdNum}>
      <div
        className={`flex h-screen w-full flex-col overflow-y-auto overflow-x-hidden lg:pl-10 ${
          messages.length ? "items-start" : "items-center"
        }`}
      >
        <ChatWindow
          messages={messages}
          onSendMessage={(message) => sendMessage(message)}
          isLoading={isLoading}
          sessionId={sessionIdNum}
          isSearchMode={isSearchMode}
          toggleSearchMode={toggleSearchMode}
        />
      </div>
    </Layout>
  );
}

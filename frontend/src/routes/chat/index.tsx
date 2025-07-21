// src/routes/chat/index.tsx
import { createFileRoute, redirect } from "@tanstack/react-router";
import { Layout } from "../../components/Layout";
import { ChatWindow } from "../../components/chat/ChatWindow";
import { useChat } from "../../context/ChatContext";
import { useAuth } from "../../context/AuthContext";

export const Route = createFileRoute("/chat/")({
  component: ChatIndexPage,
  beforeLoad: async ({}) => {
    // Verify user is authenticated
    const token = localStorage.getItem("clerk-token");

    if (!token) {
      throw redirect({ to: "/" });
    }
  },
});

function ChatIndexPage() {
  const { messages, sendMessage, isLoading, isSearchMode, toggleSearchMode } =
    useChat();
  const { isAuthenticated, isLoading: authLoading } = useAuth();

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
    <Layout>
      <div
        className={`flex h-screen w-full flex-col overflow-y-auto overflow-x-hidden lg:pl-10 ${
          messages.length ? "items-start" : "items-center"
        }`}
      >
        <ChatWindow
          messages={messages}
          onSendMessage={sendMessage}
          isLoading={isLoading}
          isSearchMode={isSearchMode}
          toggleSearchMode={toggleSearchMode}
        />
      </div>
    </Layout>
  );
}

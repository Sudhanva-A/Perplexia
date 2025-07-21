// src/routes/index.tsx
import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { ChatWindow } from "../components/chat/ChatWindow";
import { Layout } from "../components/Layout";
import { useChat } from "../context/ChatContext";

export const Route = createFileRoute("/")({
  component: HomePage,
});

function HomePage() {
  const {
    messages,
    sendMessage,
    isLoading,
    messageCount,
    isSearchMode,
    toggleSearchMode,
  } = useChat();

  const navigate = useNavigate();

  // Handle sending a message
  const handleSendMessage = async (message: string) => {
    if (messageCount >= 2) {
      // Redirect to login after 2 messages (0-indexed)
      navigate({ to: "/login" });
      return;
    }
    await sendMessage(message);
  };

  return (
    <Layout>
      <div
        className={`flex h-screen w-full flex-col overflow-y-auto overflow-x-hidden lg:pl-10 ${
          messages.length ? "items-start" : "items-center"
        }`}
      >
        <ChatWindow
          messages={messages}
          onSendMessage={handleSendMessage}
          isLoading={isLoading}
          isSearchMode={isSearchMode}
          toggleSearchMode={toggleSearchMode}
        />
      </div>
    </Layout>
  );
}

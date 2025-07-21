import { ReactNode, useEffect } from "react";
import { Sidebar } from "./Sidebar";
import { useChat } from "../context/ChatContext";
import { useNavigate } from "@tanstack/react-router";

interface LayoutProps {
  children: ReactNode;
  showSidebar?: boolean;
  sessionId?: number;
}

export function Layout({
  children,
  showSidebar = true,
  sessionId,
}: LayoutProps) {
  const navigate = useNavigate();

  const {
    sessions,
    createSession,
    deleteSession,
    renameSession,
    switchSession,
  } = useChat();

  useEffect(() => {
    if (sessionId !== undefined) {
      switchSession(sessionId);
    }
  }, [sessionId, switchSession]);

  const handleCreateSession = async () => {
    const session = await createSession();
    if (session) {
      navigate({ to: `/chat/${session.id}` });
    }
  };

  return (
    <div className="flex h-screen text-slate-100 bg-[#191a1a]">
      {showSidebar && (
        <Sidebar
          sessions={sessions}
          onCreateSession={handleCreateSession}
          onDeleteSession={deleteSession}
          onRenameSession={renameSession}
          currentSessionId={sessionId}
        />
      )}
      <main className="relative flex h-full w-full flex-1 flex-col">
        {children}
      </main>
    </div>
  );
}

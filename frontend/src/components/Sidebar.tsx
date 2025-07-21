import { useState } from "react";
import { Link } from "@tanstack/react-router";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import {
  MessageSquare,
  Plus,
  Trash2,
  Edit2,
  LogOut,
  PanelLeft,
} from "lucide-react";
import { ChatSession } from "../types";
import { Sheet, SheetContent, SheetTrigger } from "./ui/sheet";
import { useAuth } from "../context/AuthContext";
import { useClerk } from "@clerk/clerk-react";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "./ui/dialog";
import { DialogDescription } from "@radix-ui/react-dialog";

interface SidebarProps {
  sessions: ChatSession[];
  onCreateSession: () => void;
  onDeleteSession: (id: number) => void;
  onRenameSession: (id: number, name: string) => void;
  currentSessionId?: number;
}

export function Sidebar({
  sessions,
  onCreateSession,
  onDeleteSession,
  onRenameSession,
  currentSessionId,
}: SidebarProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [editingSession, setEditingSession] = useState<number | null>(null);
  const [newName, setNewName] = useState("");
  const { isAuthenticated } = useAuth();
  const { signOut } = useClerk();

  const handleRename = (id: number) => {
    if (newName.trim()) {
      onRenameSession(id, newName);
      setEditingSession(null);
      setNewName("");
    }
  };

  const startEditing = (session: ChatSession) => {
    setEditingSession(session.id);
    setNewName(session.name);
  };

  return (
    <>
      {/* Mobile Sidebar */}
      <div className="flex lg:hidden absolute top-1 left-0 z-50">
        <Sheet open={isOpen} onOpenChange={setIsOpen}>
          <SheetTrigger asChild>
            <Button variant="ghost" size="icon" className="lg:hidden">
              <PanelLeft />
            </Button>
          </SheetTrigger>
          <SheetContent side="left" className="w-64 p-0">
            <div className="flex h-full flex-col">
              <SidebarContent
                sessions={sessions}
                onCreateSession={onCreateSession}
                onDeleteSession={onDeleteSession}
                editingSession={editingSession}
                setEditingSession={setEditingSession}
                newName={newName}
                setNewName={setNewName}
                startEditing={startEditing}
                handleRename={handleRename}
                currentSessionId={currentSessionId}
                setIsOpen={setIsOpen}
                isAuthenticated={isAuthenticated}
                signOut={signOut}
                mobile={true}
              />
            </div>
          </SheetContent>
        </Sheet>
      </div>

      {/* Desktop Sidebar */}
      <div className="hidden lg:flex lg:w-64 lg:flex-col">
        <SidebarContent
          sessions={sessions}
          onCreateSession={onCreateSession}
          onDeleteSession={onDeleteSession}
          editingSession={editingSession}
          setEditingSession={setEditingSession}
          newName={newName}
          setNewName={setNewName}
          startEditing={startEditing}
          handleRename={handleRename}
          currentSessionId={currentSessionId}
          isAuthenticated={isAuthenticated}
          signOut={signOut}
          mobile={false}
        />
      </div>
    </>
  );
}

interface SidebarContentProps {
  sessions: ChatSession[];
  onCreateSession: () => void;
  onDeleteSession: (id: number) => void;
  editingSession: number | null;
  setEditingSession: (id: number | null) => void;
  newName: string;
  setNewName: (name: string) => void;
  startEditing: (session: ChatSession) => void;
  handleRename: (id: number) => void;
  currentSessionId?: number;
  setIsOpen?: (open: boolean) => void;
  isAuthenticated: boolean;
  signOut: () => void;
  mobile: boolean;
}

function SidebarContent({
  sessions,
  onCreateSession,
  onDeleteSession,
  editingSession,
  setEditingSession,
  newName,
  setNewName,
  startEditing,
  handleRename,
  currentSessionId,
  setIsOpen,
  isAuthenticated,
  signOut,
  mobile,
}: SidebarContentProps) {
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [sessionToDelete, setSessionToDelete] = useState<number | null>(null);

  const handleDeleteClick = (e: React.MouseEvent, sessionId: number) => {
    e.preventDefault();
    e.stopPropagation();
    setSessionToDelete(sessionId);
    setDeleteDialogOpen(true);
  };

  const confirmDelete = () => {
    if (sessionToDelete !== null) {
      onDeleteSession(sessionToDelete);
      setDeleteDialogOpen(false);
      setSessionToDelete(null);
    }
  };

  return (
    <div
      className={`flex flex-col overflow-y-auto bg-background text-slate-100 p-3 bg-[#202222] font-mono ${
        setIsOpen ? "h-full" : ""
      } ${mobile ? "" : "h-full"} `}
    >
      <div className="mb-4 flex items-center justify-between px-2">
        <h2 className="text-2xl font-semibold font-mono">Perplexia</h2>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="icon"
            onClick={() => {
              onCreateSession();
              if (setIsOpen) setIsOpen(false);
            }}
            className="hover:bg-neutral-700 hover:cursor-pointer"
          >
            <Plus className="h-4 w-4" />
          </Button>
        </div>
      </div>

      <div className="space-y-1">
        {isAuthenticated ? (
          sessions.length > 0 ? (
            sessions.map((session) => (
              <div key={session.id} className="relative group">
                {editingSession === session.id ? (
                  <div className="flex items-center space-x-1 p-1">
                    <Input
                      value={newName}
                      onChange={(e) => setNewName(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter") handleRename(session.id);
                        if (e.key === "Escape") setEditingSession(null);
                      }}
                      autoFocus
                      className="h-8"
                    />
                    <Button
                      size="sm"
                      className="ml-2"
                      variant="default"
                      onClick={() => handleRename(session.id)}
                    >
                      Save
                    </Button>
                  </div>
                ) : (
                  <Link
                    to="/chat/$sessionId"
                    params={{ sessionId: session.id.toString() }}
                    className={`flex items-center space-x-2 rounded-md px-3 my-2 py-2 text-sm hover:bg-neutral-700 hover:cursor-pointer
                      ${
                        currentSessionId === session.id
                          ? "bg-[#191a1a] text-accent-foreground"
                          : "hover:bg-accent/50"
                      }`}
                    onClick={() => {
                      if (setIsOpen) setIsOpen(false);
                    }}
                  >
                    <MessageSquare className="h-4 w-4" />
                    <span className="flex-1 truncate">{session.name}</span>
                    <div
                      className={`flex space-x-1 ${
                        mobile
                          ? ""
                          : "opacity-0 group-hover:opacity-100 transition-opacity"
                      }`}
                    >
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-6 w-6 hover:text-green-700 hover:cursor-pointer"
                        onClick={(e) => {
                          e.preventDefault();
                          e.stopPropagation();
                          startEditing(session);
                        }}
                      >
                        <Edit2 className="h-3 w-3" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-6 w-6 hover:text-red-700 hover:cursor-pointer"
                        onClick={(e) => handleDeleteClick(e, session.id)}
                      >
                        <Trash2 className="h-3 w-3" />
                      </Button>
                    </div>
                    <Dialog
                      open={deleteDialogOpen}
                      onOpenChange={setDeleteDialogOpen}
                    >
                      <DialogContent className="bg-[#202222] text-slate-100 border-slate-900">
                        <DialogHeader>
                          <DialogTitle>Delete {session.name}</DialogTitle>
                          <DialogDescription>
                            Are you sure you want to delete this chat? This
                            action cannot be undone.
                          </DialogDescription>
                        </DialogHeader>
                        <DialogFooter>
                          <Button
                            variant="outline"
                            onClick={() => setDeleteDialogOpen(false)}
                          >
                            Cancel
                          </Button>
                          <Button variant="destructive" onClick={confirmDelete}>
                            Delete
                          </Button>
                        </DialogFooter>
                      </DialogContent>
                    </Dialog>
                  </Link>
                )}
              </div>
            ))
          ) : (
            <p className="px-3 py-2 text-sm text-muted-foreground">
              No conversations yet. Start a new chat!
            </p>
          )
        ) : (
          <Link
            to="/login"
            className="flex items-center space-x-2 rounded-md px-3 py-2 text-sm hover:bg-accent/50"
            onClick={() => {
              if (setIsOpen) setIsOpen(false);
            }}
          >
            Sign in to see your conversations
          </Link>
        )}
      </div>

      <div className="mt-auto pt-4">
        {isAuthenticated ? (
          <Button
            variant="outline"
            className="w-full justify-start hover:bg-neutral-700 hover:cursor-pointer"
            onClick={() => signOut()}
          >
            <LogOut className="mr-2 h-4 w-4" />
            Sign Out
          </Button>
        ) : (
          <Link
            to="/login"
            className="w-full"
            onClick={() => {
              if (setIsOpen) setIsOpen(false);
            }}
          >
            <Button
              variant="outline"
              className="w-full justify-start hover:bg-neutral-700 hover:cursor-pointer"
            >
              Sign In
            </Button>
          </Link>
        )}
      </div>
    </div>
  );
}

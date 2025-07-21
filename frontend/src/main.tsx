import ReactDOM from "react-dom/client";
import "./index.css";
import "./App.css";
import { ChatProvider } from "./context/ChatContext";
import { ClerkProvider } from "@clerk/clerk-react";
import { RouterProvider, createRouter } from "@tanstack/react-router";
import { routeTree } from "./routeTree.gen";
import { AuthProvider } from "./context/AuthContext";

// Create the router instance
const router = createRouter({
  routeTree,
  defaultPreload: "intent",
});

// Register the router for type safety
declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router;
  }
}

// Clerk publishable key
const clerkPubKey = "pk_test_YnVzeS1ibHVlYmlyZC0zNy5jbGVyay5hY2NvdW50cy5kZXYk";

if (!clerkPubKey) {
  throw new Error("Missing Clerk publishable key");
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <ClerkProvider publishableKey={clerkPubKey}>
    <AuthProvider>
      <ChatProvider>
        <RouterProvider router={router} />
      </ChatProvider>
    </AuthProvider>
  </ClerkProvider>
);

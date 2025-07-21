// src/context/AuthContext.tsx
import {
  createContext,
  useContext,
  ReactNode,
  useState,
  useEffect,
} from "react";
import { useClerk, useUser } from "@clerk/clerk-react";
import { userApi, setClerkSessionRef } from "../lib/api";
import { User } from "../types";

// Define the context type
interface AuthContextType {
  isAuthenticated: boolean;
  user: User | null;
  clerkUser: any;
  isLoading: boolean;
  authToken: string | null;
  signOut: () => Promise<void>;
}

// Create the context
const AuthContext = createContext<AuthContextType | null>(null);

// Provider component
export function AuthProvider({ children }: { children: ReactNode }) {
  const { isLoaded, isSignedIn, user } = useUser();
  const { session, signOut: clerkSignOut } = useClerk();
  const [appUser, setAppUser] = useState<User | null>(null);
  const [isLoadingUser, setIsLoadingUser] = useState(true);
  const [authToken, setAuthToken] = useState<string | null>(() => {
    return localStorage.getItem("clerk-token");
  });

  // Set the clerk session reference for API interceptors to use
  useEffect(() => {
    if (session) {
      setClerkSessionRef(session);
    }
  }, [session]);

  useEffect(() => {
    const fetchUser = async () => {
      if (isLoaded && isSignedIn) {
        try {
          // Store the session token in localStorage for API requests
          const token = await session?.getToken();
          if (token) {
            localStorage.setItem("clerk-token", token);
            setAuthToken(token);
          }

          // Get the user from our backend
          const { data } = await userApi.getCurrentUser();
          setAppUser(data);
        } catch (error) {
          console.error("Failed to fetch user:", error);
        } finally {
          setIsLoadingUser(false);
        }
      } else if (isLoaded) {
        localStorage.removeItem("clerk-token");
        setAppUser(null);
        setIsLoadingUser(false);
      }
    };

    fetchUser();
  }, [isLoaded, isSignedIn, session]);

  // Function to refresh token
  const refreshToken = async () => {
    if (isLoaded && isSignedIn && session) {
      try {
        const token = await session.getToken();
        if (token) {
          localStorage.setItem("clerk-token", token);
          setAuthToken(token);
          return token;
        }
      } catch (error) {
        console.error("Failed to refresh token:", error);
      }
    }
    return null;
  };

  // Set up periodic token refresh (every 5 minutes)
  useEffect(() => {
    if (!isLoaded || !isSignedIn) return;

    // Initial token refresh
    refreshToken();

    // Refresh token periodically
    const intervalId = setInterval(refreshToken, 5 * 60 * 1000); // 5 minutes

    return () => clearInterval(intervalId);
  }, [isLoaded, isSignedIn, session]);

  // Handle sign out
  const signOut = async () => {
    try {
      localStorage.removeItem("clerk-token");
      setAppUser(null);
      setAuthToken(null);
      await clerkSignOut();
    } catch (error) {
      console.error("Error signing out:", error);
    }
  };

  const authContextValue: AuthContextType = {
    isAuthenticated: !!appUser,
    user: appUser,
    clerkUser: user,
    isLoading: !isLoaded || isLoadingUser,
    authToken,
    signOut,
  };

  return (
    <AuthContext.Provider value={authContextValue}>
      {children}
    </AuthContext.Provider>
  );
}

// Custom hook to use the auth context
export function useAuth() {
  const context = useContext(AuthContext);
  if (context === null) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}

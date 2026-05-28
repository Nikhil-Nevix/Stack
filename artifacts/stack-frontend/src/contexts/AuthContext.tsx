import { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { useLocation } from "wouter";
import { User, LoginInput } from "@workspace/api-client-react";
import { useLogin, useLogout } from "@workspace/api-client-react";
import { useToast } from "@/hooks/use-toast";

interface AuthState {
  access_token: string;
  user: User;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (data: LoginInput) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [authState, setAuthState] = useState<AuthState | null>(() => {
    const saved = localStorage.getItem("stack_auth");
    return saved ? JSON.parse(saved) : null;
  });
  
  const [, setLocation] = useLocation();
  const { toast } = useToast();
  const loginMutation = useLogin();
  const logoutMutation = useLogout();

  const login = async (data: LoginInput) => {
    try {
      const res = await loginMutation.mutateAsync({ data });
      const newState = {
        access_token: res.access_token,
        user: res.user,
      };
      setAuthState(newState);
      localStorage.setItem("stack_auth", JSON.stringify(newState));
      
      toast({
        title: "Login Successful",
        description: `Welcome back, ${res.user.full_name}`,
      });

      if (res.user.role === "admin" || res.user.role === "agent") {
        setLocation("/dashboard");
      } else {
        setLocation("/my-dashboard");
      }
    } catch (error: any) {
      toast({
        variant: "destructive",
        title: "Login Failed",
        description: error?.data?.detail || "Invalid credentials",
      });
      throw error;
    }
  };

  const logout = async () => {
    try {
      await logoutMutation.mutateAsync();
    } catch (e) {
      // Ignore logout errors
    } finally {
      setAuthState(null);
      localStorage.removeItem("stack_auth");
      setLocation("/login");
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user: authState?.user ?? null,
        token: authState?.access_token ?? null,
        isAuthenticated: !!authState,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}

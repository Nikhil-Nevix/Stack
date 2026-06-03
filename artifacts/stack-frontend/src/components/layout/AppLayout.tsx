import { useEffect, useState } from "react";
import { Link, useLocation } from "wouter";
import { useAuth } from "@/contexts/AuthContext";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuItem,
  SidebarMenuButton,
  SidebarProvider,
  SidebarTrigger,
  SidebarInset
} from "@/components/ui/sidebar";
import { 
  LayoutDashboard, 
  Ticket, 
  FileText, 
  BarChart, 
  LineChart, 
  Settings, 
  BookOpen, 
  PlusCircle, 
  User as UserIcon,
  LogOut
} from "lucide-react";
import { getDataSource } from "@/lib/adminApi";

export function AppLayout({ children, title }: { children: React.ReactNode, title?: string }) {
  const { user, logout } = useAuth();
  const [location] = useLocation();
  const [showMockBanner, setShowMockBanner] = useState(false);

  useEffect(() => {
    let isMounted = true;

    const loadDataSource = async () => {
      try {
        const response = await getDataSource();
        if (isMounted) {
          setShowMockBanner(response?.data_source === "mock");
        }
      } catch (error) {
        if (isMounted) {
          setShowMockBanner(false);
        }
      }
    };

    if (user) {
      loadDataSource();
    }

    return () => {
      isMounted = false;
    };
  }, [user]);

  if (!user) return null;

  const isAdmin = user.role === "admin";
  const isAgent = user.role === "agent";
  const isUser = user.role === "user";

  const getInitials = (name: string) => name.split(" ").map(n => n[0]).join("").substring(0, 2).toUpperCase();

  return (
    <SidebarProvider>
      <Sidebar variant="sidebar" className="border-r-0 bg-sidebar text-sidebar-foreground">
        <SidebarHeader className="p-4 bg-sidebar">
          <div className="flex items-center gap-2 font-bold text-xl text-primary-foreground">
            <div className="bg-primary rounded-md p-1 text-sidebar-primary">
              <LayoutDashboard className="h-6 w-6" />
            </div>
            <span>STACK</span>
          </div>
          <p className="text-xs text-sidebar-foreground/70 uppercase font-semibold tracking-wider mt-1">IT Service Desk</p>
        </SidebarHeader>
        <SidebarContent className="bg-sidebar px-2">
          <SidebarMenu>
            {(isAdmin || isAgent) && (
              <>
                <SidebarMenuItem>
                  <SidebarMenuButton asChild isActive={location === "/dashboard"}>
                    <Link href="/dashboard">
                      <LayoutDashboard />
                      <span>Dashboard</span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
                <SidebarMenuItem>
                  <SidebarMenuButton asChild isActive={location.startsWith("/tickets")}>
                    <Link href="/tickets">
                      <Ticket />
                      <span>All Tickets</span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
                <SidebarMenuItem>
                  <SidebarMenuButton asChild isActive={location === "/reports"}>
                    <Link href="/reports">
                      <BarChart />
                      <span>Reports</span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              </>
            )}

            {isAdmin && (
              <>
                <SidebarMenuItem>
                  <SidebarMenuButton asChild isActive={location === "/logs"}>
                    <Link href="/logs">
                      <FileText />
                      <span>Audit Logs</span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
                <SidebarMenuItem>
                  <SidebarMenuButton asChild isActive={location === "/roi"}>
                    <Link href="/roi">
                      <LineChart />
                      <span>ROI Dashboard</span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
                <SidebarMenuItem>
                  <SidebarMenuButton asChild isActive={location === "/admin"}>
                    <Link href="/admin">
                      <Settings />
                      <span>Admin Config</span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
                <SidebarMenuItem>
                  <SidebarMenuButton asChild isActive={location === "/sops"}>
                    <Link href="/sops">
                      <BookOpen />
                      <span>SOP Manager</span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              </>
            )}

            {isUser && (
              <>
                <SidebarMenuItem>
                  <SidebarMenuButton asChild isActive={location === "/my-dashboard"}>
                    <Link href="/my-dashboard">
                      <LayoutDashboard />
                      <span>My Dashboard</span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
                <SidebarMenuItem>
                  <SidebarMenuButton asChild isActive={location === "/my-tickets"}>
                    <Link href="/my-tickets">
                      <Ticket />
                      <span>My Tickets</span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
                <SidebarMenuItem>
                  <SidebarMenuButton asChild isActive={location === "/raise-ticket"}>
                    <Link href="/raise-ticket">
                      <PlusCircle />
                      <span>Raise Ticket</span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              </>
            )}
          </SidebarMenu>
        </SidebarContent>
        <SidebarFooter className="p-4 bg-sidebar border-t border-sidebar-border">
          <div className="flex items-center gap-3 mb-4">
            <Avatar className="h-9 w-9 border border-sidebar-border">
              <AvatarFallback className="bg-sidebar-primary text-sidebar-primary-foreground">
                {getInitials(user.full_name)}
              </AvatarFallback>
            </Avatar>
            <div className="flex flex-col min-w-0 flex-1">
              <span className="text-sm font-medium truncate text-sidebar-foreground">{user.full_name}</span>
              <Badge variant="secondary" className="w-fit text-[10px] mt-0.5 px-1 py-0 h-4 bg-sidebar-accent text-sidebar-accent-foreground">
                {user.role}
              </Badge>
            </div>
          </div>
          <Button variant="outline" className="w-full justify-start text-sidebar-foreground border-sidebar-border hover:bg-sidebar-accent hover:text-sidebar-accent-foreground" onClick={logout}>
            <LogOut className="mr-2 h-4 w-4" />
            Logout
          </Button>
        </SidebarFooter>
      </Sidebar>
      <SidebarInset className="flex flex-col min-h-screen bg-background">
        <header className="flex h-14 lg:h-16 items-center gap-4 border-b bg-card px-6">
          <SidebarTrigger />
          <h1 className="text-lg font-semibold text-foreground">{title || "STACK Service Desk"}</h1>
        </header>
        {showMockBanner && (
          <div className="w-full bg-[#F47920] px-6 py-3 text-sm font-medium text-white shadow-sm">
            🟠 Mock Data Mode - You are viewing simulated data. 
            Switch to Live Data in Admin → System Settings.
          </div>
        )}
        <main className="flex-1 p-6">
          {children}
        </main>
      </SidebarInset>
    </SidebarProvider>
  );
}

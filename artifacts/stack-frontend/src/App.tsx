import { Switch, Route, Router as WouterRouter, useLocation } from "wouter";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import NotFound from "@/pages/not-found";
import { AuthProvider, useAuth } from "@/contexts/AuthContext";
import Login from "@/pages/login";
import { AppLayout } from "@/components/layout/AppLayout";
import AdminDashboard from "@/pages/dashboard/AdminDashboard";
import UserDashboard from "@/pages/dashboard/UserDashboard";
import AllTickets from "@/pages/tickets/AllTickets";
import TicketDetail from "@/pages/tickets/TicketDetail";
import RaiseTicket from "@/pages/tickets/RaiseTicket";
import Reports from "@/pages/dashboard/Reports";
import Logs from "@/pages/admin/Logs";
import ROIDashboard from "@/pages/dashboard/ROIDashboard";
import AdminConfig from "@/pages/admin/AdminConfig";
import SOPManager from "@/pages/admin/SOPManager";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

function ProtectedRoute({ component: Component, allowedRoles, title, ...rest }: any) {
  const { isAuthenticated, user } = useAuth();
  const [, setLocation] = useLocation();

  if (!isAuthenticated) {
    setLocation("/login");
    return null;
  }

  if (allowedRoles && user && !allowedRoles.includes(user.role)) {
    setLocation(user.role === "user" ? "/my-dashboard" : "/dashboard");
    return null;
  }

  return (
    <AppLayout title={title}>
      <Component {...rest} />
    </AppLayout>
  );
}

function HomeRedirect() {
  const { isAuthenticated, user } = useAuth();
  const [, setLocation] = useLocation();
  
  if (!isAuthenticated) {
    setLocation("/login");
  } else if (user?.role === "user") {
    setLocation("/my-dashboard");
  } else {
    setLocation("/dashboard");
  }
  return null;
}

function Router() {
  return (
    <Switch>
      <Route path="/login" component={Login} />
      <Route path="/">
        <HomeRedirect />
      </Route>
      <Route path="/dashboard">
        {() => <ProtectedRoute component={AdminDashboard} allowedRoles={["admin", "agent"]} title="Dashboard" />}
      </Route>
      <Route path="/my-dashboard">
        {() => <ProtectedRoute component={UserDashboard} allowedRoles={["user"]} title="My Dashboard" />}
      </Route>
      <Route path="/tickets">
        {() => <ProtectedRoute component={AllTickets} allowedRoles={["admin", "agent"]} title="All Tickets" />}
      </Route>
      <Route path="/my-tickets">
        {() => <ProtectedRoute component={AllTickets} allowedRoles={["user"]} title="My Tickets" />}
      </Route>
      <Route path="/tickets/:id">
        {() => <ProtectedRoute component={TicketDetail} title="Ticket Details" />}
      </Route>
      <Route path="/raise-ticket">
        {() => <ProtectedRoute component={RaiseTicket} allowedRoles={["user"]} title="Raise a New Ticket" />}
      </Route>
      <Route path="/reports">
        {() => <ProtectedRoute component={Reports} allowedRoles={["admin", "agent"]} title="Reports & Analytics" />}
      </Route>
      <Route path="/logs">
        {() => <ProtectedRoute component={Logs} allowedRoles={["admin"]} title="System Logs" />}
      </Route>
      <Route path="/roi">
        {() => <ProtectedRoute component={ROIDashboard} allowedRoles={["admin"]} title="ROI Dashboard" />}
      </Route>
      <Route path="/admin">
        {() => <ProtectedRoute component={AdminConfig} allowedRoles={["admin"]} title="Admin Configuration" />}
      </Route>
      <Route path="/sops">
        {() => <ProtectedRoute component={SOPManager} allowedRoles={["admin"]} title="SOP Manager" />}
      </Route>
      <Route>
        <NotFound />
      </Route>
    </Switch>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <WouterRouter base={import.meta.env.BASE_URL.replace(/\/$/, "")}>
          <AuthProvider>
            <Router />
          </AuthProvider>
        </WouterRouter>
        <Toaster />
      </TooltipProvider>
    </QueryClientProvider>
  );
}

export default App;

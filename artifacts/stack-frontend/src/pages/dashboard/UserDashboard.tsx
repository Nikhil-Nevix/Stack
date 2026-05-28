import { useGetMyDashboardSummary, useListTickets } from "@workspace/api-client-react";
import { useAuth } from "@/contexts/AuthContext";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { Link } from "wouter";
import { PlusCircle, Ticket, CheckCircle2, Clock } from "lucide-react";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { format } from "date-fns";

export default function UserDashboard() {
  const { user } = useAuth();
  const { data: summary, isLoading: loadingSummary } = useGetMyDashboardSummary();
  const { data: ticketsData, isLoading: loadingTickets } = useListTickets({ limit: 5 });

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-primary/5 p-6 rounded-lg border border-primary/10">
        <div>
          <h2 className="text-2xl font-bold text-foreground">Welcome back, {user?.full_name}!</h2>
          <p className="text-muted-foreground mt-1">How can IT help you today?</p>
        </div>
        <Button asChild size="lg" className="bg-accent hover:bg-accent/90 text-accent-foreground shrink-0">
          <Link href="/raise-ticket">
            <PlusCircle className="mr-2 h-5 w-5" />
            Raise New Ticket
          </Link>
        </Button>
      </div>

      {loadingSummary || !summary ? (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Skeleton className="h-32 w-full" />
          <Skeleton className="h-32 w-full" />
          <Skeleton className="h-32 w-full" />
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">My Open Tickets</CardTitle>
              <Ticket className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{summary.my_open}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">Resolved Tickets</CardTitle>
              <CheckCircle2 className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{summary.my_resolved}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">Avg Resolution Time</CardTitle>
              <Clock className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{summary.my_avg_resolution_mins ? `${Math.round(summary.my_avg_resolution_mins)} mins` : '-'}</div>
            </CardContent>
          </Card>
        </div>
      )}

      <Card>
        <CardHeader>
          <CardTitle>My Recent Tickets</CardTitle>
        </CardHeader>
        <CardContent>
          {loadingTickets ? <Skeleton className="h-64 w-full" /> : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Title</TableHead>
                  <TableHead>Category</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {ticketsData?.tickets.map(ticket => (
                  <TableRow key={ticket.ticket_id}>
                    <TableCell className="font-medium max-w-xs truncate">{ticket.title}</TableCell>
                    <TableCell>
                      <Badge variant="outline">{ticket.use_case}</Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant={ticket.status === 'resolved' ? 'default' : 'secondary'}>
                        {ticket.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {format(new Date(ticket.created_at), "MMM d, yyyy")}
                    </TableCell>
                    <TableCell className="text-right">
                      <Button variant="ghost" size="sm" asChild>
                        <Link href={`/tickets/${ticket.ticket_id}`}>View</Link>
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
                {(!ticketsData?.tickets || ticketsData.tickets.length === 0) && (
                  <TableRow>
                    <TableCell colSpan={5} className="text-center text-muted-foreground h-24">
                      You don't have any tickets yet.
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

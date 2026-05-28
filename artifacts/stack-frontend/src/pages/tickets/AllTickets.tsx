import { useState } from "react";
import { useListTickets } from "@workspace/api-client-react";
import { Link } from "wouter";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { format } from "date-fns";

export default function AllTickets() {
  const [status, setStatus] = useState<string>("");
  const [priority, setPriority] = useState<string>("");
  const [search, setSearch] = useState("");

  const { data, isLoading } = useListTickets({
    status: status === "all" ? undefined : status,
    priority: priority === "all" ? undefined : priority,
    search: search || undefined,
  });

  const getSourceIcon = (source: string) => {
    switch (source.toLowerCase()) {
      case 'web': return '🌐';
      case 'google chat': return '💬';
      case 'teams': return '🟦';
      case 'freshservice': return '📧';
      default: return '🌐';
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader className="pb-4">
          <CardTitle>Tickets</CardTitle>
          <div className="flex flex-col sm:flex-row gap-4 mt-4">
            <Input 
              placeholder="Search tickets..." 
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="max-w-sm"
              data-testid="input-search-tickets"
            />
            <Select value={status} onValueChange={setStatus}>
              <SelectTrigger className="w-[180px]" data-testid="select-status">
                <SelectValue placeholder="All Statuses" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Statuses</SelectItem>
                <SelectItem value="open">Open</SelectItem>
                <SelectItem value="in_progress">In Progress</SelectItem>
                <SelectItem value="resolved">Resolved</SelectItem>
                <SelectItem value="closed">Closed</SelectItem>
              </SelectContent>
            </Select>
            <Select value={priority} onValueChange={setPriority}>
              <SelectTrigger className="w-[180px]" data-testid="select-priority">
                <SelectValue placeholder="All Priorities" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Priorities</SelectItem>
                <SelectItem value="low">Low</SelectItem>
                <SelectItem value="medium">Medium</SelectItem>
                <SelectItem value="high">High</SelectItem>
                <SelectItem value="urgent">Urgent</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-2">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[100px]">ID</TableHead>
                  <TableHead>Source</TableHead>
                  <TableHead>Title</TableHead>
                  <TableHead>Use Case</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Priority</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data?.tickets.map((ticket) => (
                  <TableRow key={ticket.ticket_id}>
                    <TableCell className="font-mono text-xs">{ticket.ticket_id.split('-')[0]}</TableCell>
                    <TableCell title={ticket.source}>{getSourceIcon(ticket.source)}</TableCell>
                    <TableCell className="font-medium max-w-xs truncate">{ticket.title}</TableCell>
                    <TableCell>
                      <Badge variant="outline">{ticket.use_case.replace(/_/g, ' ')}</Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant={ticket.status === 'resolved' ? 'default' : 'secondary'}>
                        {ticket.status}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant={ticket.priority === 'urgent' ? 'destructive' : 'outline'}>
                        {ticket.priority}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {format(new Date(ticket.created_at), "MMM d")}
                    </TableCell>
                    <TableCell className="text-right">
                      <Button variant="ghost" size="sm" asChild data-testid={`button-view-ticket-${ticket.ticket_id}`}>
                        <Link href={`/tickets/${ticket.ticket_id}`}>View</Link>
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
                {(!data?.tickets || data.tickets.length === 0) && (
                  <TableRow>
                    <TableCell colSpan={8} className="text-center h-24 text-muted-foreground">
                      No tickets found.
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

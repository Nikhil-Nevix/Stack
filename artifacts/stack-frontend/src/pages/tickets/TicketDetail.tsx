import { useState } from "react";
import { useParams } from "wouter";
import { 
  useGetTicket, useListTicketNotes, useGetTicketTimeline, 
  useResolveTicket, useEscalateTicket, useAddTicketNote, useUpdateTicket,
  getGetTicketQueryKey, getListTicketNotesQueryKey, getGetTicketTimelineQueryKey 
} from "@workspace/api-client-react";
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from "@/components/ui/dialog";
import { format } from "date-fns";
import { useToast } from "@/hooks/use-toast";
import { useQueryClient } from "@tanstack/react-query";
import { Bot, User, Clock, CheckCircle2, AlertTriangle, MessageSquare, ListTodo } from "lucide-react";
import { Progress } from "@/components/ui/progress";
import { useAuth } from "@/contexts/AuthContext";

export default function TicketDetail() {
  const { id } = useParams();
  const { user } = useAuth();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [noteContent, setNoteContent] = useState("");
  const [isNoteOpen, setIsNoteOpen] = useState(false);

  const isAgentOrAdmin = user?.role === "admin" || user?.role === "agent";

  const { data: ticket, isLoading: loadingTicket } = useGetTicket(id!, { query: { enabled: !!id, queryKey: getGetTicketQueryKey(id!) } });
  const { data: notes, isLoading: loadingNotes } = useListTicketNotes(id!, { query: { enabled: !!id, queryKey: getListTicketNotesQueryKey(id!) } });
  const { data: timeline, isLoading: loadingTimeline } = useGetTicketTimeline(id!, { query: { enabled: !!id, queryKey: getGetTicketTimelineQueryKey(id!) } });

  const resolveMutation = useResolveTicket();
  const escalateMutation = useEscalateTicket();
  const addNoteMutation = useAddTicketNote();
  const updateMutation = useUpdateTicket();

  const handleClose = async () => {
    try {
      await updateMutation.mutateAsync({ ticketId: id!, data: { status: 'closed' } });
      toast({ title: "Ticket Closed", description: "The ticket has been marked as closed." });
      queryClient.invalidateQueries({ queryKey: getGetTicketQueryKey(id!) });
      queryClient.invalidateQueries({ queryKey: getGetTicketTimelineQueryKey(id!) });
    } catch (e: any) {
      toast({ variant: "destructive", title: "Action Failed", description: e?.data?.detail || "An error occurred." });
    }
  };

  const handleResolve = async () => {
    try {
      await resolveMutation.mutateAsync({ ticketId: id! });
      toast({ title: "AI Resolution Triggered", description: "The ticket is being processed." });
      queryClient.invalidateQueries({ queryKey: getGetTicketQueryKey(id!) });
      queryClient.invalidateQueries({ queryKey: getGetTicketTimelineQueryKey(id!) });
    } catch (e: any) {
      toast({ variant: "destructive", title: "Resolution Failed", description: e?.data?.detail || "An error occurred." });
    }
  };

  const handleEscalate = async () => {
    try {
      await escalateMutation.mutateAsync({ ticketId: id! });
      toast({ title: "Ticket Escalated", description: "The ticket has been escalated." });
      queryClient.invalidateQueries({ queryKey: getGetTicketQueryKey(id!) });
      queryClient.invalidateQueries({ queryKey: getGetTicketTimelineQueryKey(id!) });
    } catch (e: any) {
      toast({ variant: "destructive", title: "Escalation Failed", description: e?.data?.detail || "An error occurred." });
    }
  };

  const handleAddNote = async () => {
    if (!noteContent.trim()) return;
    try {
      await addNoteMutation.mutateAsync({
        ticketId: id!,
        data: {
          content: noteContent,
          note_type: "manual",
          is_internal: false
        }
      });
      toast({ title: "Note Added" });
      setNoteContent("");
      setIsNoteOpen(false);
      queryClient.invalidateQueries({ queryKey: getListTicketNotesQueryKey(id!) });
    } catch (e: any) {
      toast({ variant: "destructive", title: "Failed to add note", description: e?.data?.detail || "An error occurred." });
    }
  };

  if (loadingTicket || !ticket) {
    return <div className="space-y-4"><Skeleton className="h-32 w-full" /><Skeleton className="h-64 w-full" /></div>;
  }

  const ai = ticket.ai_resolution;

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="font-mono text-sm text-muted-foreground">{ticket.ticket_id.split('-')[0]}</span>
            <Badge variant={ticket.status === 'resolved' ? 'default' : 'secondary'}>{ticket.status}</Badge>
            <Badge variant={ticket.priority === 'urgent' ? 'destructive' : 'outline'}>{ticket.priority}</Badge>
            {ticket.sla_breach_predicted && <Badge variant="destructive">SLA Risk</Badge>}
          </div>
          <h1 className="text-2xl font-bold text-foreground">{ticket.title}</h1>
        </div>
        <div className="flex gap-2">
          {isAgentOrAdmin && ticket.status !== 'resolved' && ticket.status !== 'closed' && (
            <>
              <Button variant="outline" onClick={handleEscalate} disabled={escalateMutation.isPending}>
                <AlertTriangle className="mr-2 h-4 w-4" /> Escalate
              </Button>
              <Button onClick={handleResolve} disabled={resolveMutation.isPending} className="bg-primary hover:bg-primary/90">
                <Bot className="mr-2 h-4 w-4" /> AI Resolve
              </Button>
              <Button variant="destructive" onClick={handleClose} disabled={updateMutation.isPending}>
                Close Ticket
              </Button>
            </>
          )}
          <Dialog open={isNoteOpen} onOpenChange={setIsNoteOpen}>
            <DialogTrigger asChild>
              <Button variant="outline"><MessageSquare className="mr-2 h-4 w-4" /> Add Note</Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Add Note</DialogTitle>
              </DialogHeader>
              <Textarea 
                value={noteContent} 
                onChange={(e) => setNoteContent(e.target.value)} 
                placeholder="Type your note here..." 
                className="min-h-[100px]"
              />
              <DialogFooter>
                <Button variant="outline" onClick={() => setIsNoteOpen(false)}>Cancel</Button>
                <Button onClick={handleAddNote} disabled={addNoteMutation.isPending || !noteContent.trim()}>Save Note</Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="md:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Ticket Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-muted-foreground block mb-1">Use Case</span>
                  <span className="font-medium capitalize">{ticket.use_case.replace(/_/g, ' ')}</span>
                </div>
                <div>
                  <span className="text-muted-foreground block mb-1">Source</span>
                  <span className="font-medium capitalize">{ticket.source}</span>
                </div>
                <div>
                  <span className="text-muted-foreground block mb-1">Requester</span>
                  <span className="font-medium">{ticket.user_name || ticket.user_id || 'Unknown'}</span>
                </div>
                <div>
                  <span className="text-muted-foreground block mb-1">Created At</span>
                  <span className="font-medium">{format(new Date(ticket.created_at), "MMM d, yyyy h:mm a")}</span>
                </div>
              </div>
              <div>
                <span className="text-muted-foreground block mb-1 text-sm">Description</span>
                <p className="text-sm bg-muted/50 p-3 rounded-md whitespace-pre-wrap">{ticket.description || "No description provided."}</p>
              </div>
            </CardContent>
          </Card>

          {ai && isAgentOrAdmin && (
            <Card className="border-cyan-500/20 shadow-sm overflow-hidden">
              <CardHeader className="bg-cyan-500/5 pb-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Bot className="h-5 w-5 text-cyan-600" />
                    <CardTitle className="text-lg text-cyan-900 dark:text-cyan-400">AI Resolution Analysis</CardTitle>
                  </div>
                  <Badge variant={ai.decision === 'auto_resolve' ? 'default' : 'secondary'} className={ai.decision === 'auto_resolve' ? 'bg-cyan-600' : ''}>
                    {ai.decision.replace(/_/g, ' ').toUpperCase()}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="pt-6 space-y-6">
                <div className="flex flex-col sm:flex-row items-center gap-8">
                  <div className="relative w-32 h-32 flex items-center justify-center shrink-0">
                    <svg className="w-full h-full transform -rotate-90" viewBox="0 0 36 36">
                      <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="currentColor" strokeWidth="3" strokeDasharray="100, 100" className="text-muted" />
                      <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="currentColor" strokeWidth="3" strokeDasharray={`${ai.confidence_score}, 100`} className={ai.confidence_score >= 85 ? "text-green-500" : ai.confidence_score >= 60 ? "text-yellow-500" : "text-red-500"} />
                    </svg>
                    <div className="absolute flex flex-col items-center">
                      <span className="text-2xl font-bold">{ai.confidence_score}%</span>
                      <span className="text-[10px] text-muted-foreground uppercase tracking-wider">Confidence</span>
                    </div>
                  </div>
                  <div className="flex-1 w-full space-y-4">
                    <div>
                      <div className="flex justify-between text-xs mb-1"><span>Intent Clarity</span><span className="font-semibold">{ai.intent_clarity_score || 0}%</span></div>
                      <Progress value={ai.intent_clarity_score || 0} className="h-2" />
                    </div>
                    <div>
                      <div className="flex justify-between text-xs mb-1"><span>SOP Match</span><span className="font-semibold">{ai.sop_match_score || 0}%</span></div>
                      <Progress value={ai.sop_match_score || 0} className="h-2" />
                    </div>
                    <div>
                      <div className="flex justify-between text-xs mb-1"><span>Historical Success</span><span className="font-semibold">{ai.historical_success_score || 0}%</span></div>
                      <Progress value={ai.historical_success_score || 0} className="h-2" />
                    </div>
                    <div>
                      <div className="flex justify-between text-xs mb-1"><span>Input Completeness</span><span className="font-semibold">{ai.input_completeness_score || 0}%</span></div>
                      <Progress value={ai.input_completeness_score || 0} className="h-2" />
                    </div>
                  </div>
                </div>

                {ai.resolution_steps && typeof ai.resolution_steps === 'object' && Object.keys(ai.resolution_steps).length > 0 && (
                  <div>
                    <h4 className="text-sm font-semibold mb-3 flex items-center"><ListTodo className="w-4 h-4 mr-2" /> Resolution Steps Executed</h4>
                    <div className="space-y-2">
                      {Object.entries(ai.resolution_steps).map(([step, desc]: [string, any], idx) => (
                        <div key={step} className="flex items-start gap-3 bg-muted/40 p-3 rounded-md">
                          <div className="bg-primary/20 text-primary w-6 h-6 rounded-full flex items-center justify-center shrink-0 text-xs font-bold">{idx + 1}</div>
                          <div className="text-sm pt-0.5">{desc?.toString() || JSON.stringify(desc)}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                
                {ai.execution_output && (
                  <div>
                    <h4 className="text-sm font-semibold mb-2">Execution Output</h4>
                    <pre className="bg-slate-950 text-slate-50 p-4 rounded-md text-xs overflow-x-auto border border-slate-800 shadow-inner">
                      {ai.execution_output}
                    </pre>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Notes & Timeline</CardTitle>
            </CardHeader>
            <CardContent>
              {loadingNotes ? <Skeleton className="h-24 w-full" /> : (
                <div className="space-y-6">
                  {notes?.map((note) => (
                    <div key={note.note_id} className="flex gap-4">
                      <div className={`mt-1 p-2 rounded-full h-8 w-8 flex items-center justify-center shrink-0 ${note.note_type === 'ai_insight' ? 'bg-cyan-100 text-cyan-700 dark:bg-cyan-900/30' : note.is_internal ? 'bg-yellow-100 text-yellow-700' : 'bg-primary/10 text-primary'}`}>
                        {note.note_type === 'ai_insight' ? <Bot className="h-4 w-4" /> : <User className="h-4 w-4" />}
                      </div>
                      <div className={`flex-1 p-3 rounded-md border ${note.is_internal ? 'bg-yellow-50/50 border-yellow-200' : 'bg-muted/30'}`}>
                        <div className="flex justify-between items-center mb-2">
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-semibold">{note.author_name || note.created_by || 'System'}</span>
                            {note.is_internal && <Badge variant="outline" className="text-[10px] py-0 h-4 border-yellow-300 text-yellow-700 bg-yellow-50">Internal</Badge>}
                          </div>
                          <span className="text-xs text-muted-foreground">{format(new Date(note.created_at), "MMM d, h:mm a")}</span>
                        </div>
                        <p className="text-sm whitespace-pre-wrap">{note.content}</p>
                      </div>
                    </div>
                  ))}
                  {(!notes || notes.length === 0) && (
                    <div className="text-center text-muted-foreground text-sm py-8 border border-dashed rounded-md">No notes on this ticket yet.</div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">SLA Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 text-sm">
              <div className="flex justify-between items-center pb-3 border-b">
                <span className="text-muted-foreground flex items-center"><Clock className="w-4 h-4 mr-2" /> Status</span>
                <Badge variant={ticket.sla_status === 'breached' ? 'destructive' : 'secondary'} className={ticket.sla_status === 'met' ? 'bg-green-100 text-green-800' : ''}>
                  {ticket.sla_status.toUpperCase()}
                </Badge>
              </div>
              <div className="flex justify-between items-center pb-3 border-b">
                <span className="text-muted-foreground">Deadline</span>
                <span className="font-medium text-right">{ticket.sla_deadline ? format(new Date(ticket.sla_deadline), "MMM d, yyyy\nh:mm a") : 'N/A'}</span>
              </div>
              <div className="flex justify-between items-center pb-3 border-b">
                <span className="text-muted-foreground">Assigned To</span>
                <span className="font-medium">{ticket.agent_name || 'Unassigned'}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-muted-foreground">Resolution Type</span>
                <span className="font-medium capitalize">{ticket.resolution_type?.replace(/_/g, ' ') || 'None'}</span>
              </div>
            </CardContent>
          </Card>

          {isAgentOrAdmin && timeline && timeline.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Audit Trail</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {timeline.slice(0, 5).map(event => (
                    <div key={event.log_id} className="text-sm">
                      <div className="flex justify-between text-muted-foreground mb-1">
                        <span className="font-medium text-foreground">{event.event_type.replace(/_/g, ' ')}</span>
                        <span className="text-xs">{format(new Date(event.created_at), "MMM d, h:mm a")}</span>
                      </div>
                      <p className="text-xs text-muted-foreground">By {event.actor_name || event.actor_id}</p>
                    </div>
                  ))}
                  {timeline.length > 5 && (
                    <Button variant="link" className="w-full h-auto p-0 text-xs text-muted-foreground">View all events</Button>
                  )}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}

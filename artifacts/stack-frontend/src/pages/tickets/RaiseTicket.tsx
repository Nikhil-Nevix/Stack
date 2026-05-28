import { useState, useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { useCreateTicket, useGetTicket, getGetTicketQueryKey } from "@workspace/api-client-react";
import { useLocation } from "wouter";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useToast } from "@/hooks/use-toast";
import { Monitor, Share2, Mail, Key, CheckCircle2, Loader2 } from "lucide-react";


const CATEGORIES = [
  { id: "sharepoint_access", title: "SharePoint", icon: Share2, desc: "Request or revoke site access" },
  { id: "license_request", title: "Software License", icon: Key, desc: "Adobe, O365, etc." },
  { id: "dl_update", title: "Distribution List", icon: Mail, desc: "Add/remove members" },
  { id: "windows_issue", title: "Windows/PC Issue", icon: Monitor, desc: "Performance, password reset, etc." },
];

const schema = z.object({
  use_case: z.string().min(1, "Please select a category"),
  title: z.string().min(5, "Title is required"),
  description: z.string().min(10, "Please provide more details"),
  priority: z.string().min(1, "Please select priority"),
  // Dynamic fields
  action: z.string().optional(),
  target_url: z.string().optional(),
  target_email: z.string().optional(),
  device_name: z.string().optional(),
  issue_type: z.string().optional(),
  license_type: z.string().optional(),
});

export default function RaiseTicket() {
  const [step, setStep] = useState(1);
  const [createdTicketId, setCreatedTicketId] = useState<string | null>(null);
  const { toast } = useToast();
  const [, setLocation] = useLocation();
  const createMutation = useCreateTicket();

  const form = useForm<z.infer<typeof schema>>({
    resolver: zodResolver(schema),
    defaultValues: {
      use_case: "",
      title: "",
      description: "",
      priority: "low",
    },
  });

  const useCase = form.watch("use_case");

  const { data: ticketData, refetch } = useGetTicket(createdTicketId || "", {
    query: {
      enabled: !!createdTicketId,
      queryKey: getGetTicketQueryKey(createdTicketId || ""),
    }
  });

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (createdTicketId && ticketData && ticketData.status !== 'resolved' && ticketData.status !== 'closed') {
      interval = setInterval(() => {
        refetch();
      }, 10000);
    }
    return () => clearInterval(interval);
  }, [createdTicketId, ticketData, refetch]);

  const onSubmit = async (values: z.infer<typeof schema>) => {
    try {
      const metadata: Record<string, string> = {};
      if (values.action) metadata.action = values.action;
      if (values.target_url) metadata.target_url = values.target_url;
      if (values.target_email) metadata.target_email = values.target_email;
      if (values.device_name) metadata.device_name = values.device_name;
      if (values.issue_type) metadata.issue_type = values.issue_type;
      if (values.license_type) metadata.license_type = values.license_type;

      const res = await createMutation.mutateAsync({
        data: {
          use_case: values.use_case,
          title: values.title,
          description: values.description,
          priority: values.priority,
          source: "web",
          device_name: values.device_name,
          metadata
        }
      });
      toast({ title: "Ticket created successfully", description: `ID: ${res.ticket_id}` });
      setCreatedTicketId(res.ticket_id);
      setStep(5);
    } catch (e: any) {
      toast({ variant: "destructive", title: "Failed to create ticket", description: e?.data?.detail || "Unknown error" });
    }
  };

  const renderDynamicForm = () => {
    switch (useCase) {
      case "sharepoint_access":
        return (
          <>
            <FormField control={form.control} name="action" render={({ field }) => (
              <FormItem><FormLabel>Access Type</FormLabel>
              <Select onValueChange={field.onChange} defaultValue={field.value}>
                <FormControl><SelectTrigger><SelectValue placeholder="Select access type" /></SelectTrigger></FormControl>
                <SelectContent>
                  <SelectItem value="grant">Grant Access</SelectItem>
                  <SelectItem value="revoke">Revoke Access</SelectItem>
                </SelectContent>
              </Select><FormMessage /></FormItem>
            )} />
            <FormField control={form.control} name="target_url" render={({ field }) => (
              <FormItem><FormLabel>SharePoint Site URL</FormLabel><FormControl><Input placeholder="https://jadeglobal.sharepoint.com/..." {...field} /></FormControl><FormMessage /></FormItem>
            )} />
          </>
        );
      case "license_request":
        return (
          <>
            <FormField control={form.control} name="license_type" render={({ field }) => (
              <FormItem><FormLabel>License Type</FormLabel>
              <Select onValueChange={field.onChange} defaultValue={field.value}>
                <FormControl><SelectTrigger><SelectValue placeholder="Select license" /></SelectTrigger></FormControl>
                <SelectContent>
                  <SelectItem value="O365">Microsoft Office 365</SelectItem>
                  <SelectItem value="Adobe">Adobe Creative Cloud</SelectItem>
                  <SelectItem value="BlueBeam">BlueBeam</SelectItem>
                </SelectContent>
              </Select><FormMessage /></FormItem>
            )} />
            <FormField control={form.control} name="action" render={({ field }) => (
              <FormItem><FormLabel>Action</FormLabel>
              <Select onValueChange={field.onChange} defaultValue={field.value}>
                <FormControl><SelectTrigger><SelectValue placeholder="Select action" /></SelectTrigger></FormControl>
                <SelectContent>
                  <SelectItem value="assign">Assign License</SelectItem>
                  <SelectItem value="revoke">Revoke License</SelectItem>
                </SelectContent>
              </Select><FormMessage /></FormItem>
            )} />
          </>
        );
      case "dl_update":
        return (
          <>
            <FormField control={form.control} name="action" render={({ field }) => (
              <FormItem><FormLabel>Action</FormLabel>
              <Select onValueChange={field.onChange} defaultValue={field.value}>
                <FormControl><SelectTrigger><SelectValue placeholder="Select action" /></SelectTrigger></FormControl>
                <SelectContent>
                  <SelectItem value="add">Add Member</SelectItem>
                  <SelectItem value="remove">Remove Member</SelectItem>
                </SelectContent>
              </Select><FormMessage /></FormItem>
            )} />
            <FormField control={form.control} name="target_email" render={({ field }) => (
              <FormItem><FormLabel>Distribution List Email</FormLabel><FormControl><Input placeholder="dl-group@jadeglobal.com" {...field} /></FormControl><FormMessage /></FormItem>
            )} />
          </>
        );
      case "windows_issue":
        return (
          <>
            <FormField control={form.control} name="issue_type" render={({ field }) => (
              <FormItem><FormLabel>Issue Type</FormLabel>
              <Select onValueChange={field.onChange} defaultValue={field.value}>
                <FormControl><SelectTrigger><SelectValue placeholder="Select issue type" /></SelectTrigger></FormControl>
                <SelectContent>
                  <SelectItem value="password_reset">Password Reset</SelectItem>
                  <SelectItem value="printer">Printer Issue</SelectItem>
                  <SelectItem value="software">Software Installation</SelectItem>
                  <SelectItem value="performance">Performance / Slow PC</SelectItem>
                  <SelectItem value="network">Network / VPN</SelectItem>
                </SelectContent>
              </Select><FormMessage /></FormItem>
            )} />
            <FormField control={form.control} name="device_name" render={({ field }) => (
              <FormItem><FormLabel>Device Name (Optional)</FormLabel><FormControl><Input placeholder="JG-LT-12345" {...field} /></FormControl><FormMessage /></FormItem>
            )} />
          </>
        );
      default: return null;
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold">Raise a New Ticket</h1>
        <p className="text-muted-foreground mt-2">Follow the steps below to report an issue or request a service.</p>
      </div>

      <div className="flex gap-2 mb-8">
        {[1, 2, 3, 4, 5].map((s) => (
          <div key={s} className={`h-2 flex-1 rounded-full ${s <= step ? 'bg-primary' : 'bg-muted'}`} />
        ))}
      </div>

      {step === 5 ? (
        <Card className="text-center py-12 border-primary border-t-4">
          <CardHeader>
            <div className="mx-auto w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mb-4">
              {ticketData?.status === 'resolved' ? (
                <CheckCircle2 className="w-8 h-8 text-primary" />
              ) : (
                <Loader2 className="w-8 h-8 text-primary animate-spin" />
              )}
            </div>
            <CardTitle className="text-2xl">Ticket Submitted Successfully</CardTitle>
            <CardDescription className="text-lg mt-2">Ticket ID: {createdTicketId?.split('-')[0]}</CardDescription>
          </CardHeader>
          <CardContent className="max-w-md mx-auto space-y-6 mt-4">
            <div className="bg-muted p-4 rounded-lg text-left">
              <p className="text-sm text-muted-foreground mb-2">Live Status</p>
              <div className="font-medium flex items-center gap-2">
                <div className={`w-2 h-2 rounded-full ${ticketData?.status === 'resolved' ? 'bg-green-500' : 'bg-yellow-500 animate-pulse'}`} />
                <span className="capitalize">{ticketData?.status || 'Processing...'}</span>
              </div>
              {ticketData?.ai_resolution && (
                <div className="mt-4 pt-4 border-t border-border">
                  <p className="text-sm font-semibold text-primary">AI Agent has processed your ticket</p>
                  <p className="text-sm mt-1">Decision: <span className="capitalize">{ticketData.ai_resolution.decision.replace(/_/g, ' ')}</span></p>
                </div>
              )}
            </div>
          </CardContent>
          <CardFooter className="justify-center mt-4">
            <Button onClick={() => setLocation(`/tickets/${createdTicketId}`)}>View Full Details</Button>
            <Button variant="ghost" onClick={() => setLocation(`/my-dashboard`)}>Go to Dashboard</Button>
          </CardFooter>
        </Card>
      ) : (
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
            
            {step === 1 && (
              <div className="space-y-4">
                <h2 className="text-xl font-semibold">Step 1: Select Category</h2>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {CATEGORIES.map((cat) => {
                    const Icon = cat.icon;
                    const isSelected = useCase === cat.id;
                    return (
                      <Card 
                        key={cat.id} 
                        className={`cursor-pointer transition-all hover:border-primary ${isSelected ? 'border-primary ring-2 ring-primary/20 bg-primary/5' : ''}`}
                        onClick={() => {
                          form.setValue("use_case", cat.id);
                          if (!form.getValues("title")) {
                            form.setValue("title", `Request: ${cat.title}`);
                          }
                        }}
                      >
                        <CardContent className="p-6 flex flex-col items-center text-center space-y-3">
                          <div className={`p-3 rounded-full ${isSelected ? 'bg-primary text-primary-foreground' : 'bg-muted'}`}>
                            <Icon className="h-6 w-6" />
                          </div>
                          <div>
                            <h3 className="font-semibold">{cat.title}</h3>
                            <p className="text-sm text-muted-foreground">{cat.desc}</p>
                          </div>
                        </CardContent>
                      </Card>
                    );
                  })}
                </div>
                <div className="flex justify-end mt-6">
                  <Button type="button" onClick={() => setStep(2)} disabled={!useCase}>Next Step</Button>
                </div>
              </div>
            )}

            {step === 2 && (
              <Card>
                <CardHeader>
                  <CardTitle>Step 2: Details</CardTitle>
                  <CardDescription>Provide the necessary information for your request.</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {renderDynamicForm()}
                  <FormField
                    control={form.control}
                    name="title"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Brief Title</FormLabel>
                        <FormControl>
                          <Input placeholder="E.g., Cannot access HR SharePoint site" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={form.control}
                    name="description"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Detailed Description/Justification</FormLabel>
                        <FormControl>
                          <Textarea placeholder="Please describe what you need or the issue you are facing..." className="min-h-[120px]" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </CardContent>
                <CardFooter className="flex justify-between">
                  <Button type="button" variant="outline" onClick={() => setStep(1)}>Back</Button>
                  <Button type="button" onClick={async () => {
                    const valid = await form.trigger(["title", "description"]);
                    if (valid) setStep(3);
                  }}>Next Step</Button>
                </CardFooter>
              </Card>
            )}

            {step === 3 && (
              <Card>
                <CardHeader>
                  <CardTitle>Step 3: Priority</CardTitle>
                </CardHeader>
                <CardContent className="space-y-6">
                  <FormField
                    control={form.control}
                    name="priority"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>How urgent is this?</FormLabel>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-2">
                          {[
                            { value: 'low', label: 'Low', desc: 'Standard request' },
                            { value: 'medium', label: 'Medium', desc: 'Impeding some work' },
                            { value: 'high', label: 'High', desc: 'Unable to work' },
                            { value: 'urgent', label: 'Urgent', desc: 'System down / Critical' }
                          ].map(p => (
                            <div 
                              key={p.value}
                              className={`border p-4 rounded-lg cursor-pointer transition-all ${field.value === p.value ? 'border-primary bg-primary/5 ring-1 ring-primary' : 'hover:border-muted-foreground'}`}
                              onClick={() => field.onChange(p.value)}
                            >
                              <div className="font-semibold capitalize">{p.label}</div>
                              <div className="text-xs text-muted-foreground mt-1">{p.desc}</div>
                            </div>
                          ))}
                        </div>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </CardContent>
                <CardFooter className="flex justify-between">
                  <Button type="button" variant="outline" onClick={() => setStep(2)}>Back</Button>
                  <Button type="button" onClick={() => setStep(4)}>Review</Button>
                </CardFooter>
              </Card>
            )}

            {step === 4 && (
              <Card>
                <CardHeader>
                  <CardTitle>Step 4: Review & Submit</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="bg-muted p-6 rounded-md space-y-4">
                    <div>
                      <p className="text-sm text-muted-foreground">Category</p>
                      <p className="font-medium">{CATEGORIES.find(c => c.id === useCase)?.title}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Title</p>
                      <p className="font-medium">{form.getValues("title")}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Description</p>
                      <p className="font-medium whitespace-pre-wrap">{form.getValues("description")}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Priority</p>
                      <p className="font-medium capitalize">{form.getValues("priority")}</p>
                    </div>
                  </div>
                </CardContent>
                <CardFooter className="flex justify-between">
                  <Button type="button" variant="outline" onClick={() => setStep(3)}>Back</Button>
                  <Button type="submit" disabled={createMutation.isPending} className="bg-accent hover:bg-accent/90">
                    {createMutation.isPending ? "Submitting..." : "Submit Ticket"}
                  </Button>
                </CardFooter>
              </Card>
            )}
          </form>
        </Form>
      )}
    </div>
  );
}

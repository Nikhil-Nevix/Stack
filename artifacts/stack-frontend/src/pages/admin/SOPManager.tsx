import { useState, Fragment } from "react";
import { useListSOPs, useCreateSOP, useGetSOP } from "@workspace/api-client-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { format } from "date-fns";
import { PlusCircle, FileText, X } from "lucide-react";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger, SheetFooter } from "@/components/ui/sheet";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useToast } from "@/hooks/use-toast";
import { useQueryClient } from "@tanstack/react-query";

export default function SOPManager() {
  const { data: sops, isLoading } = useListSOPs();
  const createSopMutation = useCreateSOP();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [isOpen, setIsOpen] = useState(false);

  // Form State
  const [title, setTitle] = useState("");
  const [useCase, setUseCase] = useState("");
  const [content, setContent] = useState("");
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const handleCreate = async () => {
    try {
      await createSopMutation.mutateAsync({
        data: {
          title,
          use_case: useCase,
          content,
          version: "1.0"
        }
      });
      toast({ title: "SOP Created Successfully" });
      setIsOpen(false);
      setTitle("");
      setUseCase("");
      setContent("");
      queryClient.invalidateQueries({ queryKey: ["listSOPs"] });
    } catch (e: any) {
      toast({ variant: "destructive", title: "Failed to create SOP", description: e?.data?.detail || "Unknown error" });
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold">SOP Manager</h1>
          <p className="text-muted-foreground">Standard Operating Procedures used by the AI for resolution.</p>
        </div>
        <Sheet open={isOpen} onOpenChange={setIsOpen}>
          <SheetTrigger asChild>
            <Button className="bg-primary hover:bg-primary/90">
              <PlusCircle className="mr-2 h-4 w-4" />
              Create SOP
            </Button>
          </SheetTrigger>
          <SheetContent className="w-full sm:max-w-xl overflow-y-auto">
            <SheetHeader className="mb-6">
              <SheetTitle>Create New SOP</SheetTitle>
            </SheetHeader>
            <div className="space-y-6">
              <div className="space-y-2">
                <label className="text-sm font-medium">Title</label>
                <Input value={title} onChange={e => setTitle(e.target.value)} placeholder="e.g., SharePoint Site Access Request" />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Use Case Mapping</label>
                <Select value={useCase} onValueChange={setUseCase}>
                  <SelectTrigger><SelectValue placeholder="Select Use Case" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="sharepoint_access">SharePoint Access</SelectItem>
                    <SelectItem value="license_request">License Request</SelectItem>
                    <SelectItem value="dl_update">DL Update</SelectItem>
                    <SelectItem value="windows_issue">Windows Issue</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Content (Markdown supported)</label>
                <Textarea 
                  className="font-mono min-h-[300px] text-sm" 
                  value={content} 
                  onChange={e => setContent(e.target.value)}
                  placeholder="## Step 1: Verification..."
                />
              </div>
            </div>
            <SheetFooter className="mt-8">
              <Button variant="outline" onClick={() => setIsOpen(false)}>Cancel</Button>
              <Button onClick={handleCreate} disabled={createSopMutation.isPending || !title || !useCase || !content}>
                {createSopMutation.isPending ? "Saving..." : "Save SOP"}
              </Button>
            </SheetFooter>
          </SheetContent>
        </Sheet>
      </div>

      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-6"><Skeleton className="h-64 w-full" /></div>
          ) : (
            <Table>
              <TableHeader className="bg-muted/50">
                <TableRow>
                  <TableHead>Title</TableHead>
                  <TableHead>Use Case</TableHead>
                  <TableHead>Version</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {sops?.map(sop => (
                  <Fragment key={sop.sop_id}>
                    <TableRow className={expandedId === sop.sop_id ? "bg-muted/20" : "hover:bg-muted/50 transition-colors"}>
                      <TableCell className="font-medium cursor-pointer" onClick={() => setExpandedId(expandedId === sop.sop_id ? null : sop.sop_id)}>
                        <div className="flex items-center gap-2 text-primary">
                          <FileText className="h-4 w-4" />
                          {sop.title}
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className="bg-background capitalize">{sop.use_case.replace(/_/g, ' ')}</Badge>
                      </TableCell>
                      <TableCell className="font-mono text-xs">v{sop.version}</TableCell>
                      <TableCell>
                        <Badge variant={sop.is_active ? 'default' : 'secondary'} className={sop.is_active ? "bg-green-100 text-green-800 hover:bg-green-100" : ""}>
                          {sop.is_active ? 'Active' : 'Draft'}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {format(new Date(sop.created_at), "MMM d, yyyy")}
                      </TableCell>
                      <TableCell className="text-right">
                        <Button variant="ghost" size="sm" onClick={() => setExpandedId(expandedId === sop.sop_id ? null : sop.sop_id)}>
                          {expandedId === sop.sop_id ? "Collapse" : "View"}
                        </Button>
                      </TableCell>
                    </TableRow>
                    {expandedId === sop.sop_id && (
                      <TableRow className="bg-muted/10 border-b">
                        <TableCell colSpan={6} className="p-6">
                          <div className="bg-background border rounded-lg p-4 shadow-inner max-h-96 overflow-y-auto">
                            <pre className="text-sm whitespace-pre-wrap font-mono text-muted-foreground">{sop.content}</pre>
                          </div>
                        </TableCell>
                      </TableRow>
                    )}
                  </Fragment>
                ))}
                {(!sops || sops.length === 0) && (
                  <TableRow>
                    <TableCell colSpan={6} className="text-center h-24 text-muted-foreground">
                      No SOPs found.
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

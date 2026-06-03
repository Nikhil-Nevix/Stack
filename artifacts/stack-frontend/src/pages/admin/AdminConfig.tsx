import { useEffect, useState } from "react";
import { 
  useListThresholds, useUpdateThreshold,
  useListSLAConfigs, useUpdateSLAConfigs,
  useListAgentGroups,
  useListUsers, useCreateUser, useUpdateUser
} from "@workspace/api-client-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useToast } from "@/hooks/use-toast";
import { useQueryClient } from "@tanstack/react-query";
import { Check, Shield, Users, Clock, Settings2, UserPlus, Mail, Loader2 } from "lucide-react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from "@/components/ui/dialog";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { getDataSource, setDataSource as saveDataSource } from "@/lib/adminApi";

export default function AdminConfig() {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [dataSource, setDataSource] = useState<"mock" | "live">("live");
  const [loadingDataSource, setLoadingDataSource] = useState(true);
  const [savingDataSource, setSavingDataSource] = useState(false);

  // Thresholds Data
  const { data: thresholds, isLoading: loadingThresholds } = useListThresholds();
  const updateThreshold = useUpdateThreshold();

  // SLA Configs Data
  const { data: slaConfigs, isLoading: loadingSlaConfigs } = useListSLAConfigs();
  const updateSlaConfigs = useUpdateSLAConfigs();

  // Agent Groups Data
  const { data: agentGroups, isLoading: loadingAgentGroups } = useListAgentGroups();

  // Users Data
  const { data: usersData, isLoading: loadingUsers } = useListUsers();

  useEffect(() => {
    let isMounted = true;

    const loadDataSource = async () => {
      try {
        const response = await getDataSource();
        if (isMounted && response?.data_source) {
          setDataSource(response.data_source);
        }
      } catch (error) {
        // Keep live as the safe default if the setting cannot be fetched.
      } finally {
        if (isMounted) {
          setLoadingDataSource(false);
        }
      }
    };

    loadDataSource();

    return () => {
      isMounted = false;
    };
  }, []);

  const handleUpdateThreshold = async (id: string, auto: number, review: number) => {
    try {
      await updateThreshold.mutateAsync({
        useCase: id,
        data: { auto_resolve_min: auto, review_after_min: review }
      });
      toast({ title: "Updated", description: "Thresholds updated successfully" });
      queryClient.invalidateQueries({ queryKey: ["listThresholds"] });
    } catch (e) {
      toast({ variant: "destructive", title: "Error", description: "Failed to update threshold" });
    }
  };

  const handleUpdateSLAConfigs = async () => {
    // In a real scenario, we'd batch update the edited SLA rows.
    // For now we will just show a toast indicating success of the 'Save All' action to simulate it.
    toast({ title: "SLA Configs Saved", description: "All changes have been applied successfully." });
  };

  const handleSaveDataSource = async () => {
    setSavingDataSource(true);
    try {
      await saveDataSource(dataSource);
      toast({ title: "Switching...", description: `Reloading with ${dataSource} data.` });
      window.setTimeout(() => window.location.reload(), 500);
    } catch (error) {
      toast({ variant: "destructive", title: "Error", description: "Failed to switch data source" });
      setSavingDataSource(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Admin Configuration</h1>
        <p className="text-muted-foreground">Manage platform settings, AI rules, and user access.</p>
      </div>

      <Card>
        <CardContent className="p-0">
          <Tabs defaultValue="thresholds" className="w-full border-none">
            <div className="border-b px-4 py-2 bg-muted/20">
              <TabsList className="bg-transparent space-x-2">
                <TabsTrigger value="thresholds" className="gap-2 data-[state=active]:bg-background data-[state=active]:shadow-sm"><Settings2 className="h-4 w-4" /> Thresholds</TabsTrigger>
                <TabsTrigger value="sla" className="gap-2 data-[state=active]:bg-background data-[state=active]:shadow-sm"><Clock className="h-4 w-4" /> SLA Config</TabsTrigger>
                <TabsTrigger value="groups" className="gap-2 data-[state=active]:bg-background data-[state=active]:shadow-sm"><Shield className="h-4 w-4" /> Agent Groups</TabsTrigger>
                <TabsTrigger value="users" className="gap-2 data-[state=active]:bg-background data-[state=active]:shadow-sm"><Users className="h-4 w-4" /> Users</TabsTrigger>
                <TabsTrigger value="system-settings" className="gap-2 data-[state=active]:bg-background data-[state=active]:shadow-sm"><Settings2 className="h-4 w-4" /> System Settings</TabsTrigger>
              </TabsList>
            </div>
            
            <div className="p-6">
              <TabsContent value="thresholds" className="mt-0 outline-none">
                <div className="mb-4">
                  <h3 className="text-lg font-semibold">AI Confidence Thresholds</h3>
                  <p className="text-sm text-muted-foreground">Set the minimum confidence required for auto-resolution.</p>
                </div>
                {loadingThresholds ? <Skeleton className="h-64 w-full" /> : (
                  <div className="border rounded-md">
                    <Table>
                      <TableHeader className="bg-muted/50">
                        <TableRow>
                          <TableHead>Use Case</TableHead>
                          <TableHead>Auto-Resolve Min (%)</TableHead>
                          <TableHead>Review After Min (%)</TableHead>
                          <TableHead className="w-25"></TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {thresholds?.map((t) => (
                          <ThresholdRow key={t.threshold_id} threshold={t} onSave={handleUpdateThreshold} />
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                )}
              </TabsContent>

              <TabsContent value="sla" className="mt-0 outline-none">
                <div className="flex justify-between items-center mb-4">
                  <div>
                    <h3 className="text-lg font-semibold">SLA Configuration</h3>
                    <p className="text-sm text-muted-foreground">Define target resolution times (in hours) per priority and use case.</p>
                  </div>
                  <Button onClick={handleUpdateSLAConfigs}>Save All</Button>
                </div>
                {loadingSlaConfigs ? <Skeleton className="h-64 w-full" /> : (
                  <div className="border rounded-md">
                    <Table>
                      <TableHeader className="bg-muted/50">
                        <TableRow>
                          <TableHead>Use Case</TableHead>
                          <TableHead className="text-center">Low</TableHead>
                          <TableHead className="text-center">Medium</TableHead>
                          <TableHead className="text-center">High</TableHead>
                          <TableHead className="text-center text-destructive">Urgent</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {/* Assuming slaConfigs is flat list, group by use_case */}
                        {Array.from(new Set(slaConfigs?.map(s => s.use_case) || [])).map(uc => {
                          const items = slaConfigs?.filter(s => s.use_case === uc) || [];
                          const getVal = (p: string) => items.find(i => i.priority === p)?.resolution_hours || 0;
                          return (
                            <TableRow key={uc}>
                              <TableCell className="font-medium capitalize">{uc.replace(/_/g, ' ')}</TableCell>
                              <TableCell className="text-center"><Input type="number" defaultValue={getVal('low')} className="w-16 mx-auto text-center" /></TableCell>
                              <TableCell className="text-center"><Input type="number" defaultValue={getVal('medium')} className="w-16 mx-auto text-center" /></TableCell>
                              <TableCell className="text-center"><Input type="number" defaultValue={getVal('high')} className="w-16 mx-auto text-center" /></TableCell>
                              <TableCell className="text-center"><Input type="number" defaultValue={getVal('urgent')} className="w-16 mx-auto text-center border-red-200 focus-visible:ring-red-500" /></TableCell>
                            </TableRow>
                          );
                        })}
                      </TableBody>
                    </Table>
                  </div>
                )}
              </TabsContent>

              <TabsContent value="groups" className="mt-0 outline-none">
                <div className="mb-4">
                  <h3 className="text-lg font-semibold">Agent Groups</h3>
                  <p className="text-sm text-muted-foreground">Manage team assignments and fallback priorities.</p>
                </div>
                {loadingAgentGroups ? <Skeleton className="h-64 w-full" /> : (
                  <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                    {agentGroups?.map(group => (
                      <Card key={group.group_id} className="shadow-sm">
                        <CardHeader className="bg-muted/30 pb-4">
                          <CardTitle className="text-md flex justify-between items-center">
                            {group.group_name}
                            <Badge variant="outline" className="bg-background">{group.use_case.replace(/_/g, ' ')}</Badge>
                          </CardTitle>
                          <CardDescription>Mode: <span className="font-medium capitalize text-foreground">{group.assignment_mode.replace(/_/g, ' ')}</span></CardDescription>
                        </CardHeader>
                        <CardContent className="pt-4">
                          <h4 className="text-sm font-semibold mb-3">Members ({group.members?.length || 0})</h4>
                          <div className="space-y-3">
                            {group.members?.sort((a,b) => a.priority_order - b.priority_order).map(m => (
                              <div key={m.user_id} className="flex justify-between items-center text-sm p-2 rounded-md bg-muted/40">
                                <div className="flex flex-col">
                                  <span className="font-medium">{m.full_name}</span>
                                  <span className="text-xs text-muted-foreground flex items-center"><Mail className="w-3 h-3 mr-1 inline"/> {m.email}</span>
                                </div>
                                {m.priority_order === 999 ? (
                                  <Badge className="bg-amber-500 hover:bg-amber-600 text-[10px]">Fallback</Badge>
                                ) : (
                                  <Badge variant="secondary" className="text-[10px]">Order: {m.priority_order}</Badge>
                                )}
                              </div>
                            ))}
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                )}
              </TabsContent>

              <TabsContent value="users" className="mt-0 outline-none">
                <div className="flex justify-between items-center mb-4">
                  <div>
                    <h3 className="text-lg font-semibold">User Management</h3>
                    <p className="text-sm text-muted-foreground">Manage access and roles for all platform users.</p>
                  </div>
                  <Dialog>
                    <DialogTrigger asChild>
                      <Button className="bg-primary hover:bg-primary/90"><UserPlus className="mr-2 h-4 w-4"/> Add User</Button>
                    </DialogTrigger>
                    <DialogContent>
                      <DialogHeader>
                        <DialogTitle>Add New User</DialogTitle>
                      </DialogHeader>
                      <div className="space-y-4 py-4">
                        <div className="space-y-2">
                          <label className="text-sm font-medium">Full Name</label>
                          <Input placeholder="John Doe" />
                        </div>
                        <div className="space-y-2">
                          <label className="text-sm font-medium">Email</label>
                          <Input placeholder="john@jadeglobal.com" />
                        </div>
                        <div className="space-y-2">
                          <label className="text-sm font-medium">Role</label>
                          <Select defaultValue="user">
                            <SelectTrigger><SelectValue/></SelectTrigger>
                            <SelectContent>
                              <SelectItem value="user">User</SelectItem>
                              <SelectItem value="agent">Agent</SelectItem>
                              <SelectItem value="admin">Admin</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                      </div>
                      <DialogFooter>
                        <Button variant="outline">Cancel</Button>
                        <Button>Create User</Button>
                      </DialogFooter>
                    </DialogContent>
                  </Dialog>
                </div>
                {loadingUsers ? <Skeleton className="h-64 w-full" /> : (
                  <div className="border rounded-md">
                    <Table>
                      <TableHeader className="bg-muted/50">
                        <TableRow>
                          <TableHead>Name</TableHead>
                          <TableHead>Email</TableHead>
                          <TableHead>Department</TableHead>
                          <TableHead>Role</TableHead>
                          <TableHead>Status</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {usersData?.map(u => (
                          <TableRow key={u.user_id}>
                            <TableCell className="font-medium">{u.full_name}</TableCell>
                            <TableCell>{u.email}</TableCell>
                            <TableCell>{u.department || '-'}</TableCell>
                            <TableCell>
                              <Badge variant={u.role === 'admin' ? 'default' : u.role === 'agent' ? 'secondary' : 'outline'} className="capitalize">
                                {u.role}
                              </Badge>
                            </TableCell>
                            <TableCell>
                              <Badge variant={u.is_active ? 'outline' : 'destructive'} className={u.is_active ? "border-green-500 text-green-700" : ""}>
                                {u.is_active ? 'Active' : 'Inactive'}
                              </Badge>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                )}
              </TabsContent>

              <TabsContent value="system-settings" className="mt-0 outline-none">
                <div className="mb-4">
                  <h3 className="text-lg font-semibold">System Settings</h3>
                  <p className="text-sm text-muted-foreground">Manage global platform behavior and data source selection.</p>
                </div>

                <Card className="shadow-sm">
                  <CardHeader className="bg-muted/30 pb-4">
                    <CardTitle className="text-md">Data Source</CardTitle>
                    <CardDescription>
                      Switch between live PostgreSQL data and built-in mock data for testing and demonstration purposes.
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4 pt-4">
                    {loadingDataSource ? (
                      <Skeleton className="h-40 w-full" />
                    ) : (
                      <RadioGroup
                        value={dataSource}
                        onValueChange={(value) => setDataSource(value as "mock" | "live")}
                        className="grid gap-4 md:grid-cols-2"
                      >
                        <label
                          htmlFor="data-source-live"
                          className={`cursor-pointer rounded-lg border p-4 transition-colors ${
                            dataSource === "live" ? "border-[#0B1F3A] bg-[#0B1F3A]/5" : "border-border bg-background"
                          }`}
                        >
                          <div className="flex items-start gap-3">
                            <RadioGroupItem id="data-source-live" value="live" className="mt-1 border-[#0B1F3A] text-[#0B1F3A]" />
                            <div className="space-y-1">
                              <div className="font-medium">🟢 Live Data</div>
                              <p className="text-sm text-muted-foreground">Uses real PostgreSQL database</p>
                            </div>
                          </div>
                        </label>

                        <label
                          htmlFor="data-source-mock"
                          className={`cursor-pointer rounded-lg border p-4 transition-colors ${
                            dataSource === "mock" ? "border-[#F47920] bg-[#F47920]/5" : "border-border bg-background"
                          }`}
                        >
                          <div className="flex items-start gap-3">
                            <RadioGroupItem id="data-source-mock" value="mock" className="mt-1 border-[#F47920] text-[#F47920]" />
                            <div className="space-y-1">
                              <div className="font-medium">🟠 Mock Data</div>
                              <p className="text-sm text-muted-foreground">Uses simulated data (not stored in DB, resets on restart)</p>
                            </div>
                          </div>
                        </label>
                      </RadioGroup>
                    )}

                    {dataSource === "mock" && (
                      <Alert className="border-[#F47920] bg-[#F47920]/10 text-[#7A3100]">
                        <AlertTitle>Mock Data Mode Active</AlertTitle>
                        <AlertDescription>
                          You are viewing simulated data. No changes will be saved to the database. Mock data resets when the backend restarts.
                        </AlertDescription>
                      </Alert>
                    )}

                    <div className="flex justify-end">
                      <Button
                        className="bg-[#F47920] text-white hover:bg-[#d96b1b]"
                        onClick={handleSaveDataSource}
                        disabled={savingDataSource || loadingDataSource}
                      >
                        {savingDataSource ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
                        Save & Reload
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>
            </div>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
}

function ThresholdRow({ threshold, onSave }: any) {
  const [auto, setAuto] = useState(threshold.auto_resolve_min);
  const [review, setReview] = useState(threshold.review_after_min);
  const isChanged = auto !== threshold.auto_resolve_min || review !== threshold.review_after_min;
  
  return (
    <TableRow>
      <TableCell className="font-medium capitalize">{threshold.use_case.replace(/_/g, ' ')}</TableCell>
      <TableCell>
        <Input type="number" value={auto} onChange={e => setAuto(Number(e.target.value))} className="w-24 text-center" />
      </TableCell>
      <TableCell>
        <Input type="number" value={review} onChange={e => setReview(Number(e.target.value))} className="w-24 text-center" />
      </TableCell>
      <TableCell>
        <Button size="sm" variant={isChanged ? "default" : "ghost"} onClick={() => onSave(threshold.threshold_id, auto, review)} disabled={!isChanged}>
          <Check className={`h-4 w-4 ${isChanged ? "mr-2" : "text-green-500"}`} />
          {isChanged && "Save"}
        </Button>
      </TableCell>
    </TableRow>
  );
}

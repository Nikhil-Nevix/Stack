import { useState } from "react";
import { useGetAuditLogs, useGetAPICallLogs, useGetPowershellLogs } from "@workspace/api-client-react";
import { Card, CardContent } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import { format } from "date-fns";
import { Badge } from "@/components/ui/badge";
import { Terminal } from "lucide-react";

function AuditLogsTab() {
  const { data, isLoading } = useGetAuditLogs({ limit: 50 });

  if (isLoading) return <Skeleton className="h-96 w-full" />;

  return (
    <Table>
      <TableHeader className="bg-muted/50">
        <TableRow>
          <TableHead>Time</TableHead>
          <TableHead>Event Type</TableHead>
          <TableHead>Actor</TableHead>
          <TableHead>Ticket ID</TableHead>
          <TableHead>Platform</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {data?.logs.map(log => (
          <TableRow key={log.log_id}>
            <TableCell className="text-sm text-muted-foreground">{format(new Date(log.created_at), "MMM d, HH:mm:ss")}</TableCell>
            <TableCell className="font-medium capitalize">{log.event_type.replace(/_/g, ' ')}</TableCell>
            <TableCell>{log.actor_name || log.actor_id}</TableCell>
            <TableCell className="font-mono text-xs">{log.ticket_id?.split('-')[0] || '-'}</TableCell>
            <TableCell><Badge variant="outline" className="bg-background">{log.platform || 'API'}</Badge></TableCell>
          </TableRow>
        ))}
        {(!data?.logs || data.logs.length === 0) && (
          <TableRow>
            <TableCell colSpan={5} className="text-center h-24 text-muted-foreground">No audit logs found.</TableCell>
          </TableRow>
        )}
      </TableBody>
    </Table>
  );
}

function APILogsTab() {
  const { data, isLoading } = useGetAPICallLogs({ limit: 50 } as any); 

  if (isLoading) return <Skeleton className="h-96 w-full" />;

  return (
    <Table>
      <TableHeader className="bg-muted/50">
        <TableRow>
          <TableHead>Time</TableHead>
          <TableHead>Method</TableHead>
          <TableHead>Endpoint</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Duration</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {(data as any)?.map((log: any) => (
          <TableRow key={log.api_log_id}>
            <TableCell className="text-sm text-muted-foreground">{format(new Date(log.called_at), "HH:mm:ss.SSS")}</TableCell>
            <TableCell>
              <Badge variant="secondary" className={log.method === 'GET' ? 'bg-blue-100 text-blue-800' : log.method === 'POST' ? 'bg-green-100 text-green-800' : 'bg-orange-100 text-orange-800'}>
                {log.method}
              </Badge>
            </TableCell>
            <TableCell className="font-mono text-xs">{log.endpoint || log.api_name}</TableCell>
            <TableCell>
              <span className={log.response_status >= 400 ? "text-destructive font-bold" : "text-green-600 font-bold"}>
                {log.response_status}
              </span>
            </TableCell>
            <TableCell>{log.duration_ms}ms</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

function PowerShellLogsTab() {
  const { data, isLoading } = useGetPowershellLogs({ limit: 50 } as any);

  if (isLoading) return <Skeleton className="h-96 w-full" />;

  const logs = (data as any) || [];

  return (
    <Table>
      <TableHeader className="bg-muted/50">
        <TableRow>
          <TableHead>Time</TableHead>
          <TableHead>Script Name</TableHead>
          <TableHead>Device</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Duration</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {logs.map((log: any) => (
          <TableRow key={log.execution_id}>
            <TableCell className="text-sm text-muted-foreground">{format(new Date(log.executed_at), "MMM d, HH:mm:ss")}</TableCell>
            <TableCell className="font-medium flex items-center gap-2">
              <Terminal className="h-4 w-4 text-primary" />
              {log.script_name}
            </TableCell>
            <TableCell className="font-mono text-xs">{log.device_name || '-'}</TableCell>
            <TableCell>
              <Badge variant={log.execution_status === 'success' ? 'default' : log.execution_status === 'failed' ? 'destructive' : 'secondary'} className={log.execution_status === 'success' ? 'bg-green-600' : ''}>
                {log.execution_status}
              </Badge>
            </TableCell>
            <TableCell>{log.duration_seconds}s</TableCell>
          </TableRow>
        ))}
        {logs.length === 0 && (
          <TableRow>
            <TableCell colSpan={5} className="text-center h-24 text-muted-foreground">No PowerShell executions found.</TableCell>
          </TableRow>
        )}
      </TableBody>
    </Table>
  );
}

export default function Logs() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">System Logs</h1>
        <p className="text-muted-foreground">Monitor system activity, API calls, and automated script executions.</p>
      </div>

      <Card>
        <CardContent className="p-0">
          <Tabs defaultValue="audit" className="w-full border-none">
            <div className="border-b px-4 py-2 bg-muted/20">
              <TabsList className="bg-transparent space-x-2">
                <TabsTrigger value="audit" className="data-[state=active]:bg-background data-[state=active]:shadow-sm">Audit Logs</TabsTrigger>
                <TabsTrigger value="api" className="data-[state=active]:bg-background data-[state=active]:shadow-sm">API Calls</TabsTrigger>
                <TabsTrigger value="powershell" className="data-[state=active]:bg-background data-[state=active]:shadow-sm">PowerShell Executions</TabsTrigger>
              </TabsList>
            </div>
            <div className="p-4">
              <TabsContent value="audit" className="mt-0 outline-none">
                <div className="border rounded-md">
                  <AuditLogsTab />
                </div>
              </TabsContent>
              <TabsContent value="api" className="mt-0 outline-none">
                <div className="border rounded-md">
                  <APILogsTab />
                </div>
              </TabsContent>
              <TabsContent value="powershell" className="mt-0 outline-none">
                <div className="border rounded-md">
                  <PowerShellLogsTab />
                </div>
              </TabsContent>
            </div>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
}

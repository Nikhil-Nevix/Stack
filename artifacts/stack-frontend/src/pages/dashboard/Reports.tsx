import { useGetResolutionRate, useGetSLACompliance, useGetAIAccuracy, useGetTicketTrends, useGetAgentPerformance } from "@workspace/api-client-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line, Legend, AreaChart, Area } from "recharts";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";

const COLORS = ['hsl(var(--chart-1))', 'hsl(var(--chart-2))', 'hsl(var(--chart-3))', 'hsl(var(--chart-4))', 'hsl(var(--chart-5))'];

export default function Reports() {
  const { data: resolutionRate, isLoading: loadingResolution } = useGetResolutionRate();
  const { data: slaCompliance, isLoading: loadingSLA } = useGetSLACompliance();
  const { data: aiAccuracy, isLoading: loadingAI } = useGetAIAccuracy();
  const { data: ticketTrends, isLoading: loadingTrends } = useGetTicketTrends();
  const { data: agentPerformance, isLoading: loadingAgents } = useGetAgentPerformance({ limit: 10 } as any);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold">Reports & Analytics</h1>
          <p className="text-muted-foreground">Performance metrics and insights for the last 30 days.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Resolution Rate by Use Case</CardTitle>
          </CardHeader>
          <CardContent className="h-[300px]">
            {loadingResolution ? <Skeleton className="h-full w-full" /> : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={resolutionRate?.by_use_case}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border))" />
                  <XAxis dataKey="use_case" tick={{fontSize: 12}} />
                  <YAxis tick={{fontSize: 12}} />
                  <Tooltip contentStyle={{backgroundColor: 'hsl(var(--popover))', borderColor: 'hsl(var(--border))'}} />
                  <Legend />
                  <Bar dataKey="auto_resolved" name="Auto Resolved" stackId="a" fill="hsl(var(--chart-2))" />
                  <Bar dataKey="manual_resolved" name="Manual Resolved" stackId="a" fill="hsl(var(--chart-1))" />
                </BarChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>SLA Compliance Status</CardTitle>
          </CardHeader>
          <CardContent className="h-[300px] flex items-center justify-center">
            {loadingSLA ? <Skeleton className="h-full w-full" /> : (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={[
                      { name: 'Met', value: slaCompliance?.met || 0 },
                      { name: 'Breached', value: slaCompliance?.breached || 0 },
                      { name: 'At Risk', value: slaCompliance?.at_risk || 0 }
                    ]}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    paddingAngle={2}
                    dataKey="value"
                  >
                    <Cell fill="hsl(var(--chart-2))" />
                    <Cell fill="hsl(var(--destructive))" />
                    <Cell fill="hsl(var(--chart-3))" />
                  </Pie>
                  <Tooltip contentStyle={{backgroundColor: 'hsl(var(--popover))', borderColor: 'hsl(var(--border))'}} />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Ticket Volume Trends</CardTitle>
          </CardHeader>
          <CardContent className="h-[300px]">
            {loadingTrends ? <Skeleton className="h-full w-full" /> : (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={ticketTrends?.trend}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border))" />
                  <XAxis dataKey="date" tick={{fontSize: 12}} />
                  <YAxis tick={{fontSize: 12}} />
                  <Tooltip contentStyle={{backgroundColor: 'hsl(var(--popover))', borderColor: 'hsl(var(--border))'}} />
                  <Area type="monotone" dataKey="total" stroke="hsl(var(--primary))" fill="hsl(var(--primary))" fillOpacity={0.2} />
                </AreaChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>AI Confidence Distribution</CardTitle>
          </CardHeader>
          <CardContent className="h-[300px]">
            {loadingAI ? <Skeleton className="h-full w-full" /> : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={aiAccuracy?.distribution}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border))" />
                  <XAxis dataKey="range" tick={{fontSize: 12}} />
                  <YAxis tick={{fontSize: 12}} />
                  <Tooltip contentStyle={{backgroundColor: 'hsl(var(--popover))', borderColor: 'hsl(var(--border))'}} />
                  <Bar dataKey="count" fill="hsl(var(--chart-3))" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Agent Performance</CardTitle>
        </CardHeader>
        <CardContent>
          {loadingAgents ? <Skeleton className="h-48 w-full" /> : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Agent</TableHead>
                  <TableHead>Tickets Resolved</TableHead>
                  <TableHead>Avg Resolution Time</TableHead>
                  <TableHead>SLA Met %</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {(agentPerformance as any)?.map((agent: any) => (
                  <TableRow key={agent.agent_id}>
                    <TableCell className="font-medium">{agent.agent_name}</TableCell>
                    <TableCell>{agent.tickets_resolved}</TableCell>
                    <TableCell>{Math.round(agent.avg_resolution_mins)} mins</TableCell>
                    <TableCell>
                      <Badge variant={agent.sla_met_pct >= 90 ? 'default' : agent.sla_met_pct >= 75 ? 'secondary' : 'destructive'}>
                        {agent.sla_met_pct.toFixed(1)}%
                      </Badge>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

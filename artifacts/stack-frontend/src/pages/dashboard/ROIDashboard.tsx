import { useState } from "react";
import { useGetCurrentROI, useGetROIHistory, useUpdateROISettings, useRecalculateROI } from "@workspace/api-client-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, Legend } from "recharts";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useToast } from "@/hooks/use-toast";
import { IndianRupee, Clock, TrendingUp, Zap } from "lucide-react";
import { useQueryClient } from "@tanstack/react-query";

export default function ROIDashboard() {
  const { data: currentROI, isLoading: loadingCurrent } = useGetCurrentROI();
  const { data: roiHistory, isLoading: loadingHistory } = useGetROIHistory();
  const updateSettings = useUpdateROISettings();
  const recalculateROI = useRecalculateROI();
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const [hourlyCost, setHourlyCost] = useState<string>("500");
  const [manualMins, setManualMins] = useState<string>("30");

  const handleSaveSettings = async () => {
    try {
      await updateSettings.mutateAsync({
        data: {
          agent_hourly_cost: Number(hourlyCost),
          avg_manual_resolution_mins: Number(manualMins)
        }
      });
      await recalculateROI.mutateAsync();
      queryClient.invalidateQueries({ queryKey: ["getCurrentROI"] });
      queryClient.invalidateQueries({ queryKey: ["getROIHistory"] });
      toast({ title: "Settings Updated", description: "ROI metrics have been recalculated." });
    } catch (e: any) {
      toast({ variant: "destructive", title: "Error", description: e?.data?.detail || "Failed to update settings" });
    }
  };

  const formatCurrency = (val: number) => `₹${val.toLocaleString()}`;

  return (
    <div className="space-y-6">
      {loadingCurrent || !currentROI ? (
        <Skeleton className="h-24 w-full" />
      ) : (
        <div className="bg-gradient-to-r from-primary to-sidebar-accent p-6 rounded-lg text-primary-foreground shadow-md">
          <h2 className="text-2xl font-bold mb-2">STACK has saved Jade Global {Math.round(currentROI.hours_saved)} hours and {formatCurrency(currentROI.cost_saved)} this month</h2>
          <p className="text-primary-foreground/80 text-sm">Based on {currentROI.auto_resolved_count} auto-resolved tickets.</p>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Auto-Resolved</CardTitle>
            <Zap className="h-4 w-4 text-accent" />
          </CardHeader>
          <CardContent>
            {loadingCurrent ? <Skeleton className="h-8 w-16" /> : (
              <div className="text-2xl font-bold">{currentROI?.auto_resolved_count}</div>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Hours Saved</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {loadingCurrent ? <Skeleton className="h-8 w-16" /> : (
              <div className="text-2xl font-bold">{Math.round(currentROI?.hours_saved || 0)}</div>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Cost Saved</CardTitle>
            <IndianRupee className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            {loadingCurrent ? <Skeleton className="h-8 w-24" /> : (
              <div className="text-2xl font-bold text-green-600">{formatCurrency(currentROI?.cost_saved || 0)}</div>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Agent Capacity Freed</CardTitle>
            <TrendingUp className="h-4 w-4 text-chart-3" />
          </CardHeader>
          <CardContent>
            {loadingCurrent ? <Skeleton className="h-8 w-16" /> : (
              <div className="text-2xl font-bold">{Math.round(((currentROI?.auto_resolved_count || 0) / (currentROI?.total_tickets || 1)) * 100)}%</div>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Monthly ROI Trend</CardTitle>
          </CardHeader>
          <CardContent className="h-[300px]">
            {loadingHistory ? <Skeleton className="h-full w-full" /> : (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={roiHistory as any}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border))" />
                  <XAxis dataKey="period_start" tickFormatter={(v) => v.substring(0,7)} tick={{fontSize: 12}} />
                  <YAxis tick={{fontSize: 12}} tickFormatter={(v) => `₹${v/1000}k`} />
                  <Tooltip contentStyle={{backgroundColor: 'hsl(var(--popover))', borderColor: 'hsl(var(--border))'}} />
                  <Legend />
                  <Line type="monotone" dataKey="cost_saved" name="Cost Saved (₹)" stroke="hsl(var(--chart-2))" strokeWidth={3} dot={{r: 4}} activeDot={{r: 6}} />
                </LineChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Settings</CardTitle>
            <CardDescription>Adjust baseline metrics used for calculation.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="hourlyCost">Agent Hourly Cost (₹)</Label>
              <Input 
                id="hourlyCost" 
                type="number" 
                value={hourlyCost} 
                onChange={(e) => setHourlyCost(e.target.value)} 
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="manualMins">Avg Manual Resolution (Mins)</Label>
              <Input 
                id="manualMins" 
                type="number" 
                value={manualMins} 
                onChange={(e) => setManualMins(e.target.value)} 
              />
            </div>
            <Button 
              className="w-full mt-4" 
              onClick={handleSaveSettings}
              disabled={updateSettings.isPending || recalculateROI.isPending}
            >
              {(updateSettings.isPending || recalculateROI.isPending) ? "Recalculating..." : "Save & Recalculate"}
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FileText, CheckCircle, Clock, Star, TrendingUp, TrendingDown, AlertCircle, RefreshCw } from "lucide-react";
import { api, type Kpis, type TrendItem, type Keyword } from "~/lib/api";

export default function DashboardPage() {
  const [kpis, setKpis] = useState<Kpis | null>(null);
  const [trend, setTrend] = useState<TrendItem[]>([]);
  const [pending, setPending] = useState<Keyword[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = async () => {
    try { setLoading(true); setError("");
      const [k, t, b] = await Promise.all([api.overview.kpis(), api.overview.trend(7), api.overview.board()]);
      setKpis(k); setTrend(t.items); setPending(b.pending_keywords || []);
    } catch (e: any) { setError(e.message); } finally { setLoading(false); }
  };
  useEffect(() => { load(); const i = setInterval(load, 30000); return () => clearInterval(i); }, []);

  const kpiCards = [
    { label: "文章总数", val: kpis?.articles_total ?? "-", icon: FileText, accent: "bg-blue-500" },
    { label: "质检通过", val: kpis?.passed_articles ?? "-", icon: CheckCircle, accent: "bg-emerald-500" },
    { label: "待处理词", val: kpis?.pending_keywords ?? "-", icon: Clock, accent: "bg-amber-500" },
    { label: "平均质量分", val: kpis?.average_quality_score?.toFixed(1) ?? "-", icon: Star, accent: "bg-blue-500" },
  ];
  const maxV = Math.max(...trend.map(t => t.count), 1);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div><h1 className="text-2xl font-bold tracking-tight text-slate-900">数据总览</h1><p className="text-sm text-slate-500 mt-1">GEO 引擎实时运行状态 · 每 30 秒自动刷新</p></div>
        <button onClick={load} className="text-blue-600 hover:text-blue-700"><RefreshCw className="h-4 w-4" /></button>
      </div>
      {error && <div className="p-3 rounded-lg bg-red-50 text-red-700 text-sm flex items-center gap-2"><AlertCircle className="h-4 w-4" />{error}</div>}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {kpiCards.map(k => (<Card key={k.label} className="relative overflow-hidden border-[#E4ECFC] hover:shadow-md transition-shadow"><div className={`absolute left-0 top-2 bottom-2 w-1 rounded-r-full ${k.accent}`} /><CardContent className="p-5 pl-6"><div className="flex items-start justify-between"><div><p className="text-sm font-medium text-slate-500">{k.label}</p><p className="text-2xl font-bold tracking-tight text-slate-900 mt-1">{k.val}</p></div><k.icon className="h-8 w-8 text-blue-500/20" /></div></CardContent></Card>))}
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card className="lg:col-span-2 border-[#E4ECFC]"><CardHeader className="pb-2"><CardTitle className="text-base">7 日产出趋势</CardTitle></CardHeader><CardContent>{loading ? <div className="h-48 flex items-center justify-center text-slate-400">加载中...</div> : trend.length === 0 ? <div className="h-48 flex items-center justify-center text-slate-400">暂无数据</div> : <div className="h-48 flex items-end gap-1.5">{trend.map((t,i)=><div key={i} className="flex-1 flex flex-col items-center gap-1"><div className="w-full rounded-t-sm" style={{height:`${(t.count/maxV)*100}%`,minHeight:8}}><div className={`w-full h-full bg-gradient-to-t from-blue-500 to-blue-400 rounded-t-sm opacity-80`} style={{height:`${(t.count/maxV)*100}%`}}/></div><span className="text-[10px] text-slate-400">{t.day?.slice(5)||i}</span></div>)}</div>}</CardContent></Card>
        <Card className="border-[#E4ECFC]"><CardHeader className="pb-2"><CardTitle className="text-base">待处理关键词</CardTitle></CardHeader><CardContent>{loading ? <div className="text-slate-400 text-sm">加载中...</div> : pending.length===0 ? <div className="text-center py-8 text-slate-400 text-sm">暂无待处理关键词</div> : <div className="space-y-3">{pending.slice(0,6).map(kw=><div key={kw.id} className="flex items-center justify-between text-sm"><span className="truncate flex-1 mr-2 text-slate-700">{kw.keyword}</span><span className="text-xs text-slate-400 whitespace-nowrap">{(kw.search_volume||0).toLocaleString()} 搜索</span></div>)}</div>}</CardContent></Card>
      </div>
    </div>
  );
}

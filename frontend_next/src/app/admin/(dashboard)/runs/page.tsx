"use client";
import { useEffect, useState } from "react";
import { Card, CardContent } from "@saasfly/ui/card";
import { Button } from "@saasfly/ui/button";
import { Input } from "@saasfly/ui/input";
import { RefreshCw } from "lucide-react";
import { api, type Run, type RunSummary } from "~/lib/api";

const runStColor: Record<string,string> = { running:"bg-blue-50 text-blue-700", succeeded:"bg-emerald-50 text-emerald-700", failed:"bg-red-50 text-red-700", partial:"bg-amber-50 text-amber-700" };

export default function RunsPage() {
  const [items, setItems] = useState<Run[]>([]);
  const [sum, setSum] = useState<RunSummary|null>(null);
  const [q, setQ] = useState(""); const [sf, setSf] = useState("");
  const [loading, setLoading] = useState(true); const [err, setErr] = useState("");
  const load = async () => { try { setLoading(true); setErr(""); const [l,s] = await Promise.all([api.runs.list({keyword:q||undefined,status:sf||undefined}),api.runs.summary()]); setItems(l.items); setSum(s); } catch(e:any){setErr(e.message)} finally{setLoading(false)} };
  useEffect(()=>{load()},[sf]);
  return (<div className="space-y-6">
    <div className="flex items-center justify-between"><div><h1 className="text-2xl font-bold tracking-tight text-slate-900">运行记录</h1><p className="text-sm text-slate-500 mt-1">任务执行历史 · 步骤时间线 · 失败追溯</p></div><Button className="bg-blue-600 hover:bg-blue-700" onClick={load}><RefreshCw className="h-4 w-4 mr-2"/>刷新</Button></div>
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">{[{l:"总运行",v:sum?.total_runs??"-"},{l:"运行中",v:sum?.running_runs??"-"},{l:"成功",v:sum?.succeeded_runs??"-"},{l:"失败",v:sum?.failed_runs??"-"}].map(k=><Card key={k.l} className="border-[#E4ECFC]"><CardContent className="p-4"><p className="text-sm text-slate-500">{k.l}</p><p className="text-2xl font-bold">{k.v}</p></CardContent></Card>)}</div>
    <div className="flex gap-2"><Input placeholder="搜索关键词..." className="max-w-xs" value={q} onChange={e=>setQ(e.target.value)} onKeyDown={e=>e.key==="Enter"&&load()}/><select className="border rounded-md px-3 text-sm" value={sf} onChange={e=>setSf(e.target.value)}><option value="">全部</option><option value="running">运行中</option><option value="succeeded">成功</option><option value="failed">失败</option></select><Button variant="outline" onClick={load}>搜索</Button></div>
    {err&&<div className="p-3 rounded-lg bg-red-50 text-red-700 text-sm">{err}</div>}
    <Card className="border-[#E4ECFC]"><CardContent className="p-0">
      {loading?<div className="p-8 text-center text-slate-400">加载中...</div>:items.length===0?<div className="p-8 text-center text-slate-400">暂无运行记录</div>:
      <table className="w-full text-sm"><thead><tr className="border-b text-left text-xs font-medium text-slate-500 uppercase"><th className="p-3 pl-4">UID</th><th className="p-3">关键词</th><th className="p-3">类型</th><th className="p-3">状态</th><th className="p-3">步骤</th><th className="p-3">开始</th></tr></thead>
      <tbody>{items.map(r=><tr key={r.id} className="border-b border-slate-50 hover:bg-slate-50"><td className="p-3 pl-4 font-mono text-xs">{r.run_uid?.slice(0,8)}</td><td className="p-3">{r.keyword||"-"}</td><td className="p-3 text-slate-500">{r.trigger_mode}</td><td className="p-3"><span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${runStColor[r.status]||""}`}>{r.status}</span></td><td className="p-3 text-slate-500">{r.current_step||"-"}</td><td className="p-3 text-slate-400 text-xs">{r.started_at?.slice(0,16)||"-"}</td></tr>)}</tbody></table>}
    </CardContent></Card>
  </div>);
}

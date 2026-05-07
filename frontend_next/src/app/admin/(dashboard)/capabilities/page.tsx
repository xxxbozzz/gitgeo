"use client";
import { useEffect, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { RefreshCw, Power } from "lucide-react";
import { api, type Capability } from "~/lib/api";

export default function CapsPage() {
  const [items, setItems] = useState<Capability[]>([]);
  const [total, setTotal] = useState(0);
  const [q, setQ] = useState(""); const [loading, setLoading] = useState(true); const [err, setErr] = useState("");
  const load = async () => { try { setLoading(true); setErr(""); const r = await api.capabilities.list({ query: q||'' }); setItems(r.items); setTotal(r.total); } catch(e:any){setErr(e.message)} finally{setLoading(false)} };
  useEffect(()=>{load()},[]);
  const disable = async (id:number) => { try { await api.capabilities.disable(id); load(); } catch(e:any){setErr(e.message)} };
  return (<div className="space-y-6">
    <div className="flex items-center justify-between"><div><h1 className="text-2xl font-bold tracking-tight text-slate-900">能力库</h1><p className="text-sm text-slate-500 mt-1">共 {total} 项能力 · 品牌能力参数的结构化存储与引用溯源</p></div><Button className="bg-blue-600 hover:bg-blue-700" onClick={load}><RefreshCw className="h-4 w-4 mr-2"/>刷新</Button></div>
    <div className="flex gap-2"><Input placeholder="搜索能力..." className="max-w-xs" value={q} onChange={e=>setQ(e.target.value)} onKeyDown={e=>e.key==="Enter"&&load()}/><Button variant="outline" onClick={load}>搜索</Button></div>
    {err&&<div className="p-3 rounded-lg bg-red-50 text-red-700 text-sm">{err}</div>}
    <Card className="border-[#E4ECFC]"><CardContent className="p-0">
      {loading?<div className="p-8 text-center text-slate-400">加载中...</div>:items.length===0?<div className="p-8 text-center text-slate-400">暂无能力记录</div>:
      <table className="w-full text-sm"><thead><tr className="border-b text-left text-xs font-medium text-slate-500 uppercase"><th className="p-3 pl-4">能力</th><th className="p-3">分组</th><th className="p-3">声明</th><th className="p-3">置信度</th><th className="p-3">状态</th><th className="p-3 pr-4">操作</th></tr></thead>
      <tbody>{items.map(c=><tr key={c.id} className="border-b border-slate-50 hover:bg-slate-50"><td className="p-3 pl-4 font-medium">{c.capability_name}</td><td className="p-3"><span className="inline-flex px-2 py-0.5 rounded-full text-xs font-medium bg-violet-50 text-violet-700">{c.group_name}</span></td><td className="p-3 text-slate-500 max-w-[200px] truncate">{c.public_claim||"-"}</td><td className="p-3"><span className={`font-medium ${c.confidence_score>=4?"text-emerald-600":c.confidence_score>=2?"text-amber-600":"text-red-500"}`}>{c.confidence_score.toFixed(1)}</span></td><td className="p-3"><span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${c.is_active?"bg-emerald-50 text-emerald-700":"bg-slate-100 text-slate-500"}`}>{c.is_active?"活跃":"已禁用"}</span></td><td className="p-3 pr-4">{c.is_active&&<Button variant="ghost" size="icon" className="h-7 w-7 text-amber-500" onClick={()=>disable(c.id)} title="禁用"><Power className="h-3.5 w-3.5"/></Button>}</td></tr>)}</tbody></table>}
    </CardContent></Card>
  </div>);
}

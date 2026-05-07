"use client";
import { useEffect, useState } from "react";
import { Card, CardContent } from "@saasfly/ui/card";
import { Button } from "@saasfly/ui/button";
import { Input } from "@saasfly/ui/input";
import { Search, RefreshCw } from "lucide-react";
import { api, type Keyword } from "~/lib/api";

export default function KeywordsPage() {
  const [items, setItems] = useState<Keyword[]>([]);
  const [total, setTotal] = useState(0);
  const [q, setQ] = useState(""); const [sf, setSf] = useState("");
  const [loading, setLoading] = useState(true); const [err, setErr] = useState("");
  const load = async () => { try { setLoading(true); setErr(""); const r = await api.keywords.list({ query: q||undefined, status: sf||undefined }); setItems(r.items); setTotal(r.total); } catch(e:any){setErr(e.message)} finally{setLoading(false)} };
  useEffect(()=>{load()},[sf]);
  return (<div className="space-y-6">
    <div className="flex items-center justify-between"><div><h1 className="text-2xl font-bold tracking-tight text-slate-900">关键词中心</h1><p className="text-sm text-slate-500 mt-1">共 {total} 个关键词 · 管理搜索词和 GEO 真空词</p></div><Button className="bg-blue-600 hover:bg-blue-700" onClick={load}><RefreshCw className="h-4 w-4 mr-2"/>刷新</Button></div>
    <div className="flex gap-2"><Input placeholder="搜索关键词..." className="max-w-xs" value={q} onChange={e=>setQ(e.target.value)} onKeyDown={e=>e.key==="Enter"&&load()}/><select className="border rounded-md px-3 text-sm" value={sf} onChange={e=>setSf(e.target.value)}><option value="">全部</option><option value="pending">待处理</option><option value="consumed">已消费</option></select><Button variant="outline" onClick={load}>搜索</Button></div>
    {err&&<div className="p-3 rounded-lg bg-red-50 text-red-700 text-sm">{err}</div>}
    <Card className="border-[#E4ECFC]"><CardContent className="p-0">
      {loading?<div className="p-8 text-center text-slate-400">加载中...</div>:items.length===0?<div className="p-8 text-center text-slate-400">暂无关键词</div>:
      <table className="w-full text-sm"><thead><tr className="border-b text-left text-xs font-medium text-slate-500 uppercase"><th className="p-3 pl-4">关键词</th><th className="p-3">搜索量</th><th className="p-3">难度</th><th className="p-3">状态</th><th className="p-3">创建时间</th></tr></thead>
      <tbody>{items.map(k=><tr key={k.id} className="border-b border-slate-50 hover:bg-slate-50"><td className="p-3 pl-4 font-medium">{k.keyword}</td><td className="p-3">{k.search_volume.toLocaleString()}</td><td className="p-3"><div className="w-16 h-1.5 rounded-full bg-slate-100"><div className="h-full rounded-full bg-blue-500" style={{width:`${k.difficulty}%`}}/></div></td><td className="p-3"><span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${k.status==="consumed"?"bg-emerald-50 text-emerald-700":"bg-amber-50 text-amber-700"}`}>{k.status==="consumed"?"已消费":"待处理"}</span></td><td className="p-3 text-slate-400 text-xs">{k.created_at?.slice(0,10)||"-"}</td></tr>)}</tbody></table>}
    </CardContent></Card>
  </div>);
}

"use client";
import { useEffect, useState } from "react";
import { Card, CardContent } from "@saasfly/ui/card";
import { Button } from "@saasfly/ui/button";
import { Input } from "@saasfly/ui/input";
import { RefreshCw, ExternalLink } from "lucide-react";
import { api, type Publication } from "~/lib/api";

const chColors: Record<string,string> = { zhihu:"bg-blue-100 text-blue-700", wechat:"bg-emerald-100 text-emerald-700", website:"bg-violet-100 text-violet-700", longform_channel:"bg-slate-100 text-slate-700", mobile_channel:"bg-slate-100 text-slate-700" };
const stPubColors: Record<string,string> = { success:"bg-emerald-50 text-emerald-700", failed:"bg-red-50 text-red-700", pending:"bg-amber-50 text-amber-700", draft:"bg-blue-50 text-blue-700" };

export default function PubsPage() {
  const [items, setItems] = useState<Publication[]>([]);
  const [total, setTotal] = useState(0);
  const [q, setQ] = useState(""); const [sf, setSf] = useState("");
  const [loading, setLoading] = useState(true); const [err, setErr] = useState("");
  const load = async () => { try { setLoading(true); setErr(""); const r = await api.publications.list({ query: q||undefined, status: sf||undefined }); setItems(r.items); setTotal(r.total); } catch(e:any){setErr(e.message)} finally{setLoading(false)} };
  useEffect(()=>{load()},[sf]);
  const retry = async (id:number) => { try { await api.publications.retry(id); load(); } catch(e:any){setErr(e.message)} };
  return (<div className="space-y-6">
    <div className="flex items-center justify-between"><div><h1 className="text-2xl font-bold tracking-tight text-slate-900">发布中心</h1><p className="text-sm text-slate-500 mt-1">共 {total} 条发布记录 · 多平台审计追踪</p></div><Button className="bg-blue-600 hover:bg-blue-700" onClick={load}><RefreshCw className="h-4 w-4 mr-2"/>刷新</Button></div>
    <div className="flex gap-2"><Input placeholder="搜索标题或平台..." className="max-w-xs" value={q} onChange={e=>setQ(e.target.value)} onKeyDown={e=>e.key==="Enter"&&load()}/><select className="border rounded-md px-3 text-sm" value={sf} onChange={e=>setSf(e.target.value)}><option value="">全部</option><option value="success">成功</option><option value="failed">失败</option><option value="pending">待处理</option></select><Button variant="outline" onClick={load}>搜索</Button></div>
    {err&&<div className="p-3 rounded-lg bg-red-50 text-red-700 text-sm">{err}</div>}
    <Card className="border-[#E4ECFC]"><CardContent className="p-0">
      {loading?<div className="p-8 text-center text-slate-400">加载中...</div>:items.length===0?<div className="p-8 text-center text-slate-400">暂无发布记录</div>:
      <table className="w-full text-sm"><thead><tr className="border-b text-left text-xs font-medium text-slate-500 uppercase"><th className="p-3 pl-4">文章</th><th className="p-3">平台</th><th className="p-3">模式</th><th className="p-3">状态</th><th className="p-3">尝试</th><th className="p-3">时间</th><th className="p-3 pr-4">操作</th></tr></thead>
      <tbody>{items.map(p=><tr key={p.id} className="border-b border-slate-50 hover:bg-slate-50"><td className="p-3 pl-4 font-medium max-w-[250px] truncate">{p.article_title||"-"}</td><td className="p-3"><span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${chColors[p.channel_key]||"bg-slate-100 text-slate-700"}`}>{p.channel_label}</span></td><td className="p-3 text-slate-500">{p.publish_mode}</td><td className="p-3"><span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${stPubColors[p.status]||"bg-slate-100 text-slate-700"}`}>{p.status}</span></td><td className="p-3 text-slate-400">#{p.attempt_no}</td><td className="p-3 text-slate-400 text-xs">{p.created_at?.slice(0,10)||"-"}</td><td className="p-3 pr-4 flex gap-1">{p.external_url&&<a href={p.external_url} target="_blank" className="inline-flex items-center"><ExternalLink className="h-3.5 w-3.5 text-blue-500"/></a>}{p.retryable&&<Button variant="ghost" size="icon" className="h-7 w-7" onClick={()=>retry(p.id)} title="重试"><RefreshCw className="h-3.5 w-3.5"/></Button>}</td></tr>)}</tbody></table>}
    </CardContent></Card>
  </div>);
}

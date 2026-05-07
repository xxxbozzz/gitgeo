"use client";

import { useEffect, useState } from "react";
import { Card, CardContent } from "@saasfly/ui/card";
import { Button } from "@saasfly/ui/button";
import { Input } from "@saasfly/ui/input";
import { Eye, RefreshCw, Trash2, Send } from "lucide-react";
import { api, type Article, type ArticlesSummary } from "~/lib/api";

const stLabel: Record<number, string> = { 0: "草稿", 1: "已通过", 2: "已发布", 3: "归档" };
const stColor: Record<number, string> = { 0: "bg-slate-100 text-slate-700", 1: "bg-emerald-50 text-emerald-700", 2: "bg-blue-50 text-blue-700", 3: "bg-slate-200 text-slate-500" };

export default function ArticlesPage() {
  const [items, setItems] = useState<Article[]>([]);
  const [sum, setSum] = useState<ArticlesSummary | null>(null);
  const [q, setQ] = useState(""); const [sf, setSf] = useState("");
  const [loading, setLoading] = useState(true); const [err, setErr] = useState("");

  const load = async () => {
    try { setLoading(true); setErr("");
      const [l, s] = await Promise.all([api.articles.list({ query: q || undefined, status: sf || undefined }), api.articles.summary()]);
      setItems(l.items); setSum(s);
    } catch (e: any) { setErr(e.message); } finally { setLoading(false); }
  };
  useEffect(() => { load(); }, [sf]);

  const act = async (a: string, id: number) => {
    try { if (a === "refix") await api.articles.refix(id); else if (a === "recycle") await api.articles.recycle(id); else if (a === "pub") await api.articles.publish(id, ["zhihu"]); load(); }
    catch (e: any) { setErr(e.message); }
  };

  const kpis = [{ label: "总文章", val: sum?.total_articles ?? "-" },{ label: "草稿", val: sum?.draft_articles ?? "-" },{ label: "已通过", val: sum?.approved_articles ?? "-" },{ label: "已发布", val: sum?.published_articles ?? "-" }];

  return (<div className="space-y-6">
    <div className="flex items-center justify-between"><div><h1 className="text-2xl font-bold tracking-tight text-slate-900">文章管理</h1><p className="text-sm text-slate-500 mt-1">草稿 / 已通过 / 已发布 · 返修 · 回收 · 发布</p></div><Button className="bg-blue-600 hover:bg-blue-700" onClick={load}><RefreshCw className="h-4 w-4 mr-2"/>刷新</Button></div>
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">{kpis.map(k=><Card key={k.label} className="border-[#E4ECFC]"><CardContent className="p-4"><p className="text-sm text-slate-500">{k.label}</p><p className="text-2xl font-bold">{k.val}</p></CardContent></Card>)}</div>
    <div className="flex gap-2"><Input placeholder="搜索标题..." className="max-w-xs" value={q} onChange={e=>setQ(e.target.value)} onKeyDown={e=>e.key==="Enter"&&load()}/><select className="border rounded-md px-3 text-sm" value={sf} onChange={e=>setSf(e.target.value)}><option value="">全部</option><option value="draft">草稿</option><option value="approved">已通过</option><option value="published">已发布</option></select><Button variant="outline" onClick={load}>搜索</Button></div>
    {err && <div className="p-3 rounded-lg bg-red-50 text-red-700 text-sm">{err}</div>}
    <Card className="border-[#E4ECFC]"><CardContent className="p-0">
      {loading ? <div className="p-8 text-center text-slate-400">加载中...</div> : items.length===0 ? <div className="p-8 text-center text-slate-400">暂无文章</div> :
      <table className="w-full text-sm"><thead><tr className="border-b text-left text-xs font-medium text-slate-500 uppercase"><th className="p-3 pl-4">ID</th><th className="p-3">标题</th><th className="p-3">分数</th><th className="p-3">状态</th><th className="p-3">时间</th><th className="p-3 pr-4">操作</th></tr></thead>
      <tbody>{items.map(a=><tr key={a.id} className="border-b border-slate-50 hover:bg-slate-50"><td className="p-3 pl-4 text-slate-400">{a.id}</td><td className="p-3 font-medium max-w-[350px] truncate">{a.title}</td><td className="p-3"><span className={`font-medium ${(a.quality_score||0)>=80?"text-emerald-600":(a.quality_score||0)>=60?"text-amber-600":"text-red-500"}`}>{a.quality_score||"-"}</span></td><td className="p-3"><span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${stColor[a.publish_status]||""}`}>{stLabel[a.publish_status]||"?"}</span></td><td className="p-3 text-slate-400 text-xs">{a.created_at?.slice(0,10)||"-"}</td><td className="p-3 pr-4 flex gap-1"><Button variant="ghost" size="icon" className="h-7 w-7" title="预览"><Eye className="h-3.5 w-3.5"/></Button><Button variant="ghost" size="icon" className="h-7 w-7" title="返修" onClick={()=>act("refix",a.id)}><RefreshCw className="h-3.5 w-3.5"/></Button><Button variant="ghost" size="icon" className="h-7 w-7" title="发布" onClick={()=>act("pub",a.id)}><Send className="h-3.5 w-3.5"/></Button><Button variant="ghost" size="icon" className="h-7 w-7 text-red-400" title="回收" onClick={()=>act("recycle",a.id)}><Trash2 className="h-3.5 w-3.5"/></Button></td></tr>)}</tbody></table>}
    </CardContent></Card>
  </div>);
}

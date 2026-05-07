"use client";
import { useEffect, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { RefreshCw, Server, Database, Cpu, Braces } from "lucide-react";
import { api, type SystemStatus } from "~/lib/api";

export default function SystemPage() {
  const [s, setS] = useState<SystemStatus|null>(null);
  const [loading, setLoading] = useState(true);
  const load = async () => { try { setLoading(true); const d = await api.system.status(); setS(d); } catch(e){} finally{setLoading(false)} };
  useEffect(()=>{load()},[]);
  return (<div className="space-y-6">
    <div className="flex items-center justify-between"><div><h1 className="text-2xl font-bold tracking-tight text-slate-900">系统状态</h1><p className="text-sm text-slate-500 mt-1">环境 · 数据库 · LLM · ChromaDB 健康检查</p></div><button onClick={load} className="text-blue-600 hover:text-blue-700"><RefreshCw className="h-4 w-4"/></button></div>
    {loading?<div className="p-8 text-center text-slate-400">加载中...</div>:
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
      {[{icon:Server,label:"环境",val:s?.environment||"-",ok:true},{icon:Database,label:"数据库",val:s?.database||"-",ok:s?.database==="ok"},{icon:Cpu,label:"LLM API",val:s?.llm_api_configured?"已配置":"未配置",ok:s?.llm_api_configured},{icon:Braces,label:"构建",val:s?.build||"-",ok:true}].map(k=><Card key={k.label} className="border-[#E4ECFC]"><CardContent className="p-4 flex items-center gap-3"><k.icon className={`h-8 w-8 ${k.ok?"text-emerald-500/30":"text-red-500/30"}`}/><div><p className="text-sm text-slate-500">{k.label}</p><p className="text-lg font-bold">{k.val}</p></div></CardContent></Card>)}</div>}
  </div>);
}

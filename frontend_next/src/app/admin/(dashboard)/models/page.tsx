"use client";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Cpu, Plus, Power } from "lucide-react";

const models = [
  { id: 1, name: "primary-chat-model", provider: "OpenAI-compatible", type: "chat", endpoint: "https://your-llm-endpoint.example/v1", primary: true },
  { id: 2, name: "gpt-4o", provider: "OpenAI", type: "chat", endpoint: "https://api.openai.com/v1", primary: false },
  { id: 3, name: "text-embedding-3-small", provider: "OpenAI", type: "embedding", endpoint: "https://api.openai.com/v1", primary: false },
];

export default function ModelsPage() {
  return (<div className="space-y-6">
    <div className="flex items-center justify-between"><div><h1 className="text-2xl font-bold tracking-tight text-slate-900">模型配置</h1><p className="text-sm text-slate-500 mt-1">管理 AI 模型接入与主备切换</p></div><Button className="bg-blue-600 hover:bg-blue-700"><Plus className="h-4 w-4 mr-2"/>添加模型</Button></div>
    <div className="space-y-3">{models.map(m=><Card key={m.id} className="border-[#E4ECFC]"><CardContent className="p-4 flex items-center justify-between"><div className="flex items-center gap-3"><Cpu className="h-5 w-5 text-blue-500"/><div><p className="font-medium">{m.name}<span className="text-xs text-slate-400 ml-2">{m.provider} · {m.type}</span></p><p className="text-xs text-slate-400 mt-0.5">{m.endpoint}</p></div></div><div className="flex items-center gap-3"><span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${m.primary?"bg-emerald-50 text-emerald-700":"bg-slate-100 text-slate-600"}`}>{m.primary?"主模型":"备用"}</span><button className="text-slate-400 hover:text-slate-600"><Power className="h-4 w-4"/></button></div></CardContent></Card>)}</div>
  </div>);
}

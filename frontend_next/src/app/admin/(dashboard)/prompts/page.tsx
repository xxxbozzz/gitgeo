"use client";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Plus, FileEdit, Play } from "lucide-react";

const templates = [
  { id: 1, name: "行业深度技术文章", category: "内容生成", active: true, desc: "含9维质检规则和品牌植入要求的完整技术长文模板，适配知识库召回" },
  { id: 2, name: "品牌能力宣传稿", category: "站外GEO", active: true, desc: "适配社交媒体平台的品牌能力宣传稿，自动嵌入能力库参数" },
  { id: 3, name: "FAQ 问答模板", category: "内容生成", active: true, desc: "结构化常见问题生成，自动包含标准引用和工程实践案例" },
  { id: 4, name: "SEO 元信息模板", category: "发布优化", active: false, desc: "自动生成 meta description、Open Graph 和结构化数据标记" },
];

export default function PromptsPage() {
  return (<div className="space-y-6">
    <div className="flex items-center justify-between"><div><h1 className="text-2xl font-bold tracking-tight text-slate-900">提示词库</h1><p className="text-sm text-slate-500 mt-1">管理 GEO Prompt 模板 · 版本控制 · 效果追踪</p></div><Button className="bg-blue-600 hover:bg-blue-700"><Plus className="h-4 w-4 mr-2"/>新建提示词</Button></div>
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">{templates.map(t=><Card key={t.id} className="border-[#E4ECFC] hover:shadow-md transition-shadow"><CardContent className="p-5"><div className="flex items-start justify-between mb-2"><div><span className="text-xs text-slate-400">{t.category}</span><h3 className="font-semibold mt-0.5">{t.name}</h3></div><span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${t.active?"bg-emerald-50 text-emerald-700":"bg-slate-100 text-slate-500"}`}>{t.active?"启用":"停用"}</span></div><p className="text-sm text-slate-500 mb-4">{t.desc}</p><div className="flex gap-2"><Button variant="outline" size="sm"><FileEdit className="h-3.5 w-3.5 mr-1"/>编辑</Button><Button size="sm" className="bg-blue-600"><Play className="h-3.5 w-3.5 mr-1"/>测试</Button></div></CardContent></Card>)}</div>
  </div>);
}

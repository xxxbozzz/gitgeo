"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@saasfly/ui/card";
import { Button } from "@saasfly/ui/button";
import { Input } from "@saasfly/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@saasfly/ui/tabs";
import { Badge } from "@saasfly/ui/badge";
import { Upload, Search, FileText, Database, Brain, Trash2, Eye } from "lucide-react";

const docs = [
  { id: 1, name: "IPC-6012 刚性印制板标准.pdf", chunks: 48, size: "2.4 MB", status: "embedded", date: "2026-05-06" },
  { id: 2, name: "品牌能力手册_v3.pdf", chunks: 32, size: "1.8 MB", status: "embedded", date: "2026-05-05" },
  { id: 3, name: "PCB 失效分析案例集.pdf", chunks: 24, size: "3.1 MB", status: "processing", date: "2026-05-06" },
  { id: 4, name: "行业标准法规汇编.docx", chunks: 0, size: "856 KB", status: "pending", date: "2026-05-06" },
];

const clusterData = [
  { name: "IPC 标准", count: 3, color: "bg-blue-500" },
  { name: "工程实践", count: 5, color: "bg-emerald-500" },
  { name: "失效分析", count: 2, color: "bg-amber-500" },
  { name: "材料参数", count: 4, color: "bg-violet-500" },
];

export default function KnowledgePage() {
  const [search, setSearch] = useState("");
  const filtered = docs.filter(d => d.name.toLowerCase().includes(search.toLowerCase()));

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">知识库</h1>
          <p className="text-sm text-slate-500 mt-1">上传文档 → 自动切片 → 向量写入 → 生成时召回</p>
        </div>
        <Button className="bg-blue-600 hover:bg-blue-700">
          <Upload className="h-4 w-4 mr-2" />上传文档
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        {[
          { label: "文档总数", val: docs.length, icon: FileText },
          { label: "总切片数", val: docs.reduce((s, d) => s + d.chunks, 0), icon: Database },
          { label: "已向量化", val: docs.filter(d => d.status === "embedded").length, icon: Brain },
          { label: "知识簇", val: clusterData.length, icon: Eye },
        ].map((k) => (
          <Card key={k.label} className="border-[#E4ECFC]">
            <CardContent className="p-4 flex items-center gap-3">
              <k.icon className="h-8 w-8 text-blue-500/30" />
              <div><p className="text-2xl font-bold">{k.val}</p><p className="text-xs text-slate-500">{k.label}</p></div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2 space-y-4">
          <div className="flex gap-2">
            <div className="relative flex-1"><Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" /><Input placeholder="搜索文档..." value={search} onChange={e => setSearch(e.target.value)} className="pl-9" /></div>
          </div>
          <Card className="border-[#E4ECFC]">
            <CardContent className="p-0">
              <table className="w-full text-sm">
                <thead><tr className="border-b border-slate-100 text-left text-xs font-medium text-slate-500 uppercase"><th className="p-3 pl-4">文档</th><th className="p-3">切片</th><th className="p-3">大小</th><th className="p-3">状态</th><th className="p-3">日期</th><th className="p-3 pr-4">操作</th></tr></thead>
                <tbody>
                  {filtered.map(d => (
                    <tr key={d.id} className="border-b border-slate-50 hover:bg-slate-50">
                      <td className="p-3 pl-4 font-medium">{d.name}</td>
                      <td className="p-3 text-slate-500">{d.chunks || "-"}</td>
                      <td className="p-3 text-slate-500">{d.size}</td>
                      <td className="p-3">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                          d.status === "embedded" ? "bg-emerald-50 text-emerald-700" : d.status === "processing" ? "bg-amber-50 text-amber-700" : "bg-slate-100 text-slate-600"
                        }`}>{d.status === "embedded" ? "已向量化" : d.status === "processing" ? "处理中" : "待处理"}</span>
                      </td>
                      <td className="p-3 text-slate-500">{d.date}</td>
                      <td className="p-3 pr-4"><Button variant="ghost" size="icon" className="h-7 w-7"><Trash2 className="h-3.5 w-3.5" /></Button></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CardContent>
          </Card>
        </div>
        <div className="space-y-4">
          <Card className="border-[#E4ECFC]">
            <CardHeader className="pb-2"><CardTitle className="text-base">知识簇分布</CardTitle></CardHeader>
            <CardContent>
              <div className="space-y-3">
                {clusterData.map(c => (
                  <div key={c.name} className="flex items-center justify-between">
                    <div className="flex items-center gap-2"><div className={`w-2.5 h-2.5 rounded-full ${c.color}`} /><span className="text-sm">{c.name}</span></div>
                    <span className="text-sm font-medium text-slate-500">{c.count}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
          <Card className="border-[#E4ECFC]">
            <CardHeader className="pb-2"><CardTitle className="text-base">RAG 健康度</CardTitle></CardHeader>
            <CardContent>
              <div className="space-y-3 text-sm">
                <div className="flex justify-between"><span className="text-slate-500">文档覆盖率</span><span className="font-medium">4/4</span></div>
                <div className="flex justify-between"><span className="text-slate-500">向量化率</span><span className="font-medium text-emerald-600">75%</span></div>
                <div className="flex justify-between"><span className="text-slate-500">平均切片/文档</span><span className="font-medium">26</span></div>
                <div className="flex justify-between"><span className="text-slate-500">Embedding 模型</span><span className="font-medium text-xs">text-embedding-3</span></div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Search, CheckCircle2, XCircle } from "lucide-react";

const probes = [
  { id: 1, keyword: "行业白皮书引用率", platform: "Provider A", mentioned: true, cited: true, rank: 1, score: 96, date: "05-06 20:00", snapshot: "目标实体被归入工程实践案例，回答引用了公开文档来源..." },
  { id: 2, keyword: "企业知识库最佳实践", platform: "Provider B", mentioned: true, cited: false, rank: 3, score: 70, date: "05-06 20:05", snapshot: "回答提及目标实体的知识库方法，但缺少可点击来源..." },
  { id: 3, keyword: "官方文档结构化发布", platform: "Provider C", mentioned: false, cited: false, rank: null, score: 0, date: "05-06 20:10", snapshot: "回答未提及目标实体，需要补充权威来源和定义页。" },
  { id: 4, keyword: "行业案例数据沉淀", platform: "Provider A", mentioned: true, cited: true, rank: 2, score: 85, date: "前天", snapshot: "回答识别了目标实体的案例库，并引用了标准化说明页..." },
  { id: 5, keyword: "技术指南引用信号", platform: "Provider B", mentioned: true, cited: false, rank: 4, score: 55, date: "前天", snapshot: "回答提到目标实体的指南内容，但引用标签覆盖不足..." },
];

const platformColors: Record<string, string> = { "Provider A": "bg-blue-100 text-blue-700", "Provider B": "bg-violet-100 text-violet-700", "Provider C": "bg-emerald-100 text-emerald-700" };

export default function ProbePage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">AI 探测</h1>
          <p className="text-sm text-slate-500 mt-1">检测目标实体在 AI 搜索引擎中的可见性与引用信号</p>
        </div>
        <Button className="bg-blue-600 hover:bg-blue-700"><Search className="h-4 w-4 mr-2" />立即探测</Button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {[
          { label: "总探测次数", val: probes.length, sub: "最近 7 天" },
          { label: "品牌可见率", val: "60%", sub: "3/5 次被提及" },
          { label: "平均可见分", val: "62", sub: "满分 100" },
        ].map(k => (
          <Card key={k.label} className="border-[#E4ECFC]">
            <CardContent className="p-4"><p className="text-sm text-slate-500">{k.label}</p><p className="text-2xl font-bold mt-1">{k.val}</p><p className="text-xs text-slate-400 mt-0.5">{k.sub}</p></CardContent>
          </Card>
        ))}
      </div>

      <Card className="border-[#E4ECFC]">
        <CardHeader className="pb-2 flex flex-row items-center justify-between">
          <CardTitle className="text-base">探测记录</CardTitle>
          <div className="flex gap-2">
            <Button variant="outline" size="sm">Provider A</Button>
            <Button variant="outline" size="sm">Provider B</Button>
            <Button variant="outline" size="sm">Provider C</Button>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          <table className="w-full text-sm">
            <thead><tr className="border-b border-slate-100 text-left text-xs font-medium text-slate-500 uppercase"><th className="p-3 pl-4">关键词</th><th className="p-3">平台</th><th className="p-3">可见</th><th className="p-3">引用</th><th className="p-3">排名</th><th className="p-3">分数</th><th className="p-3">时间</th><th className="p-3 pr-4">摘要</th></tr></thead>
            <tbody>
              {probes.map(p => (
                <tr key={p.id} className="border-b border-slate-50 hover:bg-slate-50">
                  <td className="p-3 pl-4 font-medium">{p.keyword}</td>
                  <td className="p-3"><span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${platformColors[p.platform] || ""}`}>{p.platform}</span></td>
                  <td className="p-3">{p.mentioned ? <CheckCircle2 className="h-4 w-4 text-emerald-600" /> : <XCircle className="h-4 w-4 text-slate-300" />}</td>
                  <td className="p-3">{p.cited ? <CheckCircle2 className="h-4 w-4 text-emerald-600" /> : <XCircle className="h-4 w-4 text-slate-300" />}</td>
                  <td className="p-3">{p.rank ? `#${p.rank}` : "-"}</td>
                  <td className="p-3"><span className={`font-medium ${p.score >= 80 ? "text-emerald-600" : p.score >= 50 ? "text-amber-600" : "text-red-500"}`}>{p.score}</span></td>
                  <td className="p-3 text-slate-500">{p.date}</td>
                  <td className="p-3 pr-4 text-slate-500 text-xs max-w-[200px] truncate">{p.snapshot}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  );
}

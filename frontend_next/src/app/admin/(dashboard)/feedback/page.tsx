"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { RefreshCw, ArrowRight, Zap, TrendingUp } from "lucide-react";

const cycles = [
  { id: 1, keyword: "长尾词覆盖工艺", genCount: 3, initScore: 62, lastScore: 94, improvement: "+32", labels: ["工程实践","标准文档"] },
  { id: 2, keyword: "引用率参数", genCount: 2, initScore: 58, lastScore: 87, improvement: "+29", labels: ["官方文档","测试数据"] },
  { id: 3, keyword: "核心关键词控制", genCount: 4, initScore: 71, lastScore: 96, improvement: "+25", labels: ["标准文档","失效案例","工程实践"] },
];

const recentFeedback = [
  { id: 1, keyword: "长尾词覆盖工艺", action: "外部平台尚未显著引用，建议增加 IPC 标准引用和工程实践案例", date: "05-06" },
  { id: 2, keyword: "引用率参数", action: "探测到 AI 引擎 B 提到品牌但未引用官网，建议在正文显式加入官网链接以提升引用率", date: "05-06" },
  { id: 3, keyword: "核心关键词控制", action: "AI 引擎 A 排名 #1 且引用官网，反馈标签已饱和，建议扩展衍生关键词", date: "05-05" },
];

export default function FeedbackPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">反馈闭环</h1>
        <p className="text-sm text-slate-500 mt-1">探测 → 分析 → 优化 Prompt → 再生 · 持续迭代提升 AI 可见性</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: "迭代周期", val: cycles.length, icon: RefreshCw },
          { label: "平均提升", val: "+28.7 分", icon: TrendingUp },
          { label: "活跃关键词", val: 3, icon: Zap },
          { label: "反馈标签", val: 12, icon: ArrowRight },
        ].map(k => (
          <Card key={k.label} className="border-[#E4ECFC]">
            <CardContent className="p-4 flex items-center gap-3">
              <k.icon className="h-8 w-8 text-blue-500/30" />
              <div><p className="text-2xl font-bold">{k.val}</p><p className="text-xs text-slate-500">{k.label}</p></div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card className="border-[#E4ECFC]">
          <CardHeader className="pb-2"><CardTitle className="text-base">迭代周期</CardTitle></CardHeader>
          <CardContent className="p-0">
            <table className="w-full text-sm">
              <thead><tr className="border-b border-slate-100 text-left text-xs font-medium text-slate-500 uppercase"><th className="p-3 pl-4">关键词</th><th className="p-3">代数</th><th className="p-3">初始分</th><th className="p-3">最新分</th><th className="p-3">提升</th><th className="p-3 pr-4">标签</th></tr></thead>
              <tbody>
                {cycles.map(c => (
                  <tr key={c.id} className="border-b border-slate-50">
                    <td className="p-3 pl-4 font-medium">{c.keyword}</td>
                    <td className="p-3 text-slate-500">gen-{c.genCount}</td>
                    <td className="p-3 text-red-500">{c.initScore}</td>
                    <td className="p-3 text-emerald-600 font-medium">{c.lastScore}</td>
                    <td className="p-3 text-emerald-600 font-medium">+{c.lastScore - c.initScore}</td>
                    <td className="p-3 pr-4">{c.labels.map(l => <span key={l} className="inline-flex px-1.5 py-0.5 rounded text-xs bg-slate-100 text-slate-600 mr-1">{l}</span>)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </CardContent>
        </Card>
        <Card className="border-[#E4ECFC]">
          <CardHeader className="pb-2"><CardTitle className="text-base">最近反馈</CardTitle></CardHeader>
          <CardContent>
            <div className="space-y-3">
              {recentFeedback.map(f => (
                <div key={f.id} className="flex gap-3 p-3 rounded-lg bg-slate-50">
                  <RefreshCw className="h-4 w-4 mt-0.5 text-blue-500 shrink-0" />
                  <div>
                    <span className="text-sm font-medium">{f.keyword}</span>
                    <span className="text-xs text-slate-400 ml-2">{f.date}</span>
                    <p className="text-sm text-slate-600 mt-0.5">{f.action}</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

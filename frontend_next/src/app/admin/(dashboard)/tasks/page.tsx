"use client";
import { Card, CardContent } from "@saasfly/ui/card";
import { Button } from "@saasfly/ui/button";
import { Plus, Play, Pause, Clock } from "lucide-react";

const tasks = [
  { id: 1, name: "关键词消费生产", schedule: "持续运行", daily: "3 篇/天", status: "running", last: "05-08 10:30" },
  { id: 2, name: "低分文章修复", schedule: "每小时", daily: "—", status: "running", last: "05-08 10:00" },
  { id: 3, name: "AI 平台探测", schedule: "每天 20:00", daily: "10 次", status: "paused", last: "05-07 20:00" },
  { id: 4, name: "官网 HTML 导出", schedule: "每天 06:00", daily: "5 篇/天", status: "running", last: "05-08 06:00" },
];

export default function TasksPage() {
  return (<div className="space-y-6">
    <div className="flex items-center justify-between"><div><h1 className="text-2xl font-bold tracking-tight text-slate-900">任务调度</h1><p className="text-sm text-slate-500 mt-1">定时任务 · 生成节奏 · 发布策略</p></div><Button className="bg-blue-600 hover:bg-blue-700"><Plus className="h-4 w-4 mr-2"/>新建任务</Button></div>
    <Card className="border-[#E4ECFC]"><CardContent className="p-0"><table className="w-full text-sm"><thead><tr className="border-b text-left text-xs font-medium text-slate-500 uppercase"><th className="p-3 pl-4">任务</th><th className="p-3">调度</th><th className="p-3">日产量</th><th className="p-3">状态</th><th className="p-3">上次运行</th><th className="p-3 pr-4">操作</th></tr></thead>
    <tbody>{tasks.map(t=><tr key={t.id} className="border-b border-slate-50 hover:bg-slate-50"><td className="p-3 pl-4 font-medium">{t.name}</td><td className="p-3 text-slate-500">{t.schedule}</td><td className="p-3">{t.daily}</td><td className="p-3"><span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${t.status==="running"?"bg-emerald-50 text-emerald-700":"bg-slate-100 text-slate-600"}`}>{t.status==="running"?"运行中":"已暂停"}</span></td><td className="p-3 text-slate-400 text-xs">{t.last}</td><td className="p-3 pr-4"><Button variant="ghost" size="sm">{t.status==="running"?<><Pause className="h-3.5 w-3.5 mr-1"/>暂停</>:<><Play className="h-3.5 w-3.5 mr-1"/>启动</>}</Button></td></tr>)}</tbody></table></CardContent></Card>
  </div>);
}

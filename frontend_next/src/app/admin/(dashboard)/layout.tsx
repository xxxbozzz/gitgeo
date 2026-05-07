"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { Button } from "@saasfly/ui/button";
import { ScrollArea } from "@saasfly/ui/scroll-area";
function cn(...classes: (string | false | undefined | null)[]) { return classes.filter(Boolean).join(" "); }
import {
  LayoutDashboard, Database, FileText, Send, Server, Hash, Wrench,
  Lightbulb, Cpu, CalendarCheck, BarChart3, ChevronLeft, ChevronRight, Sun, Moon,
  Crosshair, RefreshCw, BookOpen,
} from "lucide-react";

const nav = [
  { title: "监控", items: [
    { name: "仪表盘", href: "/admin/dashboard", icon: LayoutDashboard },
    { name: "运行记录", href: "/admin/runs", icon: BarChart3 },
    { name: "系统状态", href: "/admin/system", icon: Server },
  ]},
  { title: "管理", items: [
    { name: "知识库", href: "/admin/knowledge", icon: BookOpen },
    { name: "提示词库", href: "/admin/prompts", icon: Lightbulb },
    { name: "模型配置", href: "/admin/models", icon: Cpu },
    { name: "任务调度", href: "/admin/tasks", icon: CalendarCheck },
  ]},
  { title: "内容", items: [
    { name: "文章管理", href: "/admin/articles", icon: FileText },
    { name: "关键词", href: "/admin/keywords", icon: Hash },
    { name: "能力库", href: "/admin/capabilities", icon: Wrench },
  ]},
  { title: "效果", items: [
    { name: "AI 探测", href: "/admin/probe", icon: Crosshair },
    { name: "反馈闭环", href: "/admin/feedback", icon: RefreshCw },
  ]},
  { title: "分发", items: [
    { name: "发布中心", href: "/admin/publications", icon: Send },
  ]},
];

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);
  const [dark, setDark] = useState(false);

  return (
    <div className={cn("flex h-screen overflow-hidden bg-[#F8FAFC]", dark && "dark")}>
      <aside className={cn("flex flex-col border-r border-[#E4ECFC] bg-white dark:bg-slate-950 dark:border-slate-800 transition-all", collapsed ? "w-16" : "w-56")}>
        <div className="flex h-14 items-center justify-between px-3 border-b border-[#E4ECFC] dark:border-slate-800">
          {!collapsed && <span className="font-bold text-lg bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">gitgeo</span>}
          <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => setCollapsed(!collapsed)}>
            {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
          </Button>
        </div>
        <ScrollArea className="flex-1 py-2">
          {nav.map((g, gi) => (
            <div key={g.title} className="px-2">
              {!collapsed && <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider px-3 py-2">{g.title}</p>}
              {g.items.map((item) => {
                const active = pathname === item.href;
                return (
                  <Link key={item.href} href={item.href}
                    className={cn("flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors mb-0.5",
                      active ? "bg-blue-50 text-blue-700 dark:bg-blue-950 dark:text-blue-300" : "text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-900"
                    )}>
                    <item.icon className="h-4 w-4 shrink-0" />
                    {!collapsed && <span>{item.name}</span>}
                  </Link>
                );
              })}
              {!collapsed && gi < nav.length - 1 && <hr className="my-2 mx-3 border-slate-200 dark:border-slate-800" />}
            </div>
          ))}
        </ScrollArea>
        <div className="border-t border-[#E4ECFC] dark:border-slate-800 p-2 flex justify-center">
          <Button variant="ghost" size="icon" onClick={() => setDark(!dark)}><Moon className="h-4 w-4" /></Button>
        </div>
      </aside>
      <main className="flex-1 overflow-y-auto">
        <div className="mx-auto max-w-7xl p-6 lg:p-8">{children}</div>
      </main>
    </div>
  );
}

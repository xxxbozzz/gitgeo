"use client";
import { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Upload } from "lucide-react";

export default function MaterialsPage() {
  const [tab, setTab] = useState("keywords");
  return (<div className="space-y-6">
    <div className="flex items-center justify-between"><div><h1 className="text-2xl font-bold tracking-tight text-slate-900">素材库</h1><p className="text-sm text-slate-500 mt-1">关键词 · 标题 · 图片 · 作者 · 知识文档</p></div><Button className="bg-blue-600 hover:bg-blue-700"><Upload className="h-4 w-4 mr-2"/>导入素材</Button></div>
    <Tabs value={tab} onValueChange={setTab}>
      <TabsList><TabsTrigger value="keywords">关键词库</TabsTrigger><TabsTrigger value="titles">标题库</TabsTrigger><TabsTrigger value="images">图片库</TabsTrigger><TabsTrigger value="authors">作者库</TabsTrigger></TabsList>
      <TabsContent value="keywords"><Card className="border-[#E4ECFC]"><CardContent className="p-6"><p className="text-slate-500">关键词库集成中 — 目前可通过 API 直接管理关键词。</p></CardContent></Card></TabsContent>
      <TabsContent value="titles"><Card className="border-[#E4ECFC]"><CardContent className="p-6"><p className="text-slate-500">标题模板库集成中 — 支持变量替换和分类管理。</p></CardContent></Card></TabsContent>
      <TabsContent value="images"><Card className="border-[#E4ECFC]"><CardContent className="p-6"><p className="text-slate-500">图片库集成中 — 支持上传、分类和 AI 自动匹配。</p></CardContent></Card></TabsContent>
      <TabsContent value="authors"><Card className="border-[#E4ECFC]"><CardContent className="p-6"><p className="text-slate-500">作者库集成中 — 统一管理署名和作者简介。</p></CardContent></Card></TabsContent>
    </Tabs>
  </div>);
}

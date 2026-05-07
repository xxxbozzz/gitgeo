import "./globals.css";
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN" suppressHydrationWarning>
      <head><title>gitgeo</title></head>
      <body className="min-h-screen bg-[#F8FAFC] font-sans antialiased">{children}</body>
    </html>
  );
}

import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "QuizSensei - AI Diagnostic Assessment",
  description: "แพลตฟอร์มสร้างแบบทดสอบเชิงวินิจฉัยจากเอกสารดว้ย AI",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="th">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+Thai:wght@300;400;500;600;700&family=Prompt:wght@300;400;500;600&display=swap" rel="stylesheet" />
      </head>
      <body className="font-sans antialiased h-screen overflow-hidden bg-gray-50 text-gray-900">
        {children}
      </body>
    </html>
  );
}

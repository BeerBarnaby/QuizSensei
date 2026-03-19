"use client";

import { useAppStore } from '@/store/useAppStore';
import SourceList from '@/components/SourceList';
import SourceViewer from '@/components/SourceViewer';
import QuizGenerator from '@/components/QuizGenerator';

export default function Home() {
  return (
    <div className="flex h-screen bg-[#f7f7f9] text-gray-800">
      
      {/* Left Panel: Source Management */}
      <div className="w-[300px] flex-shrink-0 border-r border-gray-200 bg-white">
        <SourceList />
      </div>

      {/* Center Panel: Viewer and Editor */}
      <div className="flex-1 border-r border-gray-200 bg-white shadow-sm overflow-hidden z-10">
        <SourceViewer />
      </div>

      {/* Right Panel: Exam Generator and Results */}
      <div className="w-[400px] flex-shrink-0 bg-[#fafafa]">
        <QuizGenerator />
      </div>
      
    </div>
  );
}

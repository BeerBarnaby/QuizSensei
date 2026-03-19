"use client";

import { useAppStore } from '@/store/useAppStore';

export default function SourceViewer() {
  const { extractedText, sourceAnalysis } = useAppStore();

  return (
    <div className="flex flex-col h-full bg-white">
      <div className="p-4 border-b border-gray-100 bg-white sticky top-0 px-6">
        <h2 className="text-xl font-semibold text-gray-900">ตัวอ่านเอกสาร</h2>
        <p className="text-sm text-gray-500 mt-1">
          ระบบจะสกัดข้อความจากเอกสารเพื่อให้ AI วิเคราะห์
        </p>
      </div>
      
      <div className="flex-1 overflow-y-auto p-6 bg-white prose prose-sm max-w-none text-gray-700">
        {extractedText ? (
          <div className="whitespace-pre-wrap">{extractedText}</div>
        ) : (
          <div className="h-full flex items-center justify-center">
            <p className="text-gray-400">กรุณาอัปโหลดเอกสารเพื่ออ่านเนื้อหาที่สกัดได้</p>
          </div>
        )}
      </div>

      {sourceAnalysis && (
        <div className={`p-4 border-t ${
          sourceAnalysis.analysis_status === 'failed' || sourceAnalysis.status === 'error'
            ? 'bg-red-50 border-red-100' 
            : 'bg-blue-50 border-blue-100'
        }`}>
          <h3 className={`font-semibold text-sm ${
            sourceAnalysis.analysis_status === 'failed' || sourceAnalysis.status === 'error'
              ? 'text-red-900' 
              : 'text-blue-900'
          }`}>
            {sourceAnalysis.analysis_status === 'failed' || sourceAnalysis.status === 'error'
              ? '⚠️ การวิเคราะห์ขัดข้อง:' 
              : '✅ ผลการวิเคราะห์ Gatekeeper:'}
          </h3>
          <p className={`text-sm mt-1 ${
            sourceAnalysis.analysis_status === 'failed' || sourceAnalysis.status === 'error'
              ? 'text-red-800' 
              : 'text-blue-800'
          }`}>
            {sourceAnalysis.sufficiency_reason || sourceAnalysis.message}
          </p>
        </div>
      )}
    </div>
  );
}

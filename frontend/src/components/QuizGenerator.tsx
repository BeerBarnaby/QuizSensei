"use client";

import { useAppStore } from '@/store/useAppStore';
import { useAuthStore } from '@/store/useAuthStore';
import { SparklesIcon, CheckCircleIcon, ExclamationTriangleIcon } from '@heroicons/react/24/solid';
import { useState } from 'react';

// Maps to the strict 5 Thai levels required by the Agent
const AUDIENCE_OPTIONS = [
  { value: "ประถม", label: "ประถม (Primary)" },
  { value: "มัธยมต้น", label: "มัธยมต้น (Middle School)" },
  { value: "มัธยมปลาย", label: "มัธยมปลาย (High School)" },
  { value: "มหาวิทยาลัย", label: "มหาวิทยาลัย (University)" },
  { value: "วัยทำงาน", label: "วัยทำงาน (Working Adult)" },
];

const DIFFICULTY_OPTIONS = [
  { value: "ง่าย", label: "ง่าย (Remember/Understand)" },
  { value: "ปานกลาง", label: "ปานกลาง (Apply/Analyze)" },
  { value: "ยาก", label: "ยาก (Evaluate/Create)" },
];

export default function QuizGenerator() {
  const { currentSourceId, isProcessing, setProcessing, quizResult, setQuizResult } = useAppStore();
  
  const [audience, setAudience] = useState("มัธยมปลาย");
  const [difficulty, setDifficulty] = useState("ปานกลาง");
  const [numQuestions, setNumQuestions] = useState(5);
  const [errorMsg, setErrorMsg] = useState("");

  const handleGenerate = async () => {
    if (!currentSourceId) {
      setErrorMsg("กรุณาเลือกเอกสารอ้างอิงจากแถบด้านซ้ายก่อน");
      return;
    }
    setErrorMsg("");
    setProcessing(true);
    setQuizResult(null);

    const token = useAuthStore.getState().token;

    try {
      // Calls Phase 3 Generation API (Agent 2 -> Agent 3 Loop)
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/teacher/${currentSourceId}/generate-questions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token && { 'Authorization': `Bearer ${token}` })
        },
        body: JSON.stringify({
          number_of_questions: numQuestions,
          target_audience_level: audience,
          difficulty_filter: difficulty,
        })
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "เกิดข้อผิดพลาดในการสร้างข้อสอบ");
      }

      const data = await res.json();
      setQuizResult(data);
    } catch (err: any) {
      setErrorMsg(err.message);
    } finally {
      setProcessing(false);
    }
  };

  return (
    <div className="flex flex-col h-full">
      <div className="p-5 border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900">สร้างแบบทดสอบ</h2>
        <p className="text-sm text-gray-500 mt-1">ตั้งค่าและระบุระดับผู้เรียน</p>
      </div>

      <div className="flex-1 overflow-y-auto p-5 space-y-6">
        
        {/* Settings Form */}
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              ระดับผู้เรียนที่เหมาะสม
            </label>
            <select 
              value={audience} 
              onChange={e => setAudience(e.target.value)}
              className="w-full rounded-md border-gray-300 shadow-sm px-3 py-2 text-sm focus:ring-indigo-500 focus:border-indigo-500 border bg-white"
            >
              {AUDIENCE_OPTIONS.map(opt => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              ระดับความยาก (อิงตาม Bloom's)
            </label>
            <select 
              value={difficulty}
              onChange={e => setDifficulty(e.target.value)}
              className="w-full rounded-md border-gray-300 shadow-sm px-3 py-2 text-sm focus:ring-indigo-500 focus:border-indigo-500 border bg-white"
            >
              {DIFFICULTY_OPTIONS.map(opt => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              จำนวนข้อสอบ
            </label>
            <input 
              type="number" 
              value={numQuestions}
              onChange={e => setNumQuestions(Number(e.target.value))}
              min={1} 
              max={20}
              className="w-full rounded-md border-gray-300 shadow-sm px-3 py-2 text-sm focus:ring-indigo-500 focus:border-indigo-500 border bg-white"
            />
          </div>
        </div>

        {errorMsg && (
          <div className="p-3 bg-red-50 text-red-700 text-sm rounded-md border border-red-200 flex items-start gap-2">
            <ExclamationTriangleIcon className="w-5 h-5 flex-shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        <button
          onClick={handleGenerate}
          disabled={isProcessing || !currentSourceId}
          className="w-full flex items-center justify-center gap-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white py-3 rounded-lg font-semibold transition-all shadow-md active:scale-[0.98] disabled:opacity-50"
        >
          <SparklesIcon className="w-5 h-5 text-yellow-300" />
          {isProcessing ? 'กำลังสร้างข้อสอบ...' : 'เริ่มสร้างข้อสอบ (Zero-Hallucination)'}
        </button>

        {/* Results Overview Placeholder */}
        <div className="pt-4 border-t border-gray-200">
          {!quizResult ? (
            <div className="bg-gray-50 border border-dashed border-gray-300 rounded-lg p-6 text-center text-sm text-gray-500">
              แบบทดสอบที่ผ่านการ Audit จะปรากฏที่นี่ <br/> 
              พร้อมคำเฉลยและอ้างอิงจากต้นฉบับ
            </div>
          ) : (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4 space-y-2">
              <div className="flex items-center gap-2 text-green-800 font-semibold">
                <CheckCircleIcon className="w-5 h-5" />
                <span>สร้างข้อสอบสำเร็จแล้ว!</span>
              </div>
              <p className="text-sm text-green-700">
                ระบบ (Agent 3) ได้อนุมัติข้อสอบจำนวน {quizResult.total_approved} ข้อ และปฏิเสธข้อสอบที่ไม่ตรงเกณฑ์ {quizResult.total_rejected} ข้อ (จากทั้งหมด {quizResult.total_generated} ข้อ)
              </p>
              <div className="mt-4 pt-3 border-t border-green-200 text-sm">
                <p className="font-medium text-gray-800">ตัวอย่างข้อที่ 1:</p>
                <div className="mt-2 bg-white rounded p-3 border border-gray-200 shadow-sm">
                  <p className="font-semibold">{quizResult.questions?.[0]?.stem}</p>
                  <ul className="mt-2 space-y-1 text-gray-600">
                    {quizResult.questions?.[0]?.choices?.map((c: any) => (
                      <li key={c.key} className={c.key === quizResult.questions?.[0]?.correct_answer ? "text-green-600 font-medium" : ""}>
                         {c.key}. {c.text}
                      </li>
                    ))}
                  </ul>
                  <div className="mt-3 p-2 bg-gray-50 rounded text-xs text-gray-500">
                    <strong>อ้างอิงเนื้อหา:</strong> {quizResult.questions?.[0]?.source_evidence}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

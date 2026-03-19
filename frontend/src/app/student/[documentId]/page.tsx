"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { CheckCircleIcon, XCircleIcon } from "@heroicons/react/24/solid";

interface Question {
  question_id: string;
  question_text: string;
  options: Record<string, string>;
  topic: string;
  subtopic: string;
  difficulty: string;
}

interface GraderOutput {
  question_id: string;
  is_correct: boolean;
  correct_answer: string;
  misconception_identified?: string;
  diagnostic_message: string;
  suggested_review_topic?: string;
}

export default function StudentQuizPage() {
  const params = useParams();
  const documentId = params.documentId as string;

  const [questions, setQuestions] = useState<Question[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [selectedKey, setSelectedKey] = useState<string>("");
  const [feedback, setFeedback] = useState<GraderOutput | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");

  useEffect(() => {
    if (!documentId) return;
    fetch(`http://localhost:8000/assessment/${documentId}/questions`)
      .then(res => {
        if (!res.ok) throw new Error("ไม่พบข้อสอบสำหรับเอกสารนี้");
        return res.json();
      })
      .then(data => {
        setQuestions(data);
        setLoading(false);
      })
      .catch(err => {
        setErrorMsg(err.message);
        setLoading(false);
      });
  }, [documentId]);

  const handleSubmit = async () => {
    if (!selectedKey) return;
    setSubmitting(true);
    setErrorMsg("");

    const currentQ = questions[currentIndex];

    try {
      const res = await fetch(`http://localhost:8000/assessment/${documentId}/questions/${currentQ.question_id}/submit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ selected_key: selectedKey }),
      });
      
      if (!res.ok) throw new Error("ส่งคำตอบไม่สำเร็จ");
      const data = await res.json();
      setFeedback(data);
    } catch (err: any) {
      setErrorMsg(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  const handleNext = () => {
    if (currentIndex < questions.length - 1) {
      setCurrentIndex(curr => curr + 1);
      setSelectedKey("");
      setFeedback(null);
    }
  };

  if (loading) return <div className="p-10 text-center">กำลังโหลดข้อสอบ...</div>;
  if (errorMsg && questions.length === 0) return <div className="p-10 text-center text-red-600">{errorMsg}</div>;
  if (questions.length === 0) return <div className="p-10 text-center">ยังไม่มีข้อสอบ</div>;

  const currentQ = questions[currentIndex];

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col pt-10 px-4 items-center">
      <div className="w-full max-w-2xl bg-white shadow-md rounded-xl p-8">
        
        <div className="flex justify-between items-center border-b pb-4 mb-6">
          <h1 className="text-xl font-bold text-gray-800">ทำแบบทดสอบอัตโนมัติ (QuizSensei)</h1>
          <span className="text-sm font-medium text-blue-600 bg-blue-100 px-3 py-1 rounded-full">
            ข้อที่ {currentIndex + 1} / {questions.length}
          </span>
        </div>

        <div className="mb-6">
          <span className="text-xs font-semibold text-gray-400 uppercase tracking-wide">
            {currentQ.topic} ({currentQ.difficulty})
          </span>
          <h2 className="text-lg font-medium text-gray-900 mt-2 leading-relaxed">
            {currentQ.question_text}
          </h2>
        </div>

        <div className="space-y-3">
          {Object.entries(currentQ.options).map(([key, text]) => {
            const isSelected = selectedKey === key;
            const isSubmitted = feedback !== null;
            const isCorrectAnswer = feedback?.correct_answer === key;
            
            let btnClass = "w-full text-left px-5 py-4 border rounded-lg transition-all ";
            
            if (isSubmitted) {
              if (isCorrectAnswer) btnClass += "border-green-500 bg-green-50 text-green-800";
              else if (isSelected && !isCorrectAnswer) btnClass += "border-red-500 bg-red-50 text-red-800";
              else btnClass += "border-gray-200 text-gray-500 opacity-50";
            } else {
              if (isSelected) btnClass += "border-blue-500 bg-blue-50 ring-2 ring-blue-200";
              else btnClass += "border-gray-200 hover:border-blue-300 hover:bg-gray-50";
            }

            return (
              <button
                key={key}
                disabled={isSubmitted}
                onClick={() => setSelectedKey(key)}
                className={btnClass}
              >
                <div className="flex items-center gap-3">
                  <span className="font-semibold">{key}.</span>
                  <span>{String(text)}</span>
                </div>
              </button>
            );
          })}
        </div>

        {errorMsg && <p className="text-red-600 text-sm mt-4">{errorMsg}</p>}

        {feedback && (
          <div className={`mt-6 p-5 rounded-lg border ${feedback.is_correct ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}`}>
            <h3 className={`font-bold flex items-center gap-2 ${feedback.is_correct ? 'text-green-700' : 'text-red-700'}`}>
              {feedback.is_correct ? <CheckCircleIcon className="w-5 h-5"/> : <XCircleIcon className="w-5 h-5"/>}
              {feedback.is_correct ? "ยอดเยี่ยม! คุณตอบถูก" : "ยังไม่ถูกต้อง (Agent 4 Feedback)"}
            </h3>
            <p className="mt-3 text-sm text-gray-700 whitespace-pre-wrap leading-relaxed">
              {feedback.diagnostic_message}
            </p>
            {feedback.suggested_review_topic && (
              <div className="mt-3 text-xs bg-white p-2 rounded shadow-sm border border-orange-100 text-orange-800 inline-block">
                <strong>หัวข้อที่ควรทบทวน:</strong> {feedback.suggested_review_topic}
              </div>
            )}
          </div>
        )}

        <div className="mt-8 flex justify-end">
          {!feedback ? (
            <button
              onClick={handleSubmit}
              disabled={submitting || !selectedKey}
              className="px-6 py-2.5 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 disabled:bg-gray-300 transition-colors"
            >
              {submitting ? "กำลังตรวจคำตอบ..." : "ส่งคำตอบ"}
            </button>
          ) : currentIndex < questions.length - 1 ? (
            <button
              onClick={handleNext}
              className="px-6 py-2.5 bg-gray-800 text-white font-medium rounded-lg hover:bg-gray-900 transition-colors"
            >
              ข้อถัดไป
            </button>
          ) : (
            <div className="px-6 py-2.5 bg-green-600 text-white font-medium rounded-lg">
              จบแบบทดสอบ
            </div>
          )}
        </div>

      </div>
    </div>
  );
}

"use client";

import { DocumentArrowUpIcon, DocumentTextIcon, ArrowPathIcon } from '@heroicons/react/24/outline';
import { useAppStore } from '@/store/useAppStore';
import { useEffect, useRef, useState } from 'react';

export default function SourceList() {
  const { documents, setDocuments, setCurrentSourceId, setExtractedText, setSourceAnalysis, setQuizResult, isProcessing, setProcessing } = useAppStore();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [errorMsg, setErrorMsg] = useState("");

  const fetchDocuments = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/v1/teacher/');
      if (res.ok) {
        const data = await res.json();
        setDocuments(data);
      }
    } catch (err) {
      console.error("Failed to fetch docs", err);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setErrorMsg("");
    setProcessing(true);
    setCurrentSourceId(null);
    setExtractedText("");
    setSourceAnalysis(null);
    setQuizResult(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      // 1. Upload
      const uploadRes = await fetch('http://localhost:8000/api/v1/teacher/upload', {
        method: 'POST',
        body: formData
      });
      if (!uploadRes.ok) throw new Error("Upload failed");
      const uploadData = await uploadRes.json();
      const docId = uploadData.id || uploadData.saved_as;

      // Refresh list
      await fetchDocuments();

      // 2. Extract Text
      const extractRes = await fetch(`http://localhost:8000/api/v1/teacher/${docId}/extract`, { method: 'POST' });
      if (!extractRes.ok) throw new Error("Extraction failed");
      
      const contentRes = await fetch(`http://localhost:8000/api/v1/teacher/${docId}/content`);
      const contentData = await contentRes.json();
      setExtractedText(contentData.extracted_text || "");

      // 3. Analyze (Agent 1 Gatekeeper)
      const analyzeRes = await fetch(`http://localhost:8000/api/v1/teacher/${docId}/analyze`, { method: 'POST' });
      if (!analyzeRes.ok) throw new Error("Analysis failed");
      const analysisData = await analyzeRes.json();
      setSourceAnalysis(analysisData);

      setCurrentSourceId(docId);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to process document");
    } finally {
      setProcessing(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const handleSelectDocument = async (docId: string) => {
    setCurrentSourceId(docId);
    setProcessing(true);
    setExtractedText("");
    setSourceAnalysis(null);
    setQuizResult(null);
    setErrorMsg("");

    try {
      // Try to load text
      const contentRes = await fetch(`http://localhost:8000/api/v1/teacher/${docId}/content`);
      if (contentRes.ok) {
        const contentData = await contentRes.json();
        setExtractedText(contentData.extracted_text || "");
      }

      // Try to load analysis
      const analyzeRes = await fetch(`http://localhost:8000/api/v1/teacher/${docId}/analysis`);
      if (analyzeRes.ok) {
        const analyzeData = await analyzeRes.json();
        setSourceAnalysis(analyzeData);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setProcessing(false);
    }
  };

  return (
    <div className="flex flex-col h-full">
      <div className="p-4 border-b border-gray-100 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900 tracking-tight">QuizSensei</h2>
        <span className="text-xs bg-blue-100 text-blue-700 font-medium px-2 py-1 rounded-full">Gatekeeper</span>
      </div>
      
      <div className="p-4">
        <input 
          type="file" 
          ref={fileInputRef} 
          onChange={handleFileUpload} 
          className="hidden" 
          accept=".pdf,.txt,.docx,.png,.jpg,.jpeg"
        />
        <button 
          onClick={() => fileInputRef.current?.click()}
          className="w-full flex items-center justify-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white py-2.5 rounded-lg font-medium transition-colors shadow-sm disabled:opacity-50"
          disabled={isProcessing}
        >
          {isProcessing ? (
             <><ArrowPathIcon className="w-5 h-5 animate-spin" /> กำลังประมวลผล...</>
          ) : (
             <><DocumentArrowUpIcon className="w-5 h-5" /> อัปโหลดแหล่งข้อมูล</>
          )}
        </button>
        {errorMsg && <p className="text-xs text-red-600 mt-2">{errorMsg}</p>}
      </div>

      <div className="flex-1 overflow-y-auto p-4 pt-0">
        <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
          ไฟล์ที่เลือก
        </h3>
        
        {documents.length === 0 ? (
          <div className="text-center py-8 text-gray-400 text-sm">
            <DocumentTextIcon className="w-10 h-10 mx-auto mb-2 opacity-50" />
            ยังไม่มีเอกสาร อัปโหลดเพื่อเริ่มต้น
          </div>
        ) : (
          <ul className="space-y-2">
            {documents.map((doc, idx) => (
              <li 
                key={idx} 
                onClick={() => handleSelectDocument(doc.id || doc.document_id)}
                className="flex items-start gap-3 p-3 rounded-lg hover:bg-gray-50 cursor-pointer border border-transparent hover:border-gray-200 transition-all active:bg-gray-100"
              >
                <DocumentTextIcon className="w-5 h-5 text-indigo-500 mt-0.5 flex-shrink-0" />
                <div className="flex-1 min-w-0 overflow-hidden">
                  <p className="text-sm font-medium text-gray-900 truncate" title={doc.filename}>{doc.filename}</p>
                  <p className="text-xs text-gray-500">
                    {doc.size_bytes ? (doc.size_bytes / 1024).toFixed(1) + ' KB' : ''} 
                    {doc.extraction_state ? ` • ${doc.extraction_state}` : ''}
                  </p>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

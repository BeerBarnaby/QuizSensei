import { useState, useEffect, useRef } from 'react'
import { apiClient } from './api'
import './App.css'

function App() {
  const [sources, setSources] = useState([])
  const [selectedIds, setSelectedIds] = useState([])
  const [selectedIndicators, setSelectedIndicators] = useState([])
  const [activeSource, setActiveSource] = useState(null)
  const [editingText, setEditingText] = useState('')
  const [isEditing, setIsEditing] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const fileInputRef = useRef(null)

  const [audience, setAudience] = useState('วัยทำงาน')
  const [questions, setQuestions] = useState([])
  const [genLoading, setGenLoading] = useState(false)
  const [chatMessage, setChatMessage] = useState('')
  const [chatLoading, setChatLoading] = useState(false)
  
  // Student Quiz State
  const [isQuizMode, setIsQuizMode] = useState(false)
  const [quizQuestions, setQuizQuestions] = useState([])
  const [currentQuizIndex, setCurrentQuizIndex] = useState(0)
  const [quizFeedback, setQuizFeedback] = useState(null)
  const [quizLoading, setQuizLoading] = useState(false)

  const handleExport = async (format) => {
    if (!activeSource) return
    try {
      const blob = await apiClient.exportQuiz(activeSource.id, format)
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `quiz_${activeSource.id}.${format === 'moodle' ? 'xml' : 'json'}`
      document.body.appendChild(a)
      a.click()
      a.remove()
    } catch (err) {
      setError('Export failed.')
    }
  }

  const handleChat = async () => {
    if (!chatMessage.trim() || !activeSource) return
    setChatLoading(true)
    setTimeout(() => {
       alert(`AI Assistant: You asked about "${chatMessage}". In the next version, I will provide specific answers directly from the context of ${activeSource.name}.`)
       setChatMessage('')
       setChatLoading(false)
    }, 1000)
  }

  const handleGenerate = async () => {
    if (!activeSource) return
    setGenLoading(true)
    setQuestions([])
    setError(null)
    try {
      const result = await apiClient.generateQuestions(activeSource.id, {
        target_audience_level: audience,
        number_of_questions: 5,
        selected_indicators: selectedIndicators
      })
      if (result.questions) {
        setQuestions(result.questions)
      } else {
        setError('Generation failed')
      }
    } catch (err) {
      setError('Connection error or generation failure.')
    } finally {
      setGenLoading(false)
    }
  }

  const handleBatchExtract = async () => {
    if (selectedIds.length === 0) return
    setLoading(true)
    setError(null)
    try {
      const results = await apiClient.extractBatch(selectedIds)
      setSources(prev => prev.map(s => {
        const res = results.find(r => r.document_id === s.id)
        return res ? { ...s, status: res.extraction_status, char_count: res.char_count } : s
      }))
    } catch (err) {
      setError('Batch extraction failed.')
    } finally {
      setLoading(false)
    }
  }

  const handleSaveContent = async () => {
    if (!activeSource || !editingText) return
    setLoading(true)
    try {
      await apiClient.updateDocumentContent(activeSource.id, editingText)
      setIsEditing(false)
      // Trigger analysis after manual edit
      triggerAnalysis(activeSource.id)
    } catch (err) {
      setError('Failed to save content.')
    } finally {
      setLoading(false)
    }
  }

  const triggerAnalysis = async (docId) => {
    try {
      setSources(prev => prev.map(s => s.id === docId ? { ...s, status: 'analyzing' } : s))
      const result = await apiClient.analyzeDocument(docId)
      setSources(prev => prev.map(s => 
        s.id === docId ? { ...s, analysis: result, status: 'analyzed' } : s
      ))
    } catch (err) {
      setError('Analysis failed.')
      setSources(prev => prev.map(s => s.id === docId ? { ...s, status: 'error' } : s))
    }
  }

  const toggleSelection = (id) => {
    setSelectedIds(prev => prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id])
  }

  const toggleIndicator = (id) => {
    setSelectedIndicators(prev => prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id])
  }

  const handleUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    setLoading(true)
    setError(null)
    try {
      const result = await apiClient.uploadFile(file, audience)
      if (result.saved_as) {
        const docId = result.saved_as
        const newSource = { id: docId, name: file.name, status: 'uploaded' }
        setSources(prev => [...prev, newSource])
      } else {
        setError('Upload failed')
      }
    } catch (err) {
      setError('Connection error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <div className="sidebar">
        <div className="logo" style={{ cursor: 'pointer' }} onClick={() => { setActiveSource(null); setQuestions([]); }}>
          <span style={{ fontSize: '1.6rem' }}>🧠</span>
          <span style={{ letterSpacing: '-0.5px' }}>QuizSensei</span>
        </div>
        
        <p className="source-header">Sources</p>
        <div className="source-list">
          {sources.map(s => (
            <div 
              key={s.id} 
              className={`source-item ${activeSource?.id === s.id ? 'active' : ''}`}
            >
              <input 
                type="checkbox" 
                checked={selectedIds.includes(s.id)}
                onChange={() => toggleSelection(s.id)}
                style={{ marginRight: '8px' }}
              />
              <span onClick={() => { setActiveSource(s); setQuestions([]); setIsEditing(false); }}>
                {s.status === 'analyzed' ? '✨' : s.error ? '❌' : s.status === 'success' ? '📝' : '⏳'}
              </span>
              <span className="source-name" title={s.name} onClick={() => { setActiveSource(s); setQuestions([]); setIsEditing(false); }}>
                {s.name}
              </span>
            </div>
          ))}
          {sources.length === 0 && <p style={{ padding: '0 12px', color: '#999', fontSize: '0.8rem', fontStyle: 'italic' }}>Drop documents here</p>}
        </div>

        <input 
          type="file" 
          ref={fileInputRef} 
          style={{ display: 'none' }} 
          onChange={handleUpload}
          accept=".pdf,.docx,.txt,image/*"
        />
        
        <button 
          className="upload-btn" 
          onClick={() => fileInputRef.current?.click()}
          disabled={loading}
        >
          {loading ? 'Preparing...' : '＋ Add Source'}
        </button>

        <button 
          className="primary-action-btn" 
          style={{ width: '100%', marginTop: '12px' }}
          onClick={handleBatchExtract}
          disabled={selectedIds.length === 0 || loading}
        >
          {loading ? 'Processing...' : `Extract Selected (${selectedIds.length})`}
        </button>
      </div>

      <div className="main-content">
        {!activeSource ? (
          <div className="welcome-screen">
            <div className="welcome-icon">🎓</div>
            <h1>Empower your teaching</h1>
            <p>Upload lecture notes or research papers. Our AI will analyze the pedagogical structure and craft meaningful assessments in seconds.</p>
          </div>
        ) : (
          <div className="document-workspace fade-in">
            <div className="workspace-header">
              <h2>{activeSource.name}</h2>
              <div style={{ display: 'flex', gap: '8px' }}>
                {activeSource.status === 'analyzed' && <span className="badge">Analyzed</span>}
                <button 
                  className="secondary-action-btn"
                  onClick={() => handleExport('moodle')}
                  disabled={questions.length === 0}
                >
                  Export XML
                </button>
              </div>
            </div>

            <div className="analytical-view">
              {isEditing ? (
                <div className="edit-container fade-in">
                  <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                    <h3 style={{ margin: 0 }}>Edit Content</h3>
                    <div style={{ display: 'flex', gap: '8px' }}>
                      <button className="secondary-action-btn" onClick={() => setIsEditing(false)}>Cancel</button>
                      <button className="primary-action-btn" style={{ padding: '8px 20px' }} onClick={handleSaveContent}>Save & Analyze</button>
                    </div>
                  </header>
                  <textarea 
                    className="content-editor"
                    value={editingText}
                    onChange={(e) => setEditingText(e.target.value)}
                    placeholder="Extracted text will appear here for you to edit..."
                  />
                </div>
              ) : activeSource.status === 'analyzed' ? (
                <div className="analysis-card">
                  <header>
                    <div className="topic-block">
                      <span className="label">Topic</span>
                      <h3>{activeSource.analysis.topic}</h3>
                      <p>{activeSource.analysis.subtopic}</p>
                    </div>
                    <div className="level-block">
                      <span className="label">Difficulty</span>
                      <div className="level-val">{activeSource.analysis.suggested_learner_level}</div>
                    </div>
                  </header>

                  <section className="insight-section">
                    <p>{activeSource.analysis.learner_level_reason}</p>
                  </section>

                  <section className="tags-section">
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                      <h4>Key Concepts</h4>
                      <button 
                        className="secondary-action-btn" 
                        style={{ fontSize: '0.75rem' }}
                        onClick={async () => {
                          const content = await apiClient.getDocumentContent(activeSource.id);
                          setEditingText(content.extracted_text);
                          setIsEditing(true);
                        }}
                      >
                        ✏️ Edit Source Text
                      </button>
                    </div>
                    <div className="tag-cloud">
                      {activeSource.analysis.keywords_found?.map((k, i) => (
                        <span key={i} className="tag">{k}</span>
                      ))}
                    </div>
                  </section>

                  <section className="indicators-section" style={{ marginTop: '32px' }}>
                    <h4 style={{ marginBottom: '16px', color: 'var(--text-secondary)' }}>Selected Indicators for Quiz</h4>
                    <div className="indicator-grid">
                      {activeSource.analysis.indicators?.map((ind) => (
                        <div 
                          key={ind.id} 
                          className={`indicator-card ${selectedIndicators.includes(ind.id) ? 'selected' : ''}`}
                          onClick={() => toggleIndicator(ind.id)}
                        >
                          <div className="ind-id">{ind.id}</div>
                          <p className="ind-text">{ind.text}</p>
                          <span className="ind-relevance">{ind.relevance}</span>
                        </div>
                      ))}
                      {(!activeSource.analysis.indicators || activeSource.analysis.indicators.length === 0) && (
                        <p style={{ fontSize: '0.85rem', color: '#999', fontStyle: 'italic' }}>No indicators extracted. Try editing the text and re-analyzing.</p>
                      )}
                    </div>
                  </section>
                </div>
              ) : (
                <div className="pipeline-loading">
                  <div className="spinner"></div>
                  <p>
                    {activeSource.status === 'extracting' ? 'Reading document...' : 
                     activeSource.status === 'analyzing' ? 'AI is analyzing content...' : 
                     activeSource.status === 'success' ? 'Extraction complete. Ready for analysis.' : 
                     'Waiting for extraction...'}
                  </p>
                  {activeSource.status === 'success' && (
                    <button 
                      className="primary-action-btn" 
                      style={{ marginTop: '20px', width: 'auto' }}
                      onClick={async () => {
                        const content = await apiClient.getDocumentContent(activeSource.id);
                        setEditingText(content.extracted_text);
                        setIsEditing(true);
                      }}
                    >
                      View & Edit Text
                    </button>
                  )}
                </div>
              )}
            </div>

            <div className="context-action-bar">
              <input 
                type="text" 
                placeholder="Ask AI about this document..." 
                value={chatMessage}
                onChange={(e) => setChatMessage(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleChat()}
              />
              <button 
                className="send-btn" 
                onClick={handleChat}
                disabled={chatLoading}
              >
                {chatLoading ? '...' : (
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>
                )}
              </button>
            </div>
          </div>
        )}
      </div>

      <div className="workbench">
        <div style={{ marginBottom: '24px' }}>
          <h3 style={{ fontSize: '1rem', fontWeight: '700', color: 'var(--text-primary)' }}>Quiz Engine</h3>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Configure and generate assessments.</p>
        </div>

        <div className="config-card">
          <div className="field">
            <label>TARGET AUDIENCE</label>
            <select value={audience} onChange={e => setAudience(e.target.value)}>
              <option>ประถม</option>
              <option>มัธยมต้น</option>
              <option>มัธยมปลาย</option>
              <option>มหาวิทยาลัย</option>
              <option>วัยทำงาน</option>
            </select>
          </div>
          
          <button 
            className="primary-action-btn"
            onClick={handleGenerate}
            disabled={activeSource?.status !== 'analyzed' || genLoading}
          >
            {genLoading ? 'Thinking...' : 'Generate Quiz'}
          </button>

          <button 
            className="secondary-action-btn"
            style={{ width: '100%', marginTop: '12px', borderColor: 'var(--accent-primary)', color: 'var(--accent-primary)' }}
            onClick={handleTakeQuiz}
            disabled={activeSource?.status !== 'analyzed' || quizLoading}
          >
            {quizLoading ? 'Loading Quiz...' : '🎯 Take Student Quiz'}
          </button>
        </div>

        <div className="workbench-status">
          <p className="status-label">Questions ({questions.length})</p>
          <div className="questions-scroll">
            {questions.map((q, i) => (
              <div key={i} className="q-card fade-in">
                <div className="q-meta">
                  <span className="q-type">{q.metadata?.cognitive_level || 'Bloom'}</span>
                  <span className="q-id">#0{i+1}</span>
                </div>
                <p className="q-text">{q.question_text}</p>
                <div className="q-options-hint">{q.distractors?.length + 1} options drafted</div>
              </div>
            ))}
            {questions.length === 0 && !genLoading && (
              <div className="empty-workbench">
                <span>0</span>
              </div>
            )}
            {genLoading && (
              <div className="loading-skeletons">
                <div className="skeleton-item"></div>
                <div className="skeleton-item short"></div>
              </div>
            )}
          </div>
        </div>
      </div>

      {isQuizMode && (
        <div className="quiz-overlay fade-in">
          <div className="quiz-modal">
            <header className="quiz-header">
              <div className="quiz-progress">
                Question {currentQuizIndex + 1} of {quizQuestions.length}
              </div>
              <button className="close-btn" onClick={() => setIsQuizMode(false)}>✕</button>
            </header>

            <div className="quiz-body">
              <div className="q-card-large">
                <div className="q-topic-tag">{quizQuestions[currentQuizIndex]?.topic}</div>
                <h2 className="q-text-large">{quizQuestions[currentQuizIndex]?.question_text}</h2>
                
                <div className="options-list-large">
                  {Object.entries(quizQuestions[currentQuizIndex]?.options || {}).map(([key, text]) => (
                    <button 
                      key={key}
                      className={`option-item-large ${quizFeedback ? (quizFeedback.correct_answer === key ? 'correct' : 'incorrect') : ''}`}
                      onClick={() => !quizFeedback && handleSubmitAnswer(key)}
                      disabled={!!quizFeedback}
                    >
                      <span className="option-letter">{key}</span>
                      <span className="option-text">{text}</span>
                    </button>
                  ))}
                </div>

                {quizFeedback && (
                  <div className="diagnostic-feedback fade-in">
                    <div className={`feedback-banner ${quizFeedback.is_correct ? 'success' : 'warning'}`}>
                      {quizFeedback.is_correct ? '✨ Correct!' : '🤔 Not quite...'}
                    </div>
                    <div className="feedback-content">
                      <pre style={{ whiteSpace: 'pre-wrap', fontFamily: 'inherit' }}>{quizFeedback.diagnostic_message}</pre>
                      {quizFeedback.suggested_review_topic && (
                        <div className="review-suggestion">
                          <strong>Suggested Review:</strong> {quizFeedback.suggested_review_topic}
                        </div>
                      )}
                    </div>
                    <button 
                      className="primary-action-btn" 
                      style={{ marginTop: '20px' }}
                      onClick={() => {
                        if (currentQuizIndex < quizQuestions.length - 1) {
                          setCurrentQuizIndex(prev => prev + 1)
                          setQuizFeedback(null)
                        } else {
                          setIsQuizMode(false)
                        }
                      }}
                    >
                      {currentQuizIndex < quizQuestions.length - 1 ? 'Next Question' : 'Finish Quiz'}
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  )
}

export default App

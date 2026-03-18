import { useState, useEffect, useRef } from 'react'
import { apiClient } from './api'
import './App.css'

function App() {
  const [sources, setSources] = useState([])
  const [activeSource, setActiveSource] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const fileInputRef = useRef(null)

  const [audience, setAudience] = useState('วัยทำงาน')
  const [questions, setQuestions] = useState([])
  const [genLoading, setGenLoading] = useState(false)
  const [chatMessage, setChatMessage] = useState('')
  const [chatLoading, setChatLoading] = useState(false)

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
        number_of_questions: 5
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

  const triggerPipeline = async (docId) => {
    try {
      setSources(prev => prev.map(s => s.id === docId ? { ...s, status: 'extracting' } : s))
      await apiClient.extractDocument(docId)
      setSources(prev => prev.map(s => s.id === docId ? { ...s, status: 'analyzing' } : s))
      const analysisResult = await apiClient.analyzeDocument(docId)
      setSources(prev => prev.map(s => 
        s.id === docId ? { ...s, analysis: analysisResult, status: 'analyzed' } : s
      ))
    } catch (err) {
      console.error('Pipeline failed', err)
      setSources(prev => prev.map(s => s.id === docId ? { ...s, status: 'error' } : s))
    }
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
        const newSource = { id: docId, name: file.name, status: 'uploading' }
        setSources(prev => [...prev, newSource])
        setActiveSource(newSource)
        triggerPipeline(docId)
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
              onClick={() => { setActiveSource(s); setQuestions([]); }}
            >
              <span>{s.status === 'analyzed' ? '✨' : s.error ? '❌' : '⏳'}</span>
              <span className="source-name" title={s.name}>{s.name}</span>
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
              {activeSource.status === 'analyzed' ? (
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
                    <h4>Key Concepts</h4>
                    <div className="tag-cloud">
                      {activeSource.analysis.keywords_found?.map((k, i) => (
                        <span key={i} className="tag">{k}</span>
                      ))}
                    </div>
                  </section>
                </div>
              ) : (
                <div className="pipeline-loading">
                  <div className="spinner"></div>
                  <p>{activeSource.status === 'extracting' ? 'Reading document...' : 'AI is analyzing content...'}</p>
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
    </>
  )
}

export default App

import { useState, useEffect, useRef } from 'react'
import { apiClient } from './api'
import './App.css'

function App() {
  const [sources, setSources] = useState([])
  const [questions, setQuestions] = useState([])
  const [genLoading, setGenLoading] = useState(false)

  const handleGenerate = async () => {
    if (!activeSource) return
    setGenLoading(true)
    setError(null)
    try {
      const result = await apiClient.generateQuestions(activeSource.id, {
        target_audience_level: audience,
        num_questions: 5
      })
      if (result.questions) {
        setQuestions(result.questions)
      } else {
        setError('Generation failed: ' + (result.detail || 'Unknown error'))
      }
    } catch (err) {
      setError('Failed to generate questions.')
    } finally {
      setGenLoading(false)
    }
  }

  return (
    <>
      <div className="sidebar">
        <div className="logo">
          <span style={{ fontSize: '1.5rem' }}>🧠</span>
          <span style={{ letterSpacing: '-0.5px' }}>QuizSensei</span>
        </div>
        
        <div className="source-list">
          <p style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', fontWeight: '600', marginBottom: '16px', paddingLeft: '8px', letterSpacing: '0.5px' }}>SOURCES</p>
          {sources.map(source => (
            <div 
              key={source.id} 
              className={`source-item ${activeSource?.id === source.id ? 'active' : ''}`}
              onClick={() => {
                setActiveSource(source)
                setQuestions([]) // Clear questions when switching sources for now
              }}
            >
              <span>{source.status === 'analyzed' ? '✨' : '📄'}</span>
              <span className="source-name">
                {source.name}
              </span>
            </div>
          ))}
          {sources.length === 0 && <p className="empty-text">Drop files here to start</p>}
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
        <div className="header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <h2 style={{ fontSize: '1.1rem', fontWeight: '600' }}>{activeSource ? activeSource.name : 'Untitled Notebook'}</h2>
            {activeSource?.analysis && <span className="badge">Analyzed</span>}
          </div>
          <div style={{ display: 'flex', gap: '8px' }}>
             <button className="secondary-btn">Export</button>
             <button className="secondary-btn">Share</button>
          </div>
        </div>

        <div className="content-area fade-in">
          {error && <div className="error-box">{error}</div>}
          
          {!activeSource ? (
            <div className="welcome-screen">
              <div className="welcome-icon">🎓</div>
              <h1>Welcome, Professor</h1>
              <p>Upload your lecture notes, PDFs, or images. QuizSensei will analyze the pedagogical depth and prepare a diagnostic assessment for you.</p>
            </div>
          ) : (
            <div className="document-workspace">
              {activeSource.analysis ? (
                <div className="analysis-view fade-in">
                   <div className="analysis-header">
                     <div className="topic-info">
                       <span className="label">TOPIC</span>
                       <h3>{activeSource.analysis.topic}</h3>
                       <p>{activeSource.analysis.subtopic}</p>
                     </div>
                     <div className="level-badge">
                       <span className="label">DEPTH</span>
                       <div className="level-value">{activeSource.analysis.suggested_learner_level}</div>
                     </div>
                   </div>
                   
                   <section className="analysis-section">
                     <h4>AI Insights</h4>
                     <div className="reasoning-card">
                       <p>{activeSource.analysis.learner_level_reason}</p>
                     </div>
                   </section>

                   <section className="analysis-section">
                     <h4>Key Concepts</h4>
                     <div className="keywords-grid">
                       {activeSource.analysis.keywords_found?.map((kw, i) => (
                         <span key={i} className="keyword-chip">{kw}</span>
                       ))}
                     </div>
                   </section>
                </div>
              ) : (
                <div className="loading-state">
                  <div className="spinner"></div>
                  <p>Our AI is reading your document...</p>
                </div>
              )}
            </div>
          )}
        </div>

        <div className="action-bar">
          <input type="text" placeholder="Ask a question about this source..." />
          <button className="send-btn">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" style={{ width: '18px' }}><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>
          </button>
        </div>
      </div>

      <div className="workbench">
        <div className="workbench-header">
          <h3>Assessment</h3>
        </div>
        
        <div className="config-card">
          <div className="form-group">
            <label>TARGET AUDIENCE</label>
            <select value={audience} onChange={(e) => setAudience(e.target.value)}>
              <option>ประถม</option>
              <option>มัธยมต้น</option>
              <option>มัธยมปลาย</option>
              <option>มหาวิทยาลัย</option>
              <option>วัยทำงาน</option>
            </select>
          </div>

          <button 
            className="generate-btn"
            onClick={handleGenerate}
            disabled={!activeSource || activeSource.status !== 'analyzed' || genLoading}
          >
            {genLoading ? 'Generating...' : 'Generate Quiz'}
          </button>
        </div>

        <div className="questions-container">
          <p className="section-title">QUESTIONS ({questions.length})</p>
          <div className="questions-list">
            {questions.map((q, i) => (
              <div key={i} className="question-card fade-in">
                <div className="q-header">
                  <span className="q-number">Q{i+1}</span>
                  <span className={`q-tag ${q.metadata?.cognitive_level?.toLowerCase()}`}>{q.metadata?.cognitive_level || 'Bloom'}</span>
                </div>
                <p className="q-text">{q.question_text}</p>
                <div className="options-hint">
                  {q.distractors?.length + 1} options available
                </div>
              </div>
            ))}
            {questions.length === 0 && !genLoading && (
              <div className="questions-empty">
                <div style={{ fontSize: '2rem', marginBottom: '8px', opacity: 0.3 }}>📝</div>
                <p>No questions generated yet. Adjust settings and click 'Generate'.</p>
              </div>
            )}
            {genLoading && (
              <div className="questions-loading">
                <div className="skeleton-line"></div>
                <div className="skeleton-line short"></div>
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  )
}

export default App

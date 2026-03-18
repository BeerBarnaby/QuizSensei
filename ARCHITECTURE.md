# QuizSensei Architecture & Design

## 1. System Overview

QuizSensei is a source-grounded quiz generation platform with a NotebookLM-like UX. Users upload documents, select sources, and generate quizzes with explicit source attribution.

### Core Design Principles

- **Source-First**: Every quiz question must be grounded in selected source material
- **Explicit Attribution**: Always show which source (file, page, section) each question comes from
- **Async Processing**: Long-running operations (OCR, extraction, generation) don't block UX
- **Clean Architecture**: Loose coupling between extraction, understanding, and generation layers
- **Extensibility**: Easy to swap mock services with production implementations

---

## 2. Workflow State Machine

```
UPLOAD → UPLOADED
  ↓
SELECT → SELECTED → BUILDING SOURCE → EXTRACTED → REVIEWING
  ↓
APPROVE → APPROVED → SOURCE_READY
  ↓
GENERATE QUIZ → GENERATING_QUIZ
  ↓
GENERATED → QUIZ_READY
  ↓
(Optional) EVALUATE → EVALUATING → COMPLETED
```

**States:**

- **UPLOADED**: Files uploaded, awaiting source selection
- **SELECTED**: User selected files as source
- **BUILDING_SOURCE**: System processing extraction/OCR
- **EXTRACTED**: Text extracted, waiting for review
- **REVIEWING**: User reviewing extracted text
- **APPROVED**: User approved the extracted source
- **SOURCE_READY**: Source text finalized, ready for quiz generation
- **GENERATING_QUIZ**: Quiz generation in progress
- **QUIZ_READY**: Quiz generated
- **EVALUATING**: (Optional advanced mode) Multi-agent evaluation
- **COMPLETED**: Process complete
- **FAILED**: Any step failed

---

## 3. Data Models

### 3.1 Source

```python
class Source(Base):
    """
    Represents a selected source for quiz generation.
    Groups one or more documents that will be processed together.
    """
    id: UUID
    name: str                          # User-defined name
    state: SourceState                 # Current workflow state
    created_at: datetime
    updated_at: datetime

    # Relationships
    documents: List[Document]          # Files in this source
    extracted_content: ExtractedContent
    understanding: SourceUnderstanding
    quiz: Quiz
```

### 3.2 Document

```python
class Document(Base):
    """Physical file uploaded by user."""
    id: UUID
    source_id: UUID                    # Which source this belongs to
    filename: str
    file_type: str                     # pdf, docx, txt, image
    file_size: int                     # bytes
    file_path: str                     # Storage location
    uploaded_at: datetime
    state: DocumentState               # uploaded, extracting, extracted, failed

    # Extraction metadata
    num_pages: Optional[int]           # For PDFs
    extraction_metadata: dict          # Service-specific data
```

### 3.3 ExtractedContent

```python
class ExtractedContent(Base):
    """
    Text extracted from one or more documents.
    Can be edited by user before approval.
    """
    id: UUID
    source_id: UUID
    state: ExtractionState             # extracted, reviewing, approved

    # Content
    raw_text: str                      # Full extracted text
    edited_text: Optional[str]         # User-edited version
    approved_text: str                 # Final approved version

    # Metadata
    extraction_method: str             # "mock_pdf", "mock_ocr", etc
    extracted_at: datetime
    approved_at: Optional[datetime]

    # Section/page tracking
    sections: List[ContentSection]     # Structured: [doc][page][section]
```

### 3.4 ContentSection

```python
class ContentSection(Base):
    """
    Hierarchical content structure for attribution.
    Enables precise source referencing in quiz.
    """
    id: UUID
    extracted_content_id: UUID

    # Hierarchy
    document_id: UUID
    page_number: Optional[int]         # Relevant for PDFs, images
    section_number: int                # Sequential section number
    section_title: Optional[str]       # If document has headings

    # Content
    text: str                          # Section text
    word_count: int
```

### 3.5 SourceUnderstanding

```python
class SourceUnderstanding(Base):
    """
    AI-generated metadata about the source.
    Helps system generate better quizzes.
    """
    id: UUID
    source_id: UUID

    # Understanding
    summary: str                       # 2-3 paragraph summary
    key_topics: List[str]              # [5-10 topics]
    important_concepts: List[str]      # Key terminology
    learning_objectives: List[str]     # What students should learn
    possible_quiz_topics: List[str]    # Suggested areas for quizzes

    # Metadata
    understanding_method: str          # "mock_llm", "production_llm", etc
    generated_at: datetime
```

### 3.6 Quiz

```python
class Quiz(Base):
    """Container for generated quiz."""
    id: UUID
    source_id: UUID

    # Generation parameters
    num_questions: int
    question_type: QuestionType        # MCQ, SHORT, MIXED
    difficulty: DifficultyLevel        # EASY, MEDIUM, HARD, MIXED

    # Metadata
    state: QuizState                   # generating, ready, failed
    generated_at: datetime
    regeneration_count: int            # Track how many times user regenerated

    # Content
    questions: List[Question]
    evaluation: Optional[QuizEvaluation]  # Advanced mode
```

### 3.7 Question

```python
class Question(Base):
    """Single quiz question with source attribution."""
    id: UUID
    quiz_id: UUID

    # Question content
    text: str                          # The question
    question_type: QuestionType        # MCQ, SHORT, etc
    difficulty: DifficultyLevel

    # Answer
    answer: str                        # Correct answer
    explanation: str                   # Why this answer is correct

    # Source attribution (CRITICAL)
    source_references: List[SourceReference]

    # Optional
    ai_feedback: Optional[str]         # From evaluation
    pass_gate: bool                    # Did it pass quality checks?
    pass_gate_reason: Optional[str]
```

### 3.8 SourceReference

```python
class SourceReference(Base):
    """
    Maps question back to source material.
    Could be from one or multiple sections.
    """
    id: UUID
    question_id: UUID
    content_section_id: UUID           # Which section(s)

    # Display
    excerpt: str                       # Quote from source ("...")
    page_number: Optional[int]
    section_title: Optional[str]
    document_filename: str

    # Confidence
    confidence_score: float            # 0-1, how confident is reference?
```

### 3.9 MCQChoice (if question is MCQ)

```python
class MCQChoice(Base):
    """Answer choice for MCQ questions."""
    id: UUID
    question_id: UUID

    choice_text: str
    choice_label: str                  # A, B, C, D
    is_correct: bool
```

### 3.10 QuizEvaluation (Advanced Mode)

```python
class QuizEvaluation(Base):
    """
    Optional evaluation metadata from multi-agent evaluation.
    Part of advanced mode, not required for MVP.
    """
    id: UUID
    quiz_id: UUID

    # Evaluation results per question
    question_evaluations: List[QuestionEvaluation]

    # Summary
    overall_quality_score: float       # 0-1
    issues: List[str]
    recommendations: List[str]
    evaluated_at: datetime
```

---

## 4. Service Architecture

### 4.1 Extraction Layer

```
IExtractionService (interface)
├── PDF Extractor (mock → pytesseract OCR)
├── Image Extractor (mock → tesseract)
├── DOCX Extractor (mock → python-docx)
└── TXT Extractor (trivial)

Returns: ExtractedContent with ContentSections
```

**Mock**: Returns synthetic extracted text
**Production**: Uses pytesseract, pdf2image, python-docx

### 4.2 Understanding Layer

```
IUnderstandingService (interface)
├── LLM-Based Understanding (mock → fake data)
└── (Production) OpenAI / LLM API

Returns: SourceUnderstanding
```

**Mock**: Returns hardcoded summaries, topics, concepts
**Production**: Calls LLM API to analyze source

### 4.3 Quiz Generation Layer

```
IQuizGenerationService (interface)
├── Quiz Generator (mock → template-based)
└── (Production) LLM-based generator

Input: SourceUnderstanding, ExtractionContent, Parameters
Returns: Quiz with Questions and SourceReferences
```

**Mock**: Generates questions from template, creates fake references
**Production**: Uses LLM to generate based on source, maps references

### 4.4 Evaluation Layer (Advanced - Optional)

```
IQuizEvaluationService (interface)
├── Answer Understanding Agent (mock)
├── Reference Alignment Agent (mock)
├── Scoring Agent (mock)
├── Feedback Agent (mock)
└── Verification Agent (mock)

Returns: QuizEvaluation with per-question feedback
```

**All Mock Initially** - Provides interface for production multi-agent system

---

## 5. Frontend Architecture

### 5.1 Layout: 3-Panel NotebookLM Style

```
┌─────────────────────────────────────────────────┐
│              Header (QuizSensei)                │
├──────────┬──────────────────┬──────────────────┤
│          │                  │                  │
│  LEFT    │     CENTER       │     RIGHT        │
│          │                  │                  │
│ Sources  │  Source Viewer / │   Quiz Generator │
│ List     │  Extract Review  │   / Results      │
│          │                  │                  │
│          │                  │                  │
└──────────┴──────────────────┴──────────────────┘
```

### 5.2 Left Panel: Source List

- List of uploaded documents with metadata (name, type, size, status)
- Checkbox to select/deselect as source
- "Build Source" button (prominent)
- Status indicators

### 5.3 Center Panel: Source Viewer

- Shows extracted text from selected source
- States:
  - **Uploading**: File upload progress
  - **Processing**: Extraction in progress (spinner)
  - **Extracted**: Show text with edit capability
  - **Reviewing**: User can make edits
  - **Approved**: Final text (read-only)
- Edit mode: Inline text editing
- Approve button when happy with content

### 5.4 Right Panel: Quiz Generator / Results

- **Before Generation**:
  - Quiz settings (# questions, question type, difficulty)
  - "Generate Quiz" button
  - Loading state with progress
- **After Generation**:
  - Quiz display with:
    - Question text
    - If MCQ: choices labeled A, B, C, D
    - Answer + Explanation
    - Source reference (file, page, excerpt)
  - Buttons: "Regenerate Quiz" / "Regenerate Question"

### 5.5 State Management

```
App Context
├── uploadedFiles: File[]
├── selectedSources: UUID[]
├── currentSource: Source (with all nested data)
│   ├── documents: Document[]
│   ├── extractedContent: ExtractedContent
│   ├── understanding: SourceUnderstanding
│   └── quiz: Quiz
├── ui
│   ├── activePanel: 'sources' | 'viewer' | 'generator'
│   ├── isProcessing: boolean
│   ├── currentStep: WorkflowState
│   └── error: Optional[string]
```

---

## 6. API Endpoints

### 6.1 Document/File Management

```
POST   /api/documents/upload              # Upload file(s)
GET    /api/documents                     # List uploaded files
DELETE /api/documents/{doc_id}            # Delete file
GET    /api/documents/{doc_id}            # Get document details
```

### 6.2 Source Management

```
POST   /api/sources                       # Create source from selected docs
GET    /api/sources                       # List sources
GET    /api/sources/{source_id}           # Get source + nested data
PATCH  /api/sources/{source_id}           # Update source (state, name)
DELETE /api/sources/{source_id}           # Delete source
```

### 6.3 Extraction & Content

```
POST   /api/sources/{source_id}/build     # Trigger extraction on selected docs
GET    /api/sources/{source_id}/content   # Get extracted content
PATCH  /api/sources/{source_id}/content   # Update extracted text (edits)
POST   /api/sources/{source_id}/approve   # Approve extracted content
```

### 6.4 Understanding

```
GET    /api/sources/{source_id}/understanding  # Get source understanding
POST   /api/sources/{source_id}/understand     # Generate understanding (if not cached)
```

### 6.5 Quiz Generation

```
POST   /api/sources/{source_id}/quiz/generate  # Generate quiz
GET    /api/sources/{source_id}/quiz           # Get current quiz
POST   /api/sources/{source_id}/quiz/regenerate # Regenerate entire quiz
POST   /api/sources/{source_id}/quiz/regenerate-question/{q_id}  # Regen 1 question
```

### 6.6 Advanced: Evaluation (Phase 2)

```
POST   /api/quizzes/{quiz_id}/evaluate         # Trigger evaluation
GET    /api/quizzes/{quiz_id}/evaluation       # Get evaluation results
```

---

## 7. Directory Structure

```
d:\Project\Nectec26\
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── core/
│   │   ├── config.py
│   │   ├── llm.py
│   │   └── constants.py         # NEW: hardcoded mock data
│   ├── db/
│   │   └── session.py
│   ├── models/
│   │   ├── database_models.py   # UPDATED with all domain models
│   ├── schemas/                 # NEW: Pydantic schemas for API
│   │   ├── __init__.py
│   │   ├── document.py
│   │   ├── source.py
│   │   ├── content.py
│   │   ├── quiz.py
│   │   └── common.py
│   ├── routers/
│   │   ├── documents.py         # NEW: File upload/list
│   │   ├── sources.py           # NEW: Source CRUD
│   │   ├── content.py           # NEW: Extraction/review
│   │   └── quizzes.py           # NEW: Quiz generation
│   └── services/
│       ├── core/
│       │   ├── extraction/      # NEW: Extraction services
│       │   │   ├── base.py      # Interface
│       │   │   ├── mock.py
│       │   │   ├── pdf.py
│       │   │   ├── image.py
│       │   │   ├── docx.py
│       │   │   └── txt.py
│       │   ├── understanding/   # NEW: Understanding services
│       │   │   ├── base.py      # Interface
│       │   │   └── mock.py
│       │   ├── quiz_generation/ # NEW: Generation services
│       │   │   ├── base.py      # Interface
│       │   │   └── mock.py
│       │   └── evaluation/      # NEW: Advanced mode
│       │       ├── base.py      # Interface
│       │       └── mock.py
│       └── source_service.py    # NEW: Orchestration service
├── frontend/
│   ├── src/
│   │   ├── App.jsx              # UPDATED: 3-panel layout
│   │   ├── main.jsx
│   │   ├── index.css
│   │   ├── api.js               # UPDATED: New endpoints
│   │   ├── context/             # NEW: State management
│   │   │   └── SourceContext.jsx
│   │   ├── pages/
│   │   │   ├── MainApp.jsx      # NEW: Main 3-panel page
│   │   │   ├── Dashboard.jsx    # NEW: Initial landing
│   │   │   └── styles/
│   │   ├── components/
│   │   │   ├── SourceList.jsx   # NEW: Left panel
│   │   │   ├── SourceViewer.jsx # NEW: Center panel
│   │   │   ├── QuizGenerator.jsx # NEW: Right panel
│   │   │   ├── UploadArea.jsx   # NEW: File upload
│   │   │   ├── QuestionDisplay.jsx # NEW: Q display
│   │   │   └── styles/
│   │   └── hooks/               # NEW: Custom hooks
│   │       └── useSource.js
│   └── index.html
├── docker-compose.yml
├── requirements.txt
├── ARCHITECTURE.md              # THIS FILE
└── README.md
```

---

## 8. Service Interfaces (Python)

All services follow this pattern to enable easy mock → production switching:

```python
# base.py
from abc import ABC, abstractmethod

class IExtractionService(ABC):
    @abstractmethod
    async def extract(
        self,
        file_path: str,
        file_type: str
    ) -> ExtractedContent:
        """Extract text from file. Returns structured content."""
        pass

class IUnderstandingService(ABC):
    @abstractmethod
    async def understand(
        self,
        content: ExtractedContent
    ) -> SourceUnderstanding:
        """Analyze content and generate understanding."""
        pass

class IQuizGenerationService(ABC):
    @abstractmethod
    async def generate(
        self,
        understanding: SourceUnderstanding,
        content: ExtractedContent,
        parameters: QuizGenerationParameters
    ) -> Quiz:
        """Generate quiz grounded in content & understanding."""
        pass
```

---

## 9. Happy Path Flow

### User perspective:

```
1. Open app → Dashboard with upload area
2. Drag 2 PDF files → Upload completes
3. See files in left panel → Check both files
4. Click "Build Source" → System extracts text
5. Review extracted text in center → Approve
6. Right panel shows quiz settings
7. Set: 5 questions, MCQ+Short, Medium difficulty
8. Click "Generate Quiz"
9. See 5 questions with source refs
10. Click "Regenerate Quiz" for variants
```

### Technical flow:

```
Upload → DocumentCreated, moved to storage

Select Files → Source created, state SELECTED

Build Source →
  - For each doc: Start extraction task
  - Extract awaits in background
  - Return ExtractedContent with ContentSections
  - Update Source state: EXTRACTED

Review & Approve →
  - User sees extracted text
  - Can edit
  - Click Approve → state APPROVED

Auto Understand → (On approval)
  - Call SourceUnderstanding service
  - Generate summary, topics, etc

Generate Quiz →
  - Call QuizGenerationService
  - Pass: understanding + content + parameters
  - Get: Quiz with Questions and SourceReferences
  - Return: Quiz ready for display
```

---

## 10. State Transitions (Backend)

```
Source states:
SELECTED → (build) → BUILDING_SOURCE
BUILDING_SOURCE → EXTRACTED
EXTRACTED → REVIEWING
REVIEWING → APPROVED
APPROVED → SOURCE_READY
SOURCE_READY → GENERATING_QUIZ
GENERATING_QUIZ → QUIZ_READY
QUIZ_READY → (regenerate) → GENERATING_QUIZ
```

Document states within a Source:

```
UPLOADED → EXTRACTING → EXTRACTED
                     ↘ (on error) → FAILED
```

---

## 11. Mock Data Strategy

### Mock files that user uploads:

```
"machine-learning-fundamentals.pdf"
"data-science-workbook.pdf"
"advanced-statistics.txt"
```

### Mock extracted content:

```
ML Fundamentals section 1:
"Machine learning is a subset of artificial intelligence...
Key concepts: supervised learning, unsupervised learning..."

Data Science p.1:
"Data science combines statistics, programming, and domain..."

Statistics:
"Hypothesis testing determines whether..."
```

### Mock understanding:

```
Topics: Supervised Learning, Feature Engineering, Model Evaluation, ...
Concepts: Training/Test Split, Overfitting, Regularization, ...
```

### Mock quiz:

```
Q1 (MCQ, Medium): What is supervised learning?
  A) Learning with labeled data ← CORRECT
  B) Learning without labels
  C) Reinforcement learning
  D) Transfer learning
  Answer: A
  Explanation: Supervised learning uses labeled examples...
  Source: machine-learning-fundamentals.pdf, Page 3, Section "Supervised Learning"
  Excerpt: "Supervised learning uses labeled data where..."

Q2 (Short, Easy): Name two types of machine learning.
  Answer: Supervised and unsupervised learning
  Explanation: These are fundamental categories...
  Source: machine-learning-fundamentals.pdf, Page 2
```

---

## 12. Next Phase: Advanced Mode

When ready to add:

1. **Indicator Extraction**
   - Extract learning objectives, key terms from source
   - Suggest which indicators to focus quiz on

2. **Question Quality Audit**
   - Multi-agent review: Is question clear? Is answer correct? Is reference valid?
   - Pass/fail gate before showing to user

3. **Multi-Agent Answer Evaluation** (for student answers)
   - Understanding Agent: Did student understand the concept?
   - Alignment Agent: Does answer align with source/rubric?
   - Scoring Agent: Assign points
   - Feedback Agent: Generate learning feedback
   - Verifier Agent: Cross-check everything

4. **Quiz Analytics**
   - Track which questions trip up students
   - Surface misconceptions
   - Recommend follow-up learning

---

## 13. Key Design Decisions

| Decision                             | Rationale                                              |
| ------------------------------------ | ------------------------------------------------------ |
| **UUID for IDs**                     | Stateless, distributed-friendly                        |
| **State machine**                    | Clear, trackable, resumable workflows                  |
| **ContentSection model**             | Granular attribution, enables page/section refs        |
| **Service interfaces first**         | Can swap mock ↔ production without code changes        |
| **3-panel layout**                   | Clear information architecture, minimal scrolling      |
| **Async processing**                 | UI never blocks, long operations run in background     |
| **Approved text as source-of-truth** | User maintains control, can fix OCR errors             |
| **Multi-agent in Phase 2**           | MVP validates core concept, Phase 2 adds quality gates |

---

## 14. Development Path

### MVP (Phase 1) - NOW

- ✅ File upload (5 files, basic types)
- ✅ Source selection & "Build Source"
- ✅ Text extraction (mock + real PDF/DOCX)
- ✅ Extract review & approval
- ✅ Quiz generation (mock, grounded in source)
- ✅ Quiz display with source refs
- ✅ Regenerate quiz/question

### Phase 2 - Advanced Mode

- Indicator extraction
- Multi-agent question review
- QA pass/fail gates
- Multi-agent answer evaluation
- Quiz analytics

### Phase 3 - Scale

- Larger docs, batch processing
- Caching (don't re-extract same file)
- Student features (take quiz, track progress)
- Sharing (instructor → students)

---

This architecture balances **simplicity** (MVP works with mocks), **extensibility** (easy to swap services), and **clarity** (state machine, clean separation). Ready to implement?

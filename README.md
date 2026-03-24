# 🎓 QuizSensei: Document-Grounded Assessment Platform

**QuizSensei** is a sophisticated Multi-Agent LLM platform designed for educators to generate high-quality, document-grounded diagnostic assessments. By leveraging a multi-agent pipeline, it ensures **Zero Hallucination** and provides deep **Diagnostic Feedback** rooted in authorized source material.

---

## ✨ Key Features

- 📑 **Source-Grounded Extraction**: High-precision text extraction from PDF, DOCX, and TXT files.
- 🤖 **3-Agent Teacher Pipeline**:
  1. **Analyzer**: Performs deep content analysis and identifies key learning indicators.
  2. **Generator**: Crafts high-quality MCQs with rationales and diagnostic distractor mapping.
  3. **Auditor**: Validates every question against source evidence to prevent hallucinations.
- 🎯 **Diagnostic Assessment**: Designed to identify specific student misconceptions through carefully crafted distractors.
- 📱 **3-Panel Teacher UI**: A streamlined workspace for Source Management, Content Selection, and Quiz Generation.
- 🐳 **Dockerized Stack**: Seamless deployment via Docker Compose for both Frontend and Backend.

---

## 🏗️ Architecture

QuizSensei is built with a modern, scalable stack:
- **Frontend**: [Next.js 15](https://nextjs.org/) (App Router), Tailwind CSS, Zustand.
- **Backend**: [FastAPI](https://fastapi.tiangolo.com/) (Python 3.12), SQLAlchemy 2.0.
- **Database**: PostgreSQL (Structured Data), Redis (Caching & Task Queue).
- **AI Core**: OpenRouter API (Default: Gemini 2.0 Flash).

---

## 🚀 Quick Start (Docker)

To run the full stack locally:

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Nectec26
   ```

2. **Configure Environment**
   Create a `.env` file in the root directory:
   ```env
   OPENROUTER_API_KEY=your_api_key_here
   OPENROUTER_MODEL=google/gemini-2.0-flash-001
   DATABASE_URL=postgresql+asyncpg://user:password@db:5432/quizsensei
   REDIS_URL=redis://redis:6379/0
   ```

3. **Deploy**
   ```bash
   docker-compose up --build
   ```

4. **Access**
   - **Dashboard**: [http://localhost:3000](http://localhost:3000)
   - **API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 📂 Project Structure

```text
Nectec26/
├── app/                  # FastAPI Backend
│   ├── core/             # AI Agents & Configuration
│   ├── models/           # SQLAlchemy Database Models
│   ├── routers/          # API Endpoints (Teacher API)
│   ├── services/         # Orchestration & Business Logic
│   └── main.py           # Application Entry Point
├── frontend/             # Next.js Frontend
│   ├── src/app/          # Application Routes
│   ├── src/components/   # Modular React Components
│   └── src/store/        # State Management (Zustand)
├── docker-compose.yml    # Infrastructure Orchestration
└── README.md             # Project Documentation
```

---

## 🛠️ Tech Stack

- **Backend**: FastAPI, PyPDF2, python-docx, SQLAlchemy, Pydantic.
- **Frontend**: Next.js, React, Zustand, Tailwind CSS.
- **Infrastructure**: Docker, PostgreSQL, Redis.

---

## 📄 License
Education and Research Purposes.

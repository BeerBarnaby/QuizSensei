# 🎓 QuizSensei: Document-Grounded Assessment Platform

**QuizSensei** is a sophisticated Multi-Agent AI platform designed for educators to generate high-quality, document-grounded diagnostic assessments. By leveraging a multi-agent pipeline, it ensures **Zero Hallucination** and provides deep **Diagnostic Feedback** rooted in authorized source material.

---

## ✨ Key Features

- 🔒 **Secure Teacher Dashboard**: JWT-based authentication protecting the entire assessment generation area.
- 📑 **Source-Grounded Extraction**: High-precision text extraction from PDF, DOCX, and TXT files.
- 🤖 **3-Agent Teacher Pipeline**:
  1. **Analyzer (Gatekeeper)**: Evaluates uploaded content sufficiency and identifies learning indicators.
  2. **Generator**: Crafts high-quality MCQs based on specific Bloom's Taxonomy levels and target audiences.
  3. **Auditor**: Leniently validates AI outputs to ensure quality and prevent hallucinations before reaching the teacher.
- 📱 **3-Panel Teacher UI**: A streamlined React workspace for Source Management, Content Selection, and Quiz Generation.
- 🐳 **Dockerized Stack**: Seamless deployment via Docker Compose for both Frontend and Backend, secured in a private bridge network.

---

## 🏗️ Architecture

QuizSensei is built with a modern, scalable stack:
- **Frontend**: [Next.js 15](https://nextjs.org/) (App Router), Tailwind CSS, Zustand, Next.js Middleware.
- **Backend**: [FastAPI](https://fastapi.tiangolo.com/) (Python 3.12), SQLAlchemy 2.0, Passlib, PyJWT.
- **Database / Cache**: PostgreSQL, Redis.
- **AI Core**: OpenRouter API (Default: Google Gemini).

---

## 🚀 Quick Start (Docker)

To run the full stack locally:

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Nectec26
   ```

2. **Configure Environment**
   Create a `.env` file in the root directory and ensure the authentication variables are set:
   ```env
   # --- AI Integration ---
   OPENROUTER_API_KEYS=your_api_key_here
   OPENROUTER_MODEL=google/gemini-2.0-flash-001

   # --- Database ---
   POSTGRES_USER=quizsensei
   POSTGRES_PASSWORD=quizsensei_secret
   POSTGRES_DB=quizsensei_db
   REDIS_URL=redis://redis:6379/0

   # --- Authentication ---
   SECRET_KEY=super-secret-jwt-key
   ADMIN_USERNAME=admin
   ADMIN_PASSWORD=quizsensei2026
   ```

3. **Deploy the Platform**
   ```bash
   docker-compose up --build -d
   ```

4. **Access the Application**
   - **Teacher Dashboard**: [http://localhost:3000](http://localhost:3000) (Login with the Admin credentials above)
   - **API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 📂 Project Structure

```text
Nectec26/
├── app/                  # FastAPI Backend
│   ├── core/             # AI Agents, Configuration & Security
│   ├── models/           # SQLAlchemy Database Models
│   ├── routers/          # API Endpoints (Auth & Teacher API)
│   ├── services/         # Orchestration & LLM Pipeline
│   └── main.py           # Application Entry Point
├── frontend/             # Next.js Frontend
│   ├── src/app/          # App Router & Authenticated Pages
│   ├── src/components/   # Modular React Components
│   └── src/store/        # State Management (Zustand Auth/App)
├── docker-compose.yml    # Secure Container Orchestration
└── README.md             # Project Documentation
```

---

## 🛡️ Security Details

This project implements MVP-level security best practices:
- **Environment Isolation**: Database (Port 5432) and Redis (Port 6379) are hidden from the host machine and accessible only via Docker's internal DNS.
- **App Router Middleware**: Next.js Edge Middleware prevents unauthorized access to the application root.
- **JWT Dependencies**: FastAPI endpoints strictly require valid Bearer tokens retrieved from the `/api/v1/auth/login` endpoint.

---

## 📄 License
Education and Research Purposes.

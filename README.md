# 🎓 QuizSensei: Document-Grounded Diagnostic Assessment Platform

**QuizSensei** คือแพลตฟอร์มสร้างข้อสอบอัจฉริยะที่ใช้ระบบ Multi-Agent LLM ในการวิเคราะห์เอกสารและสร้างข้อสอบปรนัย (MCQ) ที่มีคุณภาพสูง โดยเน้นความถูกต้องของเนื้อหา (**Zero Hallucination**) และการให้คำแนะนำเชิงวินิจฉัย (**Diagnostic Feedback**) เพื่อช่วยให้ผู้เรียนเข้าใจจุดที่ควรปรับปรุง

---

## ✨ Key Features

- 📑 **Source-Grounded Extraction**: รองรับการอัปโหลดไฟล์ PDF, DOCX และ TXT พร้อมระบบสกัดข้อความที่แม่นยำ
- 🤖 **4-Agent Pipeline**: ระบบ AI 4 ระดับที่ทำงานร่วมกันเพื่อคุณภาพสูงสุด:
  1. **Analyzer (Agent 1)**: วิเคราะห์เนื้อหาและกำหนดหัวข้อการเรียนรู้
  2. **Generator (Agent 2)**: สร้างคำถามพร้อมตัวเลือกและคำอธิบาย (Rationales) ในภาษาไทย
  3. **Auditor (Agent 3)**: ตรวจสอบความถูกต้องและป้องกันการแสดงข้อมูลที่ไม่มีในต้นฉบับ (Hallucination)
  4. **Grader (Agent 4)**: ตรวจข้อสอบนักเรียนและให้คำแนะนำส่วนบุคคลเชิงโค้ชชิ่ง
- 🎯 **Diagnostic Assessment**: ข้อสอบที่ออกแบบมาเพื่อค้นหา "ความเข้าใจคลาดเคลื่อน" (Misconceptions) ของผู้เรียน
- 📱 **3-Panel UI**: หน้าจอการจัดการสำหรับครูที่ใช้งานง่าย (Source List | Viewer | Generator)
- 🎓 **Student Portal**: อินเตอร์เฟซสำหรับผู้เรียนที่สะอาดตา พร้อมระบบตรวจข้อสอบทันที
- 🐳 **Dockerized Setup**: ติดตั้งง่ายด้วย Docker Compose ทั้งระบบ Frontend และ Backend

---

## 🏗️ Architecture

ระบบสร้างขึ้นด้วยสถาปัตยกรรมที่ทันสมัยและยืดหยุ่น:
- **Frontend**: [Next.js 15](https://nextjs.org/) (App Router), Tailwind CSS, Zustand
- **Backend**: [FastAPI](https://fastapi.tiangolo.com/) (Python 3.12), SQLAlchemy, Uvicorn
- **Database**: PostgreSQL (Structured Data), Redis (Task Queue/Caching)
- **AI Core**: OpenRouter API (รองรับ Gemini Flash และโมเดลชั้นนำอื่นๆ)

---

## 🚀 Quick Start (Docker)

วิธีที่เร็วที่สุดในการรันระบบคือการใช้ Docker:

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Nectec26
   ```

2. **Set Environment Variables**
   สร้างไฟล์ `.env` ที่ root directory:
   ```env
   OPENROUTER_API_KEY=your_api_key_here
   OPENROUTER_MODEL=google/gemini-2.0-flash-001
   DATABASE_URL=postgresql+asyncpg://user:password@db:5432/quizsensei
   REDIS_URL=redis://redis:6379/0
   ```

3. **Deploy with Docker Compose**
   ```bash
   docker-compose up --build
   ```

4. **Access the Application**
   - **Teacher UI**: [http://localhost:3000](http://localhost:3000)
   - **Student UI**: [http://localhost:3000/student/[document-id]](http://localhost:3000/student/[document-id])
   - **API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 📂 Project Structure

```text
Nectec26/
├── app/                  # FastAPI Backend
│   ├── core/             # Configuration & LLM Agents
│   ├── db/               # Database Session & Models
│   ├── routers/          # API Endpoints (v1)
│   ├── services/         # Core Logic & 4-Agent Services
│   └── main.py           # Application Entry Point
├── frontend/             # Next.js Frontend
│   ├── src/app/          # Pages & Routes
│   ├── src/components/   # React Components (SourceList, QuizGenerator, etc.)
│   └── Dockerfile        # Standalone Build Config
├── docker-compose.yml    # Full Stack Orchestration
└── README.md             # This file
```

---

## 🛠️ Tech Stack & Dependencies

- **Backend**: FastAPI, PyPDF2, python-docx, SQLAlchemy, Pydantic
- **Frontend**: Next.js, React, Zustand, Heroicons, Tailwind CSS
- **Infrastructure**: Docker, Docker Compose, PostgreSQL, Redis

---

## 🤝 Contributing

ยินดีรับการมีส่วนร่วมเพื่อพัฒนาแพลตฟอร์มนี้! หากคุณพบปัญหาหรือต้องการเสนอความสามารถใหม่ๆ สามารถสร้าง Issue หรือ PR ได้ทันที

---

## 📄 License

Project นี้จัดทำขึ้นเพื่อวัตถุประสงค์ทางการศึกษาและพัฒนาเทคโนโลยีการศึกษาไทย

# QuizSensei: AI-Powered Educational Assessment Framework

**QuizSensei** คือแพลตฟอร์มการประเมินผลทางการศึกษาที่ขับเคลื่อนด้วยปัญญาประดิษฐ์ (AI-powered Assessment Platform) โดยมุ่งเน้นการเสริมสร้างทักษะความรู้ทางการเงิน (**Financial Literacy**) ระบบใช้สถาปัตยกรรม **Multi-Agent LLM Pipeline** ในการวิเคราะห์เนื้อหาเชิงลึกและสร้างเครื่องมือวัดผลที่มีประสิทธิภาพสูงสุดในรูปแบบภาษาไทย

---

## สถาปัตยกรรมระบบ (System Architecture)

ระบบประกอบด้วย 4 ตัวแทนอัจฉริยะ (Agents) ที่ทำงานประสานกันผ่าน Pipeline เพื่อการประเมินผลที่แม่นยำ:

1.  **Analytical Agent (Analyzer)**: 
    *   ดำเนินการวิเคราะห์เนื้อหาจากเอกสารที่อัปโหลด
    *   จำแนกระดับผู้เรียน (Learner Level) และประเมินความเพียงพอของเนื้อหา (Content Sufficiency)
    *   ทำหน้าที่เป็น Gatekeeper เพื่อรักษาคุณภาพของชุดข้อมูลตั้งต้น
2.  **Generation Agent (Generator)**: 
    *   ออกแบบและสร้างข้อสอบปรนัย (Multiple Choice Questions) ที่สอดคล้องกับระนาบระดับความยาก (Difficulty Levels) ที่กำหนดโดยผู้ใช้
    *   บูรณาการความรู้เฉพาะทางเข้ากับบริบทของผู้เรียน
3.  **Auditing Agent (Auditor)**: 
    *   ตรวจสอบคุณลักษณะของข้อสอบตามมาตรฐานวิชาการ
    *   ประเมินความถูกต้องของตัวเลือก (Options) และคุณภาพของตัวเลือกหลอก (Distractors) 
    *   ประยุกต์ใช้ระนาบพุทธิพิสัย (Bloom's Taxonomy) เพื่อควบคุมมาตรฐานคำถาม
4.  **Diagnostic Agent (Grader)**: 
    *   ประมวลผลการตอบสนองของผู้เรียนและให้ข้อมูลย้อนกลับเชิงวินิจฉัย (Diagnostic Feedback)
    *   วิเคราะห์ความเข้าใจผิด (Misconceptions) และให้เหตุผลทางวิชาการประกอบผลลัพธ์

---

## กรอบแนวคิดเชิงวิชาการ (Educational Methodology)

QuizSensei ใช้ทฤษฎี **Bloom’s Taxonomy** ในการกำหนดโครงสร้างความซับซ้อนของคำถาม:

| ระดับความยาก | การประยุกต์ใช้ Bloom’s Taxonomy | วัตถุประสงค์การเรียนรู้ |
| :--- | :--- | :--- |
| **ระดับพื้นฐาน (Easy)** | Remember, Understand | มุ่งเน้นการระลึกถึงข้อเท็จจริงและความเข้าใจพื้นฐาน |
| **ระดับกลาง (Intermediate)** | Apply, Analyze | การนำความรู้ไปใช้ในสถานการณ์จำลองและการแยกแยะข้อมูล |
| **ระดับสูง (Advanced)** | Analyze, Evaluate, Create | การประเมินค่าข้อมูลและการสังเคราะห์แนวคิดใหม่ |

---

## โครงสร้างทางเทคโนโลยี (Tech Stack)

*   **Core Logic**: Python 3.12+ (FastAPI Framework)
*   **Intelligent Processing**: OpenRouter Responses API (Stateful AI Processing)
*   **Infrastructure**: PostgreSQL (Async Database Layer) & Redis (Caching Layer)
*   **Interface**: Modern Single Page Application (SPA Concept) with Glassmorphism UI
*   **Document Intelligence**: Document Parser supporting PDF, DOCX, and Text Formats

---

## ขั้นตอนการติดตั้ง (Deployment Guide)

### 1. การกำหนดค่าระบบ (Configuration)
สร้างไฟล์ `.env` ณ root directory และกำหนดค่าตัวแปรสภาพแวดล้อม:

```env
OPENROUTER_API_KEYS=sk-or-v1-xxxx...
OPENROUTER_MODEL=arcee-ai/trinity-large-preview:free 
DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/quizsensei_db
```

### 2. การเริ่มการทำงาน (Execution)
รันระบบผ่าน Docker Containerization เพื่อความเสถียรของสภาพแวดล้อม:

```bash
docker compose up --build -d
```
เข้าสู่ระบบผ่าน Web Interface ได้ที่: **http://localhost:8000**

---

## โครงสร้างโปรเจกต์ (Project Structure)

```text
app/
├── core/               # Configuration and Shared Logic
├── models/             # Database Schemas
├── routers/            # API Endpoints (Exam & Document Management)
├── services/           
│   ├── analyzers/      # Analytical Agent Logic
│   ├── generators/     # Question Generation Engine
│   └── agents/         # Auditor and Diagnostic Grader
frontend/               # User Experience and Interface Components
```

---
© 2026 QuizSensei Project. Dedicated to Advanced Educational AI Research and Development.

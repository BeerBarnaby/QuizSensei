# 🧠 EvalMind – AI-Powered Assessment Platform

EvalMind คือแพลตฟอร์มวิเคราะห์เอกสารและสร้างข้อสอบอัตโนมัติ (AI-powered Assessment) ที่เน้นความรู้ด้าน **Financial Literacy (ทักษะทางการเงิน)** โดยใช้สถาปัตยกรรม **4-Agent LLM Pipeline** ที่ทำงานเป็นภาษาไทย 100%

---

## 🚀 ฟีเจอร์หลัก (Key Features)

### 1. ระบบ 4-Agent LLM Pipeline (Thai-Only)
กระบวนการทำงานถูกแบ่งเป็น 4 ขั้นตอนหลักโดยใช้ AI Agents เฉพาะทาง:

- **🕵️ Agent 1 (Analyzer)**: วิเคราะห์หัวข้อ, จำแนกระดับผู้เรียน (ประถม - วัยทำงาน), และตรวจสอบ "ความเพียงพอของเนื้อหา" (Content Sufficiency) หากเนื้อหาไม่พอระบบจะหยุดทำงานทันทีเพื่อให้ผู้ใช้อัปโหลดเพิ่ม
- **🎨 Agent 2 (Generator)**: สร้างข้อสอบปรนัยโดยอิงตามเนื้อหาเอกสาร + ระดับผู้เรียนและระดับความยากที่ผู้ใช้เลือกเอง (ง่าย/ปานกลาง/ยาก)
- **⚖️ Agent 3 (Auditor)**: ตรวจสอบคุณภาพข้อสอบเชิงลึก ทั้งความแม่นยำ, การใช้ Bloom's Taxonomy, และคุณภาพของตัวเลือกหลอก (Distractors)
- **🎓 Agent 4 (Grader)**: ตรวจคำตอบและให้ Feedback แบบวินิจฉัย (Diagnostic) เพื่ออธิบายเหตุผลว่าทำไมถึงถูกหรือผิด

### 2. การแมกระดับความยากด้วย Bloom’s Taxonomy
ระบบใช้ทฤษฎีการเรียนรู้อย่างเป็นระบบเพื่อให้ข้อสอบมีระดับความท้าทายที่เหมาะสม:
- **ง่าย** -> เน้นการจำและความเข้าใจ (Remember / Understand)
- **ปานกลาง** -> เน้นการประยุกต์ใช้และการวิเคราะห์ (Apply / Analyze)
- **ยาก** -> เน้นการวิเคราะห์, การประเมินค่า และการสร้างสรรค์ (Analyze / Evaluate / Create)

### 3. User-Driven Configuration
ผู้ใช้ไม่ได้แค่รอดูผลลัพธ์ แต่สามารถกำหนดทิศทางของข้อสอบได้เอง:
- เลือก "ระดับผู้เรียน" (Learner Level) ด้วยตัวเอง
- เลือก "ระดับความยาก" (Difficulty) ด้วยตัวเอง

---

## 🛠 เทคโนโลยีที่ใช้ (Tech Stack)
- **Backend**: FastAPI (Python 3.12+)
- **LLM API**: OpenRouter (รองรับการทำ Stateful AI ผ่าน Responses API)
- **Database**: PostgreSQL (SQLAlchemy + Asyncpg) & Redis
- **Frontend**: Vanilla HTML5, CSS (Glassmorphism), JavaScript (SPA Concept)
- **Extraction**: Support PDF, DOCX, TXT

---

## 🏃 วิธีเริ่มใช้งานระบบ

### 1. ตั้งค่า Environment
สร้างไฟล์ `.env` และระบุ API Key:
```env
OPENROUTER_API_KEYS=sk-or-v1-xxxx...
OPENROUTER_MODEL=arcee-ai/trinity-large-preview:free 
DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/evalmind
```

### 2. รันระบบผ่าน Docker
```bash
docker compose up --build -d
```
เข้าใช้งานได้ที่ **[http://localhost:8000](http://localhost:8000)**

---

## 📂 โครงสร้างโปรเจกต์ (Project Structure)
- **`app/services/analyzers/`**: Agent 1 (Analyzer Logic)
- **`app/services/generators/`**: Agent 2 (Question Generation)
- **`app/services/agents/`**: Agent 3 (Auditor) และ Agent 4 (Grader)
- **`app/routers/`**: API Endpoints (Documents, Exams)
- **`frontend/`**: หน้าจอผู้ใช้งาน (Dark Mode & Premium UI)

---
© 2026 EvalMind Project. Developed for Advanced AI Assessment.

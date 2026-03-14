# 🧠 EvalMind – AI-Powered Assessment Platform

EvalMind คือแพลตฟอร์มวิเคราะห์เอกสารและสร้างข้อสอบอัตโนมัติ (AI-powered Assessment) ที่เน้นความรู้ด้าน **Financial Literacy (ทักษะทางการเงิน)** โดยใช้สถาปัตยกรรมแบบ **Multi-Agent AI Pipeline** เพื่อความแม่นยำและการตรวจสอบคุณภาพที่สูงสุด

---

## 🚀 Key Features

### 1. NotebookLM-Style UI
หน้าจอการใช้งานแบบ 2-Panel ที่ออกแบบมาให้ใช้งานง่ายในหน้าเดียว:
- **Sidebar**: อัปโหลดเอกสาร (Drag & Drop) และดูรายชื่อเอกสารทั้งหมด
- **Main Area**: แบ่งเป็น 4 Tabs (Extraction, Analysis, Quiz, Analytics)

### 2. 4-Agent AI Pipeline (OpenRouter)
ระบบใช้ AI Agents 4 ตัวทำงานสอดประสานกันเพื่อสร้างข้อสอบที่มีคุณภาพระดับสูง:
- **🕵️ Agent 1 (Analyzer)**: วิเคราะห์เนื้อหาเพื่อระบุ Topic, Sub-topic, ความยาก (Difficulty) และ **Bloom's Taxonomy Level**
- **🎨 Agent 2 (Generator)**: สร้างข้อสอบ Multiple Choice พร้อม **Design Reasoning** (ทำไมถึงออกข้อนี้) และ **Distractor Map** (ทุกตัวเลือกที่ผิดต้องมี Misconception Tag กำกับ)
- **⚖️ Agent 3 (Auditor)**: ตรวจสอบคุณภาพข้อสอบที่ Agent 2 สร้างขึ้น หากไม่ผ่านเกณฑ์จะ **Reject** ทันที เพื่อให้ผู้เรียนได้รับข้อสอบที่ดีที่สุด
- **🎓 Agent 4 (Grader)**: ไม่ใช่แค่ตรวจถูก/ผิด แต่เป็นการ **วินิจฉัย (Diagnosis)** ว่าหากผู้เรียนตอบผิด เขา "เข้าใจผิดเรื่องอะไร" และควรทบทวนหัวข้อไหนต่อ

---

## 🛠 Technology Stack
- **Backend**: FastAPI (Python 3.12+)
- **LLM Orchestration**: OpenRouter (GPT-4o, Claude 3.5 Sonnet, or other OSS models)
- **Database**: PostgreSQL (SQLAlchemy + AsyncPG)
- **Frontend**: Vanilla HTML5 / CSS3 (Glassmorphism Dark Theme) / JavaScript (ES6)
- **Deployment**: Docker & Docker Compose

---

## 🏃 วิธีเริ่มใช้งาน (Local Setup)

### 1. เตรียมสภาพแวดล้อม
```bash
# Clone project และเข้า directory
cd Nectec26

# สร้าง virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# or: source .venv/bin/activate # Mac/Linux

# ติดตั้ง dependencies
pip install -r requirements.txt
```

### 2. ตั้งค่า Environment Variables
สร้างไฟล์ `.env` (ดูตัวอย่างที่ `.env.example`) และระบุ `OPENROUTER_API_KEY`:
```env
OPENROUTER_API_KEY=sk-or-v1-xxxx...
OPENROUTER_MODEL=google/gemini-pro-1.5  # หรือโมเดลอื่น
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/evalmind
```

### 3. รัน Server
```bash
uvicorn app.main:app --reload
```
เปิด Browser ไปที่: **[http://localhost:8000](http://localhost:8000)**

---

## 📂 Project Structure
- **`app/routers/`**: Document management และ Exam/Analytics endpoints
- **`app/services/agents/`**: หัวใจของระบบ (Auditor, Grader, Generator)
- **`app/services/analyzers/`**: Agent 1 ที่ทำหน้าที่แยกประเภทเนื้อหา
- **`app/schemas/`**: Data contracts สำหรับการคุยกันระหว่าง Agents และ Frontend
- **`frontend/`**: หน้าจอผู้ใช้งานทั้งหมด (Single Page Application)
- **`uploads/`, `sidecars/`**: พื้นที่จัดเก็บไฟล์และผลการวิเคราะห์ (Analysis/Questions) แบบ JSON

---

## 🔒 Security & Performance
- **Deterministic Grading**: Agent 4 ใช้ข้อมูลวินิจฉัยที่ถูกคำนวณไว้แล้วจาก Agent 2 ทำให้การตรวจคำตอบรวดเร็วและประหยัด API Cost
- **Async Workflow**: ใช้ `aiofiles` และ `AsyncSession` เพื่อรองรับการทำงานแบบ Non-blocking
- **Safe Filenames**: ป้องกัน Path Traversal ในการจัดเก็บไฟล์

---

## 📄 License
© 2026 EvalMind Project. Developed for Advanced AI Assessment.

# QuizSensei

**AI-Driven Diagnostic Assessment Platform for Financial Literacy**

QuizSensei เป็นแพลตฟอร์มอัจฉริยะที่ใช้เทคโนโลยี **Multi-Agent LLM** เพื่อแปลงเอกสารความรู้ทางการเงิน (Financial Literacy) ให้เป็นแบบทดสอบเชิงวินิจฉัย (Diagnostic Assessment) แบบอัตโนมัติ พร้อมตรวจคำตอบและให้คำแนะนำแบบเฉพาะตัว (Personalized Coaching) โดยใช้หลักการ Zero-Hallucination

---

## 1. ฟีเจอร์หลัก (Key Features)

- **📄 Document Upload & Extraction:** อัปโหลดและสกัดข้อความจากแหล่งข้อมูล (PDF, TXT, DOCX, Images)
- **🤖 4-Agent Pipeline:**
  - **Agent 1 (Gatekeeper & Analyzer):** ตรวจสอบว่าเอกสารมีความรู้เพียงพอต่อการออกข้อสอบหรือไม่ (Content Sufficiency) เเละระบุระดับผู้เรียนทั้ง 5 ระดับ (ประถม, มัธยมต้น, มัธยมปลาย, มหาวิทยาลัย, วัยทำงาน)
  - **Agent 2 (Generator):** สร้างข้อสอบแบบปรนัย 4 ตัวเลือก โดยอิงจากเอกสาร 100% (Zero-hallucination) พร้อมสร้างตัวเลือกหลอก (Diagnostic Distractors) ที่สะท้อนความเข้าใจผิดที่พบได้บ่อย
  - **Agent 3 (Auditor):** ตรวจทานข้อสอบกับต้นฉบับอย่างเข้มงวด หากเนื้อหาไม่ตรงจะยกเลิกและสั่งสร้างใหม่ทันที (Auto-Regeneration)
  - **Agent 4 (Grader & Coach):** ตรวจคำตอบของนักเรียนและให้คำอธิบายที่เข้าใจง่าย เพื่อชี้จุดที่เข้าใจผิด
- **💻 Modern Next.js Interface:** หน้าบ้านรูปแบบ 3 คอลัมน์ (NotebookLM-style) ที่ใช้งานง่าย รวดเร็ว และรองรับภาษาไทยเต็มรูปแบบ

---

## 2. วิธีการติดตั้งและรันโปรเจกต์ (Installation & Setup)

### วิธีที่ 1: รันผ่าน Docker Compose (แนะนำ)
รันทั้ง Backend (FastAPI), Frontend (Next.js), Database (Postgres) และ Cache (Redis) ในคำสั่งเดียว
1. สร้างไฟล์ `.env` ในโฟลเดอร์หลัก และกำหนดค่า API Key:
   ```env
   OPENROUTER_API_KEY=your_key_here
   OPENROUTER_MODEL=google/gemini-2.5-flash
   ```
2. รันคำสั่ง Docker:
   ```bash
   docker-compose up --build
   ```
3. เข้าใช้งานระบบ:
   - **Frontend:** http://localhost:3000
   - **Backend API Docs:** http://localhost:8000/docs

### วิธีที่ 2: รันแยกส่วนสำหรับการพัฒนา (Manual Development)

**Backend (FastAPI):**
```bash
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Frontend (Next.js):**
```bash
cd frontend
npm install
npm run dev
# ทำงานที่พอร์ต 3000
```

---

## 3. โครงสร้างโปรเจกต์ (Project Architecture)

- **`app/`**: Backend พัฒนาด้วย FastAPI ประกอบไปด้วย Core Logic, Models (SQLAlchemy), Schemas, Service classes สำหรับ Agents เเละเส้นทาง API (Routers)
- **`frontend/`**: Frontend พัฒนาด้วย Next.js (App Router), Tailwind CSS v4, Zustand. มี Components หลักสำหรับระบบจัดการเอกสาร (SourceList, SourceViewer) เเละระบบสุ่มข้อสอบ (QuizGenerator)
- **`uploads/`**: โฟลเดอร์เก็บเอกสารต้นฉบับเเละ JSON sidecars ที่เกี่ยวข้อง
- **`docker-compose.yml`**: เซ็ตอัป Infrastructure โดยรวมพร้อม Database เเละ Next.js Standalone build

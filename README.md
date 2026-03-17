# QuizSensei

**AI-Driven Diagnostic Assessment Platform for Financial Literacy**

QuizSensei เป็นแพลตฟอร์ม Backend อัจฉริยะที่ใช้ระบบ **Multi-Agent LLM Pipeline** ในการเปลี่ยนเอกสารความรู้ทางการเงิน (Financial Literacy) ให้กลายเป็นแบบทดสอบเชิงวินิจฉัย (Diagnostic Assessment) แบบอัตโนมัติ

---

## 1. โปรเจ็คนี้คืออะไร? (What is this project?)
QuizSensei คือระบบนิเวศการเรียนรู้ที่ใช้พลังของ Generative AI ในการ:
- **แสกนและวิเคราะห์เอกสาร:** รองรับทั้งไฟล์ Digital และเอกสารแสกนผ่านระบบ Universal OCR
- **สร้างข้อสอบเชิงวินิจฉัย:** สร้างคำถามที่ไม่ได้แค่วัดความรู้ แต่สามารถระบุ "ความเข้าใจผิด" (Misconception) ของผู้เรียนได้ผ่านตัวเลือกที่ผิด (Distractors)
- **ประเมินผลอัจฉริยะ:** ให้ Feedback แบบทันที (Zero-cost diagnostic) โดยอิงจากข้อมูลที่ AI วิเคราะห์ไว้ในขั้นตอนการสร้าง

---

## 2. รันยังไง? (How to run it?)

### วิธีที่ 1: Docker Compose (แนะนำ)
ต้องการเพียง Docker และ Docker Desktop ในเครื่อง:
1.  `.env` และใส่ API Key จาก **OpenRouter**
2.  เปิด Terminal ในโฟลเดอร์โปรเจ็คแล้วรัน:
    ```bash
    docker-compose up --build
    ```
3.  Backend จะรันที่ `http://localhost:8000`

### วิธีที่ 2: รันแบบ Manual (สำหรับ Development)
1.  ติดตั้ง Python 3.12+
2.  ติดตั้ง Tesseract OCR ในเครื่อง (ถ้าต้องการใช้ Local OCR)
3.  ติดตั้ง Dependencies:
    ```bash
    pip install -r requirements.txt
    ```
4.  ตั้งค่า `.env` ให้ครบถ้วน
5.  รันด้วย Uvicorn:
    ```bash
    python main.py
    ```

---

## 3. โครงสร้างเป็นยังไง? (Structure)
โปรเจ็คถูกออกแบบให้แยกส่วน (Decoupled) อย่างชัดเจนตามรูปแบบ Service-Oriented Architecture:

```text
Nectec26/
├── app/
│   ├── core/           # หัวใจของระบบ (Config, LLM Wrapper, DB Session)
│   ├── models/         # SQLAlchemy Database Models (Postgres)
│   ├── schemas/        # Pydantic Schemas สำหรับ Input/Output API
│   ├── services/       # Business Logic หลัก
│   │   ├── agents/     # Multi-Agent Pipeline (Auditor, Grader)
│   │   ├── analyzers/  # Agent 1: Analyzer
│   │   ├── generators/ # Agent 2: Generator
│   │   ├── extractors/ # 3-Tier OCR Engine (PDF, DOCX, Image)
│   │   └── ocr_service.py
│   ├── routers/        # API Endpoints (FastAPI)
│   └── main.py         # จุดรันโปรแกรม
└── uploads/            # พื้นที่เก็บไฟล์และ Sidecar JSON (Data Storage)
```

---

## 4. ใช้ Tech Stack อะไร? (Tech Stack)
- **Language:** Python 3.12
- **Framework:** FastAPI (High-performance API)
- **Database:** PostgreSQL (Relational Data)
- **Storage:** Local Filesystem (Sidecar JSON Strategy)
- **AI/LLM:** OpenRouter API (Accessing Gemini Flash, StepFun, etc.)
- **OCR:** 3-Tier Engine (Digital Extract + Vision LLM + Tesseract)
- **Infrastructure:** Docker & Docker Compose

---

## 5. Flow การทำงานหลักคืออะไร? (Main Workflow)

ระบบทำงานประสานกันผ่าน **4-Agent Pipeline**:

1.  **Phase 1: Extraction & OCR** -> อ่านไฟล์เอกสาร ถ้าเป็นภาพจะส่งให้ Vision LLM (Tier 2) หรือ Tesseract (Tier 3) พร้อมเกลาข้อความให้เป็น Markdown
2.  **Phase 2: Analyzer (Agent 1)** -> วิเคราะห์เนื้อหาว่าเกี่ยวกับการเงินไหม เนื้อหาพอไหม และกลุ่มเป้าหมายคือใคร
3.  **Phase 3: Generator & Auditor (Agent 2 & 3)** -> 
    - **Generator:** สร้างข้อสอบตามทฤษฎี Bloom's Taxonomy พร้อมออกแบบตัวเลือกที่ผิดให้สอดคล้องกับพฤติกรรมผู้เรียน
    - **Auditor:** ตรวจสอบคุณภาพ ถ้าไม่ผ่านระบบจะสร้างใหม่ทันที (Auto-Regeneration)
4.  **Phase 4: Grader (Agent 4)** -> ระบบตรวจคำตอบแบบ Diagnostic ที่ไม่ต้องเรียก AI ซ้ำ ทำให้ประมวลผลได้เร็วและฟรี (Zero-cost)

---

> [!NOTE]
> ระบบนี้ถูกออกแบบมาเพื่อความ Robust และ Scalability โดยการใช้ไฟล์ JSON เป็น Sidecar เพื่อเก็บข้อมูลขนาดใหญ่และใช้ Database สำหรับส่วนที่ต้องการ Query รวดเร็ว

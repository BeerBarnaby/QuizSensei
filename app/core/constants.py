"""
Central enums, Thai labels, and Bloom's Taxonomy mappings for QuizSensei v2.
All user-facing strings are in Thai. Code identifiers remain in English.
"""
from enum import Enum


# ── Learner Levels ────────────────────────────────────────────────────────────

class LearnerLevel(str, Enum):
    """5 learner levels as specified in the QuizSensei spec."""
    PRIMARY = "primary"
    MIDDLE_SCHOOL = "middle_school"
    HIGH_SCHOOL = "high_school"
    UNIVERSITY = "university"
    WORKING_ADULT = "working_adult"


LEARNER_LEVEL_TH = {
    LearnerLevel.PRIMARY: "ประถม",
    LearnerLevel.MIDDLE_SCHOOL: "มัธยมต้น",
    LearnerLevel.HIGH_SCHOOL: "มัธยมปลาย",
    LearnerLevel.UNIVERSITY: "มหาวิทยาลัย",
    LearnerLevel.WORKING_ADULT: "วัยทำงาน",
}

LEARNER_LEVEL_FROM_TH = {v: k for k, v in LEARNER_LEVEL_TH.items()}


# ── Difficulty Levels ─────────────────────────────────────────────────────────

class Difficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


DIFFICULTY_TH = {
    Difficulty.EASY: "ง่าย",
    Difficulty.MEDIUM: "ปานกลาง",
    Difficulty.HARD: "ยาก",
}


# ── Bloom's Taxonomy ──────────────────────────────────────────────────────────

class BloomsLevel(str, Enum):
    REMEMBER = "remember"
    UNDERSTAND = "understand"
    APPLY = "apply"
    ANALYZE = "analyze"
    EVALUATE = "evaluate"
    CREATE = "create"


DIFFICULTY_TO_BLOOMS = {
    Difficulty.EASY: [BloomsLevel.REMEMBER, BloomsLevel.UNDERSTAND],
    Difficulty.MEDIUM: [BloomsLevel.APPLY, BloomsLevel.ANALYZE],
    Difficulty.HARD: [BloomsLevel.ANALYZE, BloomsLevel.EVALUATE, BloomsLevel.CREATE],
}

DIFFICULTY_TO_BLOOMS_TH = {
    Difficulty.EASY: "การจำ/ความเข้าใจ (Remember / Understand): คำถามวัดความจำนิยาม กฎพื้นฐาน หรือการอธิบายความหมายตรงๆ",
    Difficulty.MEDIUM: "การประยุกต์ใช้/วิเคราะห์ (Apply / Analyze): คำถามวัดการนำไปใช้ในสถานการณ์จำลอง การคำนวณ การเปรียบเทียบ",
    Difficulty.HARD: "การวิเคราะห์/ประเมินค่า/สร้างสรรค์ (Analyze / Evaluate / Create): คำถามวัดการตัดสินใจ การจัดลำดับความสำคัญ การออกแบบแผน",
}


# ── Document States ───────────────────────────────────────────────────────────

class DocumentState(str, Enum):
    UPLOADED = "uploaded"
    EXTRACTING = "extracting"
    EXTRACTED = "extracted"
    APPROVED = "approved"
    FAILED = "failed"


# ── Source States ─────────────────────────────────────────────────────────────

class SourceState(str, Enum):
    CREATED = "created"
    ANALYZING = "analyzing"
    READY = "ready"
    INSUFFICIENT = "insufficient"
    GENERATING = "generating"
    QUIZ_READY = "quiz_ready"


# ── Quiz States ───────────────────────────────────────────────────────────────

class QuizState(str, Enum):
    GENERATING = "generating"
    AUDITING = "auditing"
    READY = "ready"
    FAILED = "failed"


# ── Audit Status ──────────────────────────────────────────────────────────────

class AuditStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


# ── User Roles ────────────────────────────────────────────────────────────────

class UserRole(str, Enum):
    TEACHER = "teacher"



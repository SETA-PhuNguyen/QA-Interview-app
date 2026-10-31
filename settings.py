from pathlib import Path


APP_DIR = Path(__file__).resolve().parent
ASSISTANT_HISTORY_FILE = APP_DIR / "assistant_history.json"
SKILL_FILE = APP_DIR / "qa_sdet_senior_interviewer_skill.md"
MODEL_NAME = "gemini-flash-lite-latest"

SCENARIO_QA_TOPIC = "Tình huống thực tế - QA"
SCENARIO_DEVELOPER_TOPIC = "Tình huống thực tế - Developer"
SCENARIO_TOPICS = [SCENARIO_QA_TOPIC, SCENARIO_DEVELOPER_TOPIC]

TOPICS = [
    *SCENARIO_TOPICS,
    "Level 0: Foundation",
    "Level 1: Core QA Skills",
    "Level 2: Defect Tracking",
    "Level 3: Performance Testing",
    "Level 4: Automation Testing",
    "Level 5: API Testing",
    "Level 6: Test Design & Planning",
    "Level 7: Test Management",
    "Level 8: AI & Intelligence",
    "Java Core",
    "Networking & Security",
    "Enterprise Stack & Messaging",
    "DevOps, Cloud & Architecture",
    "Observability & Tuning",
    "Design Patterns & Soft Skills",
]

WELCOME_MESSAGE = (
    "Chào bạn! Tôi là Senior SDET Interviewer của bạn. "
    "Nhấn **Nhận câu hỏi tiếp theo** để bắt đầu buổi luyện tập."
)

QUESTION_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "topic": {"type": "STRING", "enum": TOPICS},
        "difficulty": {"type": "STRING"},
        "question": {"type": "STRING"},
    },
    "required": ["topic", "difficulty", "question"],
}

FEEDBACK_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "topic": {"type": "STRING", "enum": TOPICS},
        "verdict": {"type": "STRING", "enum": ["PASSED", "FAILED / SUBSTANDARD"]},
        "progress_delta": {
            "type": "INTEGER",
            "minimum": -10,
            "maximum": 20,
        },
        "detailed_analysis": {"type": "STRING"},
        "best_practice_answer": {"type": "STRING"},
        "memory_hack": {"type": "STRING"},
        "next_topic": {"type": "STRING", "enum": TOPICS},
        "next_difficulty": {"type": "STRING"},
        "next_question": {"type": "STRING"},
    },
    "required": [
        "topic",
        "verdict",
        "progress_delta",
        "detailed_analysis",
        "best_practice_answer",
        "memory_hack",
        "next_topic",
        "next_difficulty",
        "next_question",
    ],
}

APP_RULES = """
Bạn phải tuân theo đầy đủ nội dung skill bên trên. Ứng dụng quản lý bảng điểm
và tự hiển thị bảng điểm sau mỗi câu trả lời, nên không đưa bảng điểm vào phần
feedback JSON.
Khi được yêu cầu đặt câu hỏi, chỉ hỏi đúng một câu kỹ thuật, chọn ngẫu nhiên
giữa các chủ đề Level 0-8, 14 enterprise modules, hoặc một tình huống thực tế
thuộc QA/Developer. Câu hỏi tình huống chỉ được thuộc một trong hai topic
"Tình huống thực tế - QA" hoặc "Tình huống thực tế - Developer"; không tạo
tình huống thuộc các topic khác. Nêu chính xác topic và độ khó.
Khi chấm câu trả lời, trả về đúng JSON theo schema được cung cấp: verdict chỉ
được là PASSED hoặc FAILED / SUBSTANDARD; progress_delta là +10 đến +20 khi
PASSED, và từ -10 đến 0 khi FAILED / SUBSTANDARD. Chọn chính xác một topic từ
danh sách schema. Mọi câu hỏi mới phải có topic, difficulty và question riêng.
Khi chấm câu trả lời, next_topic và next_difficulty phải mô tả rõ câu hỏi tiếp
theo; nếu câu hỏi hiện tại là tình huống thực tế, giữ nguyên topic QA hoặc
Developer đó. Mọi trường nội dung phải bằng tiếng Việt.
""".strip()


def load_system_prompt():
    if not SKILL_FILE.is_file():
        raise FileNotFoundError(f"Không tìm thấy file hướng dẫn: {SKILL_FILE.name}")
    skill_prompt = SKILL_FILE.read_text(encoding="utf-8")
    return f"{skill_prompt}\n\n--- Quy tắc tích hợp ứng dụng ---\n{APP_RULES}"

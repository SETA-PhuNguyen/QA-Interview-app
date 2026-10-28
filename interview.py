import json
import os

import httpx
from google import genai
from google.genai import types

from settings import FEEDBACK_SCHEMA, MODEL_NAME, SKILL_FILE, TOPICS, WELCOME_MESSAGE, load_system_prompt

API_TIMEOUT_MS = 45_000
MAX_CONTEXT_MESSAGES = 6
MAX_OUTPUT_TOKENS = 1_024
SCOREBOARD_MARKER = "### 📊 BẢNG ĐÁNH GIÁ ĐỘ THUẦN THỤC"
NEXT_QUESTION_MARKER = "### Câu hỏi tiếp theo"


def compact_message(message):
    content = message["content"]
    if message["role"] == "assistant" and SCOREBOARD_MARKER in content:
        before_scoreboard, after_scoreboard = content.split(SCOREBOARD_MARKER, 1)
        next_question_index = after_scoreboard.find(NEXT_QUESTION_MARKER)
        next_question = (
            after_scoreboard[next_question_index:]
            if next_question_index >= 0
            else ""
        )
        content = "\n\n".join(
            part for part in (before_scoreboard.strip(), next_question.strip()) if part
        )
    return content


def build_gemini_contents(messages, extra_user_prompt=None):
    contents = []
    for message in messages:
        if message["content"] == WELCOME_MESSAGE:
            continue
        role = "model" if message["role"] == "assistant" else "user"
        contents.append(
            types.Content(
                role=role,
                parts=[types.Part.from_text(text=compact_message(message))],
            )
        )

    if extra_user_prompt:
        contents.append(
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=extra_user_prompt)],
            )
        )
    return contents[-MAX_CONTEXT_MESSAGES:]


def generate_response(messages, extra_user_prompt, structured_feedback=False):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError(
            "Chưa tìm thấy GEMINI_API_KEY. Hãy điền key trong file .env "
            "rồi khởi động lại ứng dụng."
        )
    if not SKILL_FILE.is_file():
        raise FileNotFoundError(f"Không tìm thấy file hướng dẫn: {SKILL_FILE.name}")

    config = types.GenerateContentConfig(
        system_instruction=load_system_prompt(),
        max_output_tokens=MAX_OUTPUT_TOKENS,
    )
    if structured_feedback:
        config.response_mime_type = "application/json"
        config.response_schema = FEEDBACK_SCHEMA

    client = genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(
            timeout=API_TIMEOUT_MS,
            retry_options=types.HttpRetryOptions(attempts=1),
        ),
    )
    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=build_gemini_contents(messages, extra_user_prompt),
            config=config,
        )
    except httpx.TimeoutException as error:
        raise TimeoutError(
            f"Gemini không phản hồi trong {API_TIMEOUT_MS // 1000} giây. "
            "Hãy thử lại hoặc kiểm tra mạng, API key và model."
        ) from error
    if not response.text or not response.text.strip():
        raise ValueError("Gemini không trả về nội dung. Vui lòng thử lại.")
    return response.text.strip()


def parse_feedback(response_text):
    try:
        feedback = json.loads(response_text)
    except json.JSONDecodeError as error:
        raise ValueError(f"Gemini trả về feedback không đúng JSON: {error}") from error

    required = FEEDBACK_SCHEMA["required"]
    if not isinstance(feedback, dict) or any(key not in feedback for key in required):
        raise ValueError("Gemini trả về feedback thiếu trường theo schema.")
    if feedback["topic"] not in TOPICS:
        raise ValueError("Gemini trả về chủ đề không nằm trong danh sách theo dõi.")
    if feedback["verdict"] not in ("PASSED", "FAILED / SUBSTANDARD"):
        raise ValueError("Gemini trả về kết quả đánh giá không hợp lệ.")
    if isinstance(feedback["progress_delta"], bool) or not isinstance(
        feedback["progress_delta"], int
    ):
        raise ValueError("Gemini trả về mức thay đổi điểm không hợp lệ.")
    text_fields = (
        "detailed_analysis",
        "best_practice_answer",
        "memory_hack",
        "next_question",
    )
    if any(
        not isinstance(feedback[field], str) or not feedback[field].strip()
        for field in text_fields
    ):
        raise ValueError("Gemini trả về nội dung feedback chưa đầy đủ.")
    return feedback

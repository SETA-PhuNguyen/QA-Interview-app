import streamlit as st
from dotenv import load_dotenv
from google.genai.errors import APIError

from assistant_history import (
    AssistantHistoryError,
    append_answered_question,
    append_history_entry,
    load_assistant_history,
    remove_unanswered_questions,
    save_assistant_history,
)
from interview import generate_response, parse_feedback
from progress import (
    UNCLASSIFIED_TOPIC,
    build_question_history,
    build_scoreboard,
    topic_for_question,
)
from settings import APP_DIR, TOPICS, WELCOME_MESSAGE


load_dotenv(APP_DIR / ".env")
st.set_page_config(page_title="QA & SDET Interview Coach", page_icon="🎯", layout="wide")


def get_chat_messages():
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": WELCOME_MESSAGE}]
    return st.session_state.messages


def initialize_assistant_history():
    if "assistant_history" in st.session_state:
        return
    history = []
    try:
        history = load_assistant_history()
        completed_history = remove_unanswered_questions(history)
        if completed_history != history:
            try:
                history = save_assistant_history(completed_history)
            except AssistantHistoryError as error:
                history = completed_history
                st.session_state.assistant_history_error = str(error)
        st.session_state.assistant_history = history
        st.session_state.setdefault("assistant_history_error", None)
    except AssistantHistoryError as error:
        st.session_state.assistant_history = history
        st.session_state.assistant_history_error = str(error)


def persist_history_entry(content, kind, topic=None, question_id=None):
    if st.session_state.assistant_history_error:
        st.error(
            "Mục này chỉ còn trong phiên hiện tại vì file lịch sử không đọc được: "
            f"{st.session_state.assistant_history_error}"
        )
        return
    try:
        st.session_state.assistant_history = append_history_entry(
            st.session_state.assistant_history, content, kind, topic, question_id
        )
        return st.session_state.assistant_history[-1].get("id")
    except AssistantHistoryError as error:
        st.error(str(error))
        return None


def persist_answered_question(question, answer, topic):
    if st.session_state.assistant_history_error:
        st.error(
            "Câu hỏi và câu trả lời chỉ còn trong phiên hiện tại vì file lịch sử "
            f"không đọc được: {st.session_state.assistant_history_error}"
        )
        return None
    try:
        history, question_id = append_answered_question(
            st.session_state.assistant_history, question, answer, topic
        )
        st.session_state.assistant_history = history
        return question_id
    except AssistantHistoryError as error:
        st.error(str(error))
        return None


def render_topic_questions(topic, questions):
    st.markdown(f"**{topic}**")
    st.caption(f"{len(questions)} câu hỏi")
    with st.expander("Xem câu hỏi"):
        if not questions:
            st.caption("Chưa có câu hỏi.")
        for number, question in enumerate(questions, start=1):
            title = " ".join(question["content"].split())
            if len(title) > 68:
                title = f"{title[:65]}..."
            if st.button(
                f"{number}. {title}",
                key=f"history_question_{question['id']}",
                width="stretch",
            ):
                st.session_state.selected_history_question = question["id"]
                st.rerun()


def request_gemini(messages, prompt, structured_feedback=False):
    try:
        return generate_response(messages, prompt, structured_feedback)
    except APIError as error:
        if error.code == 504:
            st.error(
                "Gemini đã hết thời gian xử lý yêu cầu (504). App đang dùng "
                "model Flash Lite phản hồi nhanh hơn; hãy thử lại sau một chút. "
                "Nếu vẫn xảy ra, đây có thể là sự cố tạm thời phía Gemini API."
            )
        else:
            st.error(f"Gemini API trả về lỗi: {error}")
    except (ValueError, FileNotFoundError, TimeoutError) as error:
        st.error(str(error))
    return None


def render_feedback(feedback):
    verdict = feedback["verdict"]
    verdict_label = "✅ PASSED" if verdict == "PASSED" else "🛑 FAILED / SUBSTANDARD"
    st.markdown(f"### Evaluation Result: {verdict_label}")
    st.markdown(f"**Chủ đề:** {feedback['topic']}")
    st.markdown("### Detailed Analysis")
    st.markdown(feedback["detailed_analysis"])
    st.markdown("### Best Practice Answer")
    st.markdown(feedback["best_practice_answer"])
    st.markdown("### Memory Hacks (Mẹo ghi nhớ)")
    st.markdown(feedback["memory_hack"])

    topic = feedback["topic"]
    scoreboard = build_scoreboard(st.session_state.assistant_history)
    st.markdown(scoreboard)
    st.markdown("### Câu hỏi tiếp theo")
    st.markdown(feedback["next_question"])

    return (
        f"Evaluation Result: {verdict_label}\n\n"
        f"**Chủ đề:** {topic}\n\n"
        f"### Detailed Analysis\n{feedback['detailed_analysis']}\n\n"
        f"### Best Practice Answer\n{feedback['best_practice_answer']}\n\n"
        f"### Memory Hacks\n{feedback['memory_hack']}\n\n"
        f"{scoreboard}\n\n"
        f"### Câu hỏi tiếp theo\n{feedback['next_question']}"
    )


initialize_assistant_history()
messages = get_chat_messages()
question_history = build_question_history(st.session_state.assistant_history)

with st.sidebar:
    selected_view = st.segmented_control(
        "Mục",
        options=["Luyện tập", "Lịch sử"],
        default="Luyện tập",
        key="main_view",
        width="stretch",
    )

    st.subheader("📊 Tiến trình câu hỏi")
    questions_by_topic = {topic: [] for topic in TOPICS}
    questions_by_topic[UNCLASSIFIED_TOPIC] = []
    for question in question_history:
        questions_by_topic[question["topic"]].append(question)

    for topic in TOPICS:
        render_topic_questions(topic, questions_by_topic[topic])

    if questions_by_topic[UNCLASSIFIED_TOPIC]:
        render_topic_questions(
            UNCLASSIFIED_TOPIC, questions_by_topic[UNCLASSIFIED_TOPIC]
        )

st.title("🎯 QA & SDET Interview Coach")
if st.session_state.assistant_history_error:
    st.error(st.session_state.assistant_history_error)

selected_question_id = st.session_state.get("selected_history_question")
selected_question = next(
    (question for question in question_history if question["id"] == selected_question_id),
    None,
)
if selected_question:
    with st.container(border=True):
        st.subheader(f"Câu hỏi · {selected_question['topic']}")
        st.markdown(selected_question["content"])
        if selected_question["answer"]:
            st.markdown("#### Câu trả lời của bạn")
            st.markdown(selected_question["answer"])
        else:
            st.info("Bạn chưa trả lời câu hỏi này.")
        if selected_question["feedback"]:
            with st.expander("Xem đánh giá và đáp án tham khảo"):
                st.markdown(selected_question["feedback"])

if selected_view == "Lịch sử":
    st.subheader(f"Lịch sử câu hỏi đã lưu ({len(question_history)})")
    st.caption("Chọn một câu hỏi để xem câu trả lời và phần đánh giá của bạn.")
    if not question_history:
        st.info("Chưa có câu hỏi nào được lưu. Hãy bắt đầu luyện tập trước.")
    else:
        for question in question_history:
            with st.expander(question["content"]):
                st.caption(f"{question['topic']} · {question['created_at']}")
                if question["answer"]:
                    st.markdown("#### Câu trả lời của bạn")
                    st.markdown(question["answer"])
                else:
                    st.info("Bạn chưa trả lời câu hỏi này.")
                if question["feedback"]:
                    st.markdown("#### Đánh giá và đáp án tham khảo")
                    st.markdown(question["feedback"])
else:
    st.write(
        "Luyện phỏng vấn cá nhân với Gemini theo skill interviewer trong dự án. "
        "Tiến trình tự cập nhật sau mỗi câu trả lời."
    )

    for message in messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if st.button(
        "Nhận câu hỏi tiếp theo",
        type="primary",
        disabled=bool(st.session_state.get("pending_question")),
    ):
        with st.spinner("Gemini đang tạo câu hỏi (tối đa 45 giây)..."):
            question = request_gemini(
                messages,
                "Bắt đầu hoặc tiếp tục buổi phỏng vấn. Hãy chọn ngẫu nhiên một chủ đề "
                "QA/SDET và hỏi đúng một câu kỹ thuật. Trả lời bằng văn bản thuần, "
                "không dùng JSON, không thêm code fence hoặc đánh giá. Chỉ ghi chủ đề, "
                "độ khó và câu hỏi.",
            )
        if question:
            st.session_state.messages.append({"role": "assistant", "content": question})
            st.session_state.pending_question = {
                "content": question,
                "topic": topic_for_question(question),
            }
            st.rerun()

    pending_question = st.session_state.get("pending_question")
    if pending_question:
        st.caption("Hãy trả lời câu hỏi hiện tại trước khi nhận câu hỏi mới.")
    user_input = st.chat_input(
        "Nhập câu trả lời của bạn tại đây...",
        disabled=not pending_question,
    )
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        answer_question_id = persist_answered_question(
            pending_question["content"],
            user_input,
            pending_question["topic"],
        )
        st.session_state.pending_question = None
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Gemini đang đánh giá câu trả lời (tối đa 45 giây)..."):
                response_text = request_gemini(
                    st.session_state.messages,
                    "Đánh giá câu trả lời mới nhất của ứng viên theo skill interviewer. "
                    "Trả về JSON theo schema; đánh giá nghiêm khắc và hỏi tiếp đúng "
                    "một câu duy nhất.",
                    structured_feedback=True,
                )
            if response_text:
                try:
                    feedback = parse_feedback(response_text)
                except ValueError as error:
                    st.error(str(error))
                else:
                    rendered_response = render_feedback(feedback)
                    st.session_state.messages.append(
                        {"role": "assistant", "content": rendered_response}
                    )
                    if answer_question_id is not None:
                        persist_history_entry(
                            rendered_response,
                            "feedback",
                            question_id=answer_question_id,
                        )
                    st.session_state.pending_question = {
                        "content": feedback["next_question"],
                        "topic": topic_for_question(feedback["next_question"]),
                    }
                    st.rerun()

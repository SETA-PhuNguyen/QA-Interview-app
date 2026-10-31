from settings import SCENARIO_TOPICS, TOPICS


UNCLASSIFIED_TOPIC = "Chưa phân loại"


def topic_for_question(content):
    normalized_content = content.casefold()
    scenario_topic = next(
        (topic for topic in SCENARIO_TOPICS if topic.casefold() in normalized_content),
        None,
    )
    if scenario_topic:
        return scenario_topic
    return next(
        (topic for topic in TOPICS if topic.casefold() in normalized_content),
        UNCLASSIFIED_TOPIC,
    )


def build_question_history(history):
    questions = []
    questions_by_id = {}
    current_question = None

    for index, entry in enumerate(history):
        if entry["kind"] == "question":
            topic = entry.get("topic") or topic_for_question(entry["content"])
            if topic not in TOPICS:
                topic = UNCLASSIFIED_TOPIC
            question_id = entry.get("id", index)
            current_question = {
                "id": question_id,
                "topic": topic,
                "content": entry["content"],
                "difficulty": entry.get("difficulty"),
                "created_at": entry["created_at"],
                "answer": None,
                "feedback": None,
            }
            questions.append(current_question)
            questions_by_id[question_id] = current_question
        elif entry["kind"] in ("answer", "feedback"):
            question = questions_by_id.get(entry.get("question_id"), current_question)
            if not question:
                continue
            if entry["kind"] == "answer" and question["answer"] is None:
                question["answer"] = entry["content"]
            elif entry["kind"] == "feedback" and question["answer"] is not None:
                question["feedback"] = entry["content"]

    return [question for question in questions if question["answer"] is not None]

import json
import os
import tempfile
from datetime import datetime, timezone
from uuid import uuid4

from settings import ASSISTANT_HISTORY_FILE


class AssistantHistoryError(Exception):
    pass


def load_assistant_history():
    if not ASSISTANT_HISTORY_FILE.exists():
        return []

    try:
        with ASSISTANT_HISTORY_FILE.open("r", encoding="utf-8") as history_file:
            history = json.load(history_file)
    except (OSError, json.JSONDecodeError) as error:
        raise AssistantHistoryError(
            f"Không đọc được {ASSISTANT_HISTORY_FILE.name}: {error}"
        ) from error

    if not isinstance(history, list):
        raise AssistantHistoryError(
            f"{ASSISTANT_HISTORY_FILE.name} phải chứa một JSON array."
        )

    for entry in history:
        if (
            not isinstance(entry, dict)
            or entry.get("kind") not in ("question", "answer", "feedback")
            or not isinstance(entry.get("content"), str)
            or not isinstance(entry.get("created_at"), str)
            or ("topic" in entry and not isinstance(entry["topic"], str))
            or (
                "difficulty" in entry
                and not isinstance(entry["difficulty"], str)
            )
            or ("id" in entry and not isinstance(entry["id"], (str, int)))
            or (
                "question_id" in entry
                and not isinstance(entry["question_id"], (str, int))
            )
        ):
            raise AssistantHistoryError(
                f"{ASSISTANT_HISTORY_FILE.name} có mục lịch sử không hợp lệ."
            )
    return history


def remove_unanswered_questions(history):
    answered_question_ids = set()
    current_question_id = None

    for index, entry in enumerate(history):
        if entry["kind"] == "question":
            current_question_id = entry.get("id", index)
        elif entry["kind"] == "answer":
            question_id = entry.get("question_id", current_question_id)
            if question_id is not None:
                answered_question_ids.add(question_id)

    completed_history = []
    current_question_id = None
    for index, entry in enumerate(history):
        if entry["kind"] == "question":
            current_question_id = entry.get("id", index)
            if current_question_id in answered_question_ids:
                completed_history.append(entry)
        else:
            question_id = entry.get("question_id", current_question_id)
            if question_id in answered_question_ids:
                completed_history.append(entry)

    return completed_history


def save_assistant_history(history):
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=ASSISTANT_HISTORY_FILE.parent,
            prefix=f"{ASSISTANT_HISTORY_FILE.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            temporary_path = temporary_file.name
            json.dump(history, temporary_file, ensure_ascii=False, indent=2)
            temporary_file.write("\n")
        os.replace(temporary_path, ASSISTANT_HISTORY_FILE)
    except OSError as error:
        if temporary_path and os.path.exists(temporary_path):
            os.unlink(temporary_path)
        raise AssistantHistoryError(
            f"Không lưu được lịch sử vào {ASSISTANT_HISTORY_FILE.name}: {error}"
        ) from error
    return history


def append_history_entry(history, content, kind, topic=None, question_id=None):
    if kind not in ("question", "answer", "feedback"):
        raise ValueError(f"Loại phản hồi không hợp lệ: {kind}")

    entry = {
        "kind": kind,
        "content": content,
        "created_at": datetime.now(timezone.utc).astimezone().isoformat(
            timespec="seconds"
        ),
    }
    if kind == "question" and topic:
        entry["topic"] = topic
    if kind == "question":
        entry["id"] = uuid4().hex
    if kind in ("answer", "feedback") and question_id is not None:
        entry["question_id"] = question_id
    updated_history = [*history, entry]
    return save_assistant_history(updated_history)


def append_answered_question(history, question, answer, topic, difficulty=None):
    question_id = uuid4().hex
    created_at = datetime.now(timezone.utc).astimezone().isoformat(
        timespec="seconds"
    )
    updated_history = [
        *history,
        {
            "kind": "question",
            "content": question,
            "created_at": created_at,
            "topic": topic,
            "id": question_id,
            **({"difficulty": difficulty} if difficulty else {}),
        },
        {
            "kind": "answer",
            "content": answer,
            "created_at": created_at,
            "question_id": question_id,
        },
    ]
    return save_assistant_history(updated_history), question_id

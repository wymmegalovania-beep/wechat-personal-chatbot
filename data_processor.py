import json
import re
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional


LINE_PATTERNS = [
    re.compile(
        r"^\[(?P<ts>\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}(?::\d{2})?)\]\s*(?P<speaker>[^:：]+)[:：]\s*(?P<text>.+)$"
    ),
    re.compile(
        r"^(?P<ts>\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}(?::\d{2})?)\s*-\s*(?P<speaker>[^:：]+)[:：]\s*(?P<text>.+)$"
    ),
    re.compile(r"^(?P<speaker>[^:：]+)[:：]\s*(?P<text>.+)$"),
]

SYSTEM_PREFIXES = ("系统", "system", "消息记录", "撤回了一条消息")


def _is_system_line(text: str) -> bool:
    lower = text.strip().lower()
    return any(lower.startswith(prefix.lower()) for prefix in SYSTEM_PREFIXES)


def parse_chat_file(chat_file: str) -> List[Dict[str, str]]:
    messages: List[Dict[str, str]] = []
    for raw in Path(chat_file).read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        if _is_system_line(line):
            continue
        for pattern in LINE_PATTERNS:
            match = pattern.match(line)
            if match:
                groups = match.groupdict()
                text = groups["text"].strip()
                if text and not _is_system_line(text):
                    messages.append(
                        {
                            "timestamp": groups.get("ts") or "",
                            "speaker": groups["speaker"].strip(),
                            "text": text,
                        }
                    )
                break
    return messages


def infer_user_name(messages: List[Dict[str, str]]) -> Optional[str]:
    if not messages:
        return None
    speaker_counts = Counter(m["speaker"] for m in messages if m.get("speaker"))
    return speaker_counts.most_common(1)[0][0] if speaker_counts else None


def extract_examples(
    messages: List[Dict[str, str]],
    user_name: str,
    min_examples: int = 10,
    max_examples: int = 20,
) -> List[Dict[str, str]]:
    pairs: List[Dict[str, str]] = []
    for i in range(1, len(messages)):
        prev_msg = messages[i - 1]
        cur_msg = messages[i]
        if cur_msg["speaker"] != user_name:
            continue
        if prev_msg["speaker"] == user_name:
            continue
        pairs.append(
            {
                "input": prev_msg["text"],
                "reply": cur_msg["text"],
            }
        )
        if len(pairs) >= max_examples:
            break

    if len(pairs) < min_examples:
        fallback_user_msgs = [
            {"input": "（无明确上文）", "reply": m["text"]}
            for m in messages
            if m["speaker"] == user_name
        ]
        for item in fallback_user_msgs:
            if len(pairs) >= min(max_examples, min_examples):
                break
            if item not in pairs:
                pairs.append(item)
    return pairs[:max_examples]


def build_style_profile(messages: List[Dict[str, str]], user_name: str) -> Dict:
    user_msgs = [m["text"] for m in messages if m["speaker"] == user_name]
    total = len(user_msgs)
    if not user_msgs:
        return {
            "user_name": user_name,
            "message_count": 0,
            "avg_length": 0.0,
            "emoji_ratio": 0.0,
            "question_ratio": 0.0,
            "common_phrases": [],
        }

    avg_length = sum(len(m) for m in user_msgs) / total
    emoji_count = sum(1 for m in user_msgs if re.search(r"[\U0001F300-\U0001FAFF😂🤣😊😄😅😭👍🙏]", m))
    question_count = sum(1 for m in user_msgs if "?" in m or "？" in m)

    words = []
    for msg in user_msgs:
        msg_words = [w for w in re.split(r"[\s,，。.!！？?；;:：()\[\]“”\"'、]+", msg) if len(w) >= 2]
        words.extend(msg_words)

    common_phrases = [w for w, _ in Counter(words).most_common(8)]

    return {
        "user_name": user_name,
        "message_count": total,
        "avg_length": round(avg_length, 2),
        "emoji_ratio": round(emoji_count / total, 2),
        "question_ratio": round(question_count / total, 2),
        "common_phrases": common_phrases,
    }


def create_personal_profile(
    chat_file: str,
    user_name: Optional[str] = None,
    output_file: str = "personal_profile.json",
) -> Dict:
    messages = parse_chat_file(chat_file)
    if not messages:
        raise ValueError("No valid chat messages were found in the file.")

    resolved_user = user_name or infer_user_name(messages)
    if not resolved_user:
        raise ValueError("Unable to infer user name from chat history.")

    examples = extract_examples(messages, resolved_user)
    style_profile = build_style_profile(messages, resolved_user)
    profile = {
        "user_name": resolved_user,
        "style_profile": style_profile,
        "examples": examples[:5],
        "metadata": {
            "source_file": chat_file,
            "parsed_messages": len(messages),
        },
    }
    Path(output_file).write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")
    return profile

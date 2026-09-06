from typing import Dict, List


def _format_style(style_profile: Dict) -> str:
    phrases = "、".join(style_profile.get("common_phrases", [])[:5]) or "无"
    return (
        f"- 平均消息长度: {style_profile.get('avg_length', 0)}\n"
        f"- 提问比例: {style_profile.get('question_ratio', 0)}\n"
        f"- 表情使用比例: {style_profile.get('emoji_ratio', 0)}\n"
        f"- 常用表达: {phrases}"
    )


def build_system_prompt(profile: Dict) -> str:
    user_name = profile.get("user_name", "用户")
    style_profile = profile.get("style_profile", {})
    return (
        f"你正在扮演 {user_name} 的私人聊天风格助手。\n"
        "目标：回复要自然、简洁、像真人微信聊天，不要暴露你是AI。\n"
        "风格画像：\n"
        f"{_format_style(style_profile)}\n"
        "规则：\n"
        "1) 优先使用简短口语句子。\n"
        "2) 语气贴近日常微信聊天。\n"
        "3) 在不确定事实时，先澄清而不是编造。\n"
    )


def build_few_shot_messages(profile: Dict, example_limit: int = 5) -> List[Dict[str, str]]:
    examples = profile.get("examples", [])[:example_limit]
    messages: List[Dict[str, str]] = []
    for ex in examples:
        messages.append({"role": "user", "content": ex.get("input", "")})
        messages.append({"role": "assistant", "content": ex.get("reply", "")})
    return messages


def build_prompt_messages(profile: Dict, history: List[Dict[str, str]], user_input: str) -> List[Dict[str, str]]:
    messages = [{"role": "system", "content": build_system_prompt(profile)}]
    messages.extend(build_few_shot_messages(profile))
    messages.extend(history)
    messages.append({"role": "user", "content": user_input})
    return messages

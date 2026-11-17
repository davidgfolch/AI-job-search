from ..config import get_skill_system_prompt, get_learning_path_system_prompt


def build_skill_prompt_messages(skill_name: str, context: str) -> list[dict]:
    context_str = f"\nContext (related technologies found in jobs): {context}" if context else ""
    user_message = f"Skill: {skill_name}{context_str}\n\nProvide a deep technical description."
    return [
        {"role": "system", "content": get_skill_system_prompt()},
        {"role": "user", "content": user_message}
    ]


def build_learning_path_prompt_messages(skill_name: str, context: str = "") -> list[dict]:
    context_str = f"\nContext (related technologies found in jobs): {context}" if context else ""
    user_message = f"Skill: {skill_name}{context_str}\n\nProvide the learning path."
    return [
        {"role": "system", "content": get_learning_path_system_prompt()},
        {"role": "user", "content": user_message}
    ]


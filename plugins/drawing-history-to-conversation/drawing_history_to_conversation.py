import re


try:
    from workflow.decorators import input_slot, output_slot, script_meta
except ImportError:
    def passthrough_decorator(*args, **kwargs):
        return lambda function: function

    input_slot = output_slot = script_meta = passthrough_decorator


CONVERSATION_HEADER = re.compile(
    r"(user|ai|assistant)[:：]\s*([0-9]+(?:\s*[,，]\s*[0-9]+)*)?\s*"
)
HISTORY_HEADER = re.compile(
    r"\[([0-9]+)\]\s*(用户|user|ai|assistant)\s*[·・]\s*"
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}[ T][0-9]{2}:[0-9]{2}"
    r"(?::[0-9]{2})?(?:[.,][0-9]+)?\s*",
    re.IGNORECASE,
)
IMAGE_REFERENCE = re.compile(r"\[图\s*([0-9]+)\]")
CANCELLED = re.compile(
    r"(?:Generation cancel(?:led|ed)|生成已取消|生成取消|已取消)[.!。]?",
    re.IGNORECASE,
)
FAILED = re.compile(
    r"\[生成失败(?:[:：][^\]]*)?\]|"
    r"^(?:Couldn't|Could not) generate content\b|^Generation failed\b",
    re.IGNORECASE,
)


def trim_blank_lines(lines):
    start = 0
    end = len(lines)
    while start < end and not lines[start].strip():
        start += 1
    while end > start and not lines[end - 1].strip():
        end -= 1
    return "\n".join(lines[start:end])


def read_history(text):
    messages = []
    for line in text.splitlines():
        header = HISTORY_HEADER.fullmatch(line.strip(" \t\u00a0\ufeff\u200b"))
        if header:
            sequence, role = header.groups()
            messages.append({
                "sequence": sequence,
                "role": "user" if role.lower() in ("用户", "user") else "ai",
                "lines": [],
            })
        elif messages:
            messages[-1]["lines"].append(line)
        elif line.strip(" \t\u00a0\ufeff\u200b"):
            raise ValueError("输入须为 user:/ai: 格式，或以 [序号] 用户 · 时间 开头的绘画历史原文。")
    if not messages:
        raise ValueError("未找到绘画历史消息，请输入完整的会话历史【原始】单元格。")
    return messages


def image_numbers(text):
    numbers = list(dict.fromkeys(int(match.group(1)) for match in IMAGE_REFERENCE.finditer(text)))
    if any(number < 1 for number in numbers):
        raise ValueError("图片编号必须为正整数。")
    return numbers


def normalize_input(text):
    if not isinstance(text, str):
        raise ValueError("History / Conversation 必须是文本。")

    first_line = next((line for line in text.splitlines() if line.strip()), "")
    if not first_line or CONVERSATION_HEADER.fullmatch(first_line.strip()):
        return text, []

    messages = read_history(text)
    converted = []
    warnings = []
    declared_images = set()
    pending_user = None

    for message in messages:
        body = trim_blank_lines(message["lines"])
        images = [number for number in image_numbers(body) if number not in declared_images]
        if message["role"] == "user":
            pending_user = {"role": "user", "images": images, "text": body}
            converted.append(pending_user)
            declared_images.update(images)
            continue

        cancelled = CANCELLED.fullmatch(body.strip()) is not None
        failed = FAILED.search(body.strip()) is not None
        if (cancelled or failed) and images:
            raise ValueError(f"第 {message['sequence']} 条 AI 消息同时包含失败/取消和新返图，无法确定状态。")

        if images:
            converted.append({"role": "ai", "images": images, "text": ""})
            declared_images.update(images)
            pending_user = None
        elif cancelled or failed:
            status = "cancelled" if cancelled else "failed"
            if pending_user is None:
                warnings.append(
                    f"第 {message['sequence']} 条 AI {status} 事件没有可归属的待处理用户请求，已省略。"
                )
            else:
                pending_user["status"] = status
                pending_user = None

    if not converted or converted[-1]["role"] != "user" or "status" in converted[-1]:
        raise ValueError("绘画历史须以本轮待执行的用户请求结束；请追加真实的本轮请求，不要补造消息。")

    lines = []
    for message in converted:
        numbers = ", ".join(str(number) for number in message["images"])
        lines.append(f"{message['role']}:" + (f" {numbers}" if numbers else ""))
        if message["text"]:
            lines.append(message["text"])
        if "status" in message:
            lines.append(f"status: {message['status']}")
    return "\n".join(lines), warnings


@script_meta(display="Drawing History to Conversation")
@input_slot(index=0, label="History / Conversation", name="text", value_type="string")
@output_slot(index=0, label="Conversation", name="conversation", value_type="string")
@output_slot(index=1, label="Warnings", name="warnings", value_type="string")
def run(inputs):
    if "text" not in inputs:
        return {"conversation": "", "warnings": ""}
    conversation, warnings = normalize_input(inputs["text"])
    return {"conversation": conversation, "warnings": "\n".join(warnings)}

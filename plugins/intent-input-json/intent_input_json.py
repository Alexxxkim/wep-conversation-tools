import json
import re


try:
    from workflow.decorators import input_slot, output_slot, script_meta
except ImportError:
    def passthrough_decorator(*args, **kwargs):
        return lambda function: function

    input_slot = output_slot = script_meta = passthrough_decorator


HEADER = re.compile(r"(user|ai|assistant)[:：]\s*([0-9]+(?:\s*[,，]\s*[0-9]+)*)?\s*")
STATUS = re.compile(r"status[:：]\s*(.*?)\s*")
IMAGE_REFERENCE = re.compile(r"\[图\s*([0-9]+)\]")
REGION = re.compile(r"\[\s*locale\s*=\s*([^\s\[\]=]+)\s*\]")
STYLE = re.compile(r"style\s*[:：]\s*(.*?)\s*", re.IGNORECASE | re.DOTALL)


def parse_region(region):
    if region is None:
        return None
    if not isinstance(region, str):
        raise ValueError("Region 必须是文本，格式为 [locale=en-AU]。")
    if not region.strip():
        return None
    match = REGION.fullmatch(region.strip())
    if not match:
        raise ValueError("Region 格式须为 [locale=en-AU]，locale 不能为空。")
    return {"locale": match.group(1)}


def parse_style(style):
    if style is None:
        return None
    if not isinstance(style, str):
        raise ValueError("Style 必须是文本，格式为 style: cartoon。")
    if not style.strip():
        return None
    match = STYLE.fullmatch(style.strip())
    if not match:
        raise ValueError("Style 格式须为 style: cartoon。")
    return match.group(1) or None


def parse_conversation(conversation):
    if not isinstance(conversation, str):
        raise ValueError("Conversation 必须是文本。")

    messages = []
    for line in conversation.splitlines():
        header = HEADER.fullmatch(line.strip())
        if header:
            role, numbers = header.groups()
            if role == "ai":
                role = "assistant"
            images = [int(number) for number in re.split(r"[,，]", numbers)] if numbers else []
            messages.append({"role": role, "images": images, "lines": []})
            continue

        if not messages:
            if line.strip():
                raise ValueError("请以 user: 或 ai: 消息标题开头。")
            continue

        status_match = STATUS.fullmatch(line.strip())
        if status_match:
            message = messages[-1]
            status = status_match.group(1)
            if message["role"] != "user":
                raise ValueError("status 只能标记所属的 user 请求。")
            if status not in ("cancelled", "failed"):
                raise ValueError("status 只能填写 cancelled 或 failed；成功返图无需状态。")
            if "status" in message:
                raise ValueError("同一条 user 请求只能填写一次 status。")
            message["status"] = status
        else:
            messages[-1]["lines"].append(line)

    messages = [
        message for message in messages
        if message["role"] != "assistant"
        or message["images"]
        or "\n".join(message["lines"]).strip()
    ]
    if not messages or messages[-1]["role"] != "user":
        raise ValueError("最后一条消息必须是本轮的 user:。")
    if "status" in messages[-1]:
        raise ValueError("本轮 user 请求尚未执行，不应填写 status；请追加本轮请求。")

    image_ids = {}
    preceding_user = None
    for message in messages:
        if message["role"] == "user":
            preceding_user = message
        elif message["images"] and preceding_user and "status" in preceding_user:
            raise ValueError("已标记 cancelled 或 failed 的请求不能同时声明成功返图。")

    for message in reversed(messages):
        for number in message["images"]:
            if number < 1 or number in image_ids:
                raise ValueError(f"图片编号必须为正整数，且只声明一次：{number}")
            image_ids[number] = f"image{len(image_ids) + 1}"

    def replace_reference(match):
        number = int(match.group(1))
        if number not in image_ids:
            raise ValueError(f"图片引用未声明：{match.group(0)}")
        return f"[{image_ids[number]}]"

    history = []
    latest_result_id = None
    for message in messages:
        attachments = [
            {"id": image_ids[number], "type": "image"}
            for number in message["images"]
        ]
        entry = {
            "role": message["role"],
            "text": IMAGE_REFERENCE.sub(
                replace_reference, "\n".join(message["lines"]).strip("\n")
            ),
            "attachments": attachments,
        }
        if "status" in message:
            entry["status"] = message["status"]
        history.append(entry)
        if message["role"] == "assistant" and attachments:
            latest_result_id = attachments[0]["id"]

    current_request = history.pop()
    del current_request["role"]
    payload = {"current_request": current_request}
    if latest_result_id is not None:
        payload["latest_result_id"] = latest_result_id
    payload["history"] = history
    return payload


@script_meta(display="Intent Input JSON")
@input_slot(index=0, label="Conversation", name="conversation", value_type="string")
@input_slot(index=1, label="Region", name="region", value_type="string")
@input_slot(index=2, label="Style", name="style", value_type="string")
@output_slot(index=0, label="JSON", name="json", value_type="string")
def run(inputs):
    if "conversation" not in inputs:
        return {"json": ""}
    payload = parse_conversation(inputs["conversation"])
    style = parse_style(inputs.get("style"))
    if style is not None:
        payload["style"] = style
    region = parse_region(inputs.get("region"))
    if region is not None:
        payload["region"] = region
    return {"json": json.dumps(payload, ensure_ascii=False, indent=2)}

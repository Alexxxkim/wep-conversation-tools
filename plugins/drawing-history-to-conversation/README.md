# Drawing History to Conversation — WEP

版本：`1.2.0`（沿用现有源码版本；本包不改转换逻辑）。

把 `[序号] 用户 · 时间` / `[序号] AI · 时间` 格式的原始绘画历史转成 `user:` / `ai:` 格式的 Conversation。也可原样透传已整理好的 Conversation。

## 安装与端口

在 WEP 中添加 **Script → Inline Python**，粘贴 [drawing_history_to_conversation.py](drawing_history_to_conversation.py) 的完整内容，包括装饰器。

| 方向 | 标签 | 内部名称 | 类型 | 连接 |
| --- | --- | --- | --- | --- |
| 输入 | History / Conversation | `text` | string | 原始历史文本或 Conversation |
| 输出 | Conversation | `conversation` | string | Intent Input JSON 的 Conversation |
| 输出 | Warnings | `warnings` | string | 可选文本预览，不接 JSON 解析器 |

节点显示名为 `Drawing History to Conversation`，可在工作流里手动改成「绘画历史转换 · Conversation」。这是 WEP 脚本，不是 ComfyUI 插件。WEP 注册依赖平台提供的 `workflow.decorators`，本地运行会使用无操作装饰器兼容转换逻辑。

## 规则与边界

1. 第一条非空行已经是 `user:`、`ai:` 或 `assistant:` 标题时，整段原样透传，不清理、不重新校验。
2. 对原始绘画历史移除消息序号和时间戳；用户正文、Create / Make 前缀、大小写、错字、行内空格及正文内部换行保持原样。仅去除各消息正文前后的历史分隔空行。
3. `[图N]` / `[图 N]` 首次出现时登记为该消息的图片；后续引用不重复声明。AI 消息里的新图输出为 `ai: N`，省略其文字。图片编号必须为正整数。
4. 明确取消事件转成前一待处理用户请求的 `status: cancelled`；明确失败事件转成 `status: failed`。没有明确状态或新图时，不推测 AI 成功、失败或取消。
5. 孤立的取消或失败事件省略，并写入 Warnings。失败/取消和同一 AI 消息中的新返图冲突时，报错。
6. 原始绘画历史必须以真实的本轮待执行用户请求结束，否则报错，不补造请求。已是 Conversation 的输入由下游解析器校验。
7. 输入未连接时返回两个空字符串；空白字符串原样透传。非文本输入报错。

只处理文本和图片编号，不联网、不上传图片、不调用模型。

## 虚构示例

输入见 [examples/history.txt](examples/history.txt)：

```text
[1] 用户 · 2026-01-01 09:00:00
Create a sticker of a cat wearing a blue hat

[2] AI · 2026-01-01 09:00:01
Here is the sticker. [图1]

[3] 用户 · 2026-01-01 09:01:00
把 [图1] 的帽子改成红色
```

输出见 [examples/conversation.txt](examples/conversation.txt)：

```text
user:
Create a sticker of a cat wearing a blue hat
ai: 1
user:
把 [图1] 的帽子改成红色
```

## 本地使用与测试

需要 Python 3.9+，不需要额外安装第三方依赖。在本 README 所在目录执行：

```sh
python3 -B -m unittest discover -s tests -v
```

本地 Python 用法：

```python
from drawing_history_to_conversation import run

result = run({"text": "[1] 用户 · 2026-01-01 09:00:00\n画一只猫"})
print(result["conversation"])
print(result["warnings"])
```

测试与示例均为虚构数据，不包含真实会话或完整工作流。本包未指定开源许可证；Public 仓库不等于已授权自由修改和分发，发布前请确认代码权属与许可证。

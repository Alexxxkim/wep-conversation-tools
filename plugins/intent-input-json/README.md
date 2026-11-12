# Intent Input JSON — WEP

公共打包版本：`1.0.0`（采用现有包含 Region / Style 的源码；不改解析逻辑）。

把 Conversation 文本转换为 JSON 字符串，包含 `current_request`、`history`、可选的 `latest_result_id`、`style`、`region`。

## 安装与端口

在 WEP 中添加 **Script → Inline Python**，粘贴 [intent_input_json.py](intent_input_json.py) 的完整内容，包括装饰器。

| 方向 | 标签 | 内部名称 | 类型 | 说明 |
| --- | --- | --- | --- | --- |
| 输入 0 | Conversation | `conversation` | string | 消息文本；可接绘画历史转换节点的 Conversation |
| 输入 1 | Region | `region` | string | 可选，例如 `[locale=zh-CN]` |
| 输入 2 | Style | `style` | string | 可选，例如 `style: cartoon` |
| 输出 0 | JSON | `json` | string | 格式化 JSON，可接文本预览或下游文本输入 |

这是 WEP 脚本，不是 ComfyUI 插件。WEP 注册依赖平台提供的 `workflow.decorators`，本地运行会使用无操作装饰器兼容解析逻辑。Region 和 Style 可以单独接入，也可以都不接入。

## Conversation 格式

按从旧到新的顺序填写消息；标题独占一行，最后一条有效消息必须是本轮 `user:` 请求。

```text
user: 1
给 [图1] 里的猫戴上帽子
ai: 2
user:
把 [图2] 的帽子改成红色
```

- 支持 `user:`、`ai:` 和兼容写法 `assistant:`；AI 角色在 JSON 中输出为 `assistant`。
- 图片在所属消息标题中声明一次，多图写成 `user: 1, 2`；支持中文冒号和逗号。正文中的 `[图1]` / `[图 1]` 替换成对应的 `[imageN]`。
- 图片 ID 从最新消息向前分配，同一消息内按声明顺序分配；历史消息仍按时间正序输出。最近一次 AI 返图的首张图片写入 `latest_result_id`。
- 图片编号必须为正整数且不能重复声明；未声明图片的正文引用会报错。普通正文数字不登记为附件。
- 历史用户请求可另起一行写 `status: cancelled` 或 `status: failed`；不允许其他状态、重复状态、AI 状态或本轮状态。状态与同一请求的成功返图冲突时报错。
- 连续用户消息保留为独立请求，不合并、不推测状态。没有正文也没有图片的空 AI 消息会被省略。
- Conversation 输入缺失时返回空 JSON 字符串；已连接但输入为空、不合法或非文本时，报错。

## Region / Style 格式

```text
[locale=zh-CN]
```

Region 提取为顶层 `"region": {"locale": "zh-CN"}`，不推测默认地区。接受方括号内部和等号两侧的空白；非空输入格式不匹配时，报错。

```text
style: cartoon
```

Style 提取为顶层 `"style": "cartoon"`。前缀不区分大小写，支持中文冒号；风格正文去除首尾空白，保留内部空白、换行及大小写，不限制风格名称。

Region / Style 未连接、为 `None`、空字符串或仅空白时省略对应字段。`style:` 冒号后没有正文也会省略 Style。

## 虚构示例

完整输入见 [examples/inputs.json](examples/inputs.json)，预期输出见 [examples/output.json](examples/output.json)。单轮输入：

```python
from intent_input_json import run

result = run({
    "conversation": "user:\n画一只猫",
    "region": "[locale=zh-CN]",
    "style": "style: cartoon",
})
print(result["json"])
```

输出：

```json
{
  "current_request": {
    "text": "画一只猫",
    "attachments": []
  },
  "history": [],
  "style": "cartoon",
  "region": {
    "locale": "zh-CN"
  }
}
```

节点只处理文本与附件 ID，JSON 的 attachments 不包含图片像素。不会上传、下载图片或调用模型。

## 本地测试

需要 Python 3.9+，不需要额外安装第三方依赖。在本 README 所在目录执行：

```sh
python3 -B -m unittest discover -s tests -v
```

测试与示例均为虚构数据，不包含真实会话或完整工作流。本包未指定开源许可证；Public 仓库不等于已授权自由修改和分发，发布前请确认代码权属与许可证。

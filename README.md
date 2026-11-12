# WEP Conversation Tools

两个可独立使用的 WEP **Script / Inline Python** 节点，把绘画历史整理成 Conversation，再转换为下游可使用的 JSON。

Two standalone WEP Inline Python scripts for converting drawing history into conversations and structured JSON. Runtime logic uses only the Python standard library; WEP node registration requires the host-provided `workflow.decorators`.

## 包含的节点

| 节点 | 源码 | 作用 |
| --- | --- | --- |
| Drawing History to Conversation（绘画历史转换） | [drawing_history_to_conversation.py](plugins/drawing-history-to-conversation/drawing_history_to_conversation.py) | 原始绘画历史 → Conversation；同时输出 Warnings |
| Intent Input JSON | [intent_input_json.py](plugins/intent-input-json/intent_input_json.py) | Conversation + 可选 Region / Style → JSON 字符串 |

这是截图所示 **WEP 脚本节点**的源码包，**不是 ComfyUI `custom_nodes` 插件**，也不是浏览器扩展或可通过 `pip install` 安装的包。没有 WEP 环境时仍可在本地调用转换函数，但不会出现 WEP 节点界面。未验证其他工作流平台的节点兼容性。

## 在 WEP 中使用

1. 添加一个 **Script** 节点，选择 **Inline Python**。
2. 打开绘画历史转换的 `.py` 文件，复制全部内容，包括装饰器，粘贴到节点中。
3. 再添加一个 **Script / Inline Python** 节点，粘贴 Intent Input JSON 的完整 `.py` 文件。
4. 确认端口按下图连接；Region 和 Style 可不连接。

```text
历史对话 Text
  → Drawing History to Conversation.text
      conversation → Intent Input JSON.conversation
      warnings     → 文本预览（可选）

地区文本 [locale=zh-CN] → Intent Input JSON.region（可选）
风格文本 style: cartoon → Intent Input JSON.style（可选）

Intent Input JSON.json → JSON 预览 / 下游 LLM 的文本输入
```

`Warnings` 是提示文本，不要连接到 Conversation 或 JSON 解析器。两个脚本只处理文本与图片编号，**不上传图片、不调用模型、不执行网络请求**。图片内容仍需在工作流中另行传入。

## 本地验证

需要 Python 3.9 或更新版本。本包已在 Python 3.9.6 上验证；无需额外安装第三方依赖。在本 README 所在目录执行：

```sh
python3 -B -m unittest discover -s plugins/drawing-history-to-conversation/tests -v
python3 -B -m unittest discover -s plugins/intent-input-json/tests -v
python3 -B -m unittest discover -s tests -v
```

这些测试验证转换逻辑与两节点串联，不代表已在每个 WEP 版本中验证界面行为。各插件目录内提供接口说明、独立测试和虚构示例。

## 公开发布范围

- 本包只包含两个节点及其公开说明、测试、虚构示例。
- 不包含真实用户历史、业务 PE、完整工作流、内网地址、节点 ID、API Key 或账户配置。
- GitHub 上传步骤见 [PUBLISH_TO_GITHUB.md](PUBLISH_TO_GITHUB.md)。
- 本包未指定开源许可证。公开可见不等于授权他人自由修改和分发；发布前请确认代码权属，并由有权人选择许可证。若代码来自公司项目，须先确认有权公开。

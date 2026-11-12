# ComfyUI Conversation Tools

三个 ComfyUI **Custom Node**：绘画历史 → Conversation → 意图输入 JSON，以及五路风格 PE 选择器。仓库同时保留原来的两个 WEP **Script / Inline Python** 脚本，转换逻辑保持一致。

Three ComfyUI custom nodes for drawing history conversion, structured intent JSON, and lazy style-based PE selection, with the original standalone WEP Inline Python scripts preserved. No additional Python dependencies are required.

## 包含的节点

| ComfyUI 节点 | 注册名称 | 作用 |
| --- | --- | --- |
| Drawing History to Conversation · 绘画历史转换 | `DMCanvasDrawingHistoryToConversation` | 原始绘画历史 → Conversation；同时输出 Warnings |
| Intent Input JSON | `DMCanvasIntentInputJSONWithMetadata` | Conversation + 可选 Region / Style → JSON 字符串 |
| Style Selector · 风格选择器 | `DMCanvasStyleSelector` | 根据风格从 cutout / emoji / retro / cartoon / empty 选一路 PE 文本 |

ComfyUI 入口是仓库根目录的 [__init__.py](__init__.py)，节点注册在 [nodes.py](nodes.py)。前两个节点在 `DM Canvas/Conversation` 分类下；风格选择器在 `DM Canvas/Style` 分类下，实现见 [style_selector.py](style_selector.py)，接线说明见 [STYLE_SELECTOR.md](STYLE_SELECTOR.md)。Intent 节点使用独立注册名称，避免覆盖早期只支持 Conversation 的 `DMCanvasIntentInputJSON` 插件。

## 在 ByteArtist 插件库安装

如果使用 Git 仓库下载 Custom Node 的入口，填写：

- 仓库地址：`https://github.com/Alexxxkim/wep-conversation-tools.git`
- 模式：`branch`
- Branch：`main`

也可以选择 `commit` 模式并留空，由下载入口取最新提交；固定 commit 时，必须使用**包含根目录 `__init__.py` 和 `nodes.py` 的新版提交**，旧的纯 WEP 提交不能作为 ComfyUI 插件加载。

下载 / 更新后，按平台提供的操作安装到当前工作台，并重启或重新加载 ComfyUI 后端，再刷新页面、搜索上述节点。仅刷新网页不一定能加载新安装的 Python 节点。详细步骤与排查见 [BYTEARTIST_INSTALL.md](BYTEARTIST_INSTALL.md)。未在 ByteArtist 实际下载、安装或执行工作流。

## 在本地 ComfyUI 安装

在 ComfyUI 的 `custom_nodes` 目录执行：

```sh
git clone https://github.com/Alexxxkim/wep-conversation-tools.git
```

或下载仓库 ZIP，解压后将**整个仓库文件夹**放入 `ComfyUI/custom_nodes/`。结构必须是：

```text
ComfyUI/custom_nodes/wep-conversation-tools/
├── __init__.py
├── nodes.py
├── style_selector.py
└── plugins/
    ├── drawing-history-to-conversation/drawing_history_to_conversation.py
    └── intent-input-json/intent_input_json.py
```

不要只复制 `__init__.py`、`nodes.py`、`style_selector.py` 或单个 `plugins/` 子目录；不要在插件目录里多套一层同名文件夹。无需 `pip install`，安装后重启 ComfyUI 后端。风格选择器需要支持 Lazy Evaluation 的 ComfyUI 后端。

## ComfyUI 节点接口与连接

| 节点 | 输入 | 输出 |
| --- | --- | --- |
| 绘画历史转换 | `text`（STRING） | `conversation`、`warnings`（STRING） |
| Intent Input JSON | `conversation`（STRING）；可选 `region`、`style`（STRING） | `json`（STRING） |
| 风格选择器 | `style`（STRING）；可选 `cutout`、`emoji`、`retro`、`cartoon`、`empty`（STRING） | `out`（STRING） |

绘画历史转换的 `text`，以及 Intent Input JSON 的 `conversation`、`region`、`style` 均默认显示为 **STRING 输入接口**（`forceInput: true`），不再显示节点内文本框，也不需要手动执行 Convert widget to input。请连接上游 Text / String 等节点；`text` 和 `conversation` 必须连接，`region` 和 `style` 仍可不连接，未连接时省略对应 JSON 字段。

更新插件后重启或重新加载 ComfyUI 后端，再添加新版节点。旧工作流中保存的文本控件和节点布局不保证自动迁移；先保留原文本与连接信息，再重新添加节点并接线，不要把原文本当成已自动转入输入端口。

风格选择器的输入仍支持直接填写文本，或通过节点菜单转换为输入端口，详见 [STYLE_SELECTOR.md](STYLE_SELECTOR.md)。

```text
历史对话文本 → 绘画历史转换.text
                  conversation → Intent Input JSON.conversation → JSON 预览 / 下游 LLM
                  warnings     → 文本预览（可选）

[locale=zh-CN] → Intent Input JSON.region（可选）
style: cartoon → Intent Input JSON.style（可选）
```

Region / Style 留空时省略对应 JSON 字段。图片编号、取消 / 失败状态、用户正文保留和异常输入校验沿用原有逻辑。绘画历史为空时返回空字符串；Intent 的 Conversation 为空或格式不合法时仍报错，不补造用户请求。

风格选择器将原来的 Switch＋Merge 合并为一个节点：`Cutout` → `cutout`，`3D Emoji` → `emoji`，`Retro Game` → `retro`，`Cartoon` → `cartoon`，空风格 → `empty`。支持名称大小写与常见紧凑别名、`style: cartoon` 字段文本。未知风格报错，不自动回退；选中 PE 原样输出。五路 PE 输入为 lazy，仅请求选中的输入。完整规则与替换接线见 [STYLE_SELECTOR.md](STYLE_SELECTOR.md)。

三个节点只处理文本与图片编号，**不上传图片、不调用模型、不执行网络请求**。图片内容仍需在工作流中另行传入。

## 在 WEP 中使用

1. 添加一个 **Script** 节点，选择 **Inline Python**。
2. 打开绘画历史转换的 `.py` 文件，复制全部内容，包括装饰器，粘贴到节点中。
3. 再添加一个 **Script / Inline Python** 节点，粘贴 Intent Input JSON 的完整 `.py` 文件。
4. 确认端口按下图连接；Region 和 Style 可不连接。

WEP 需要平台提供的 `workflow.decorators`。原始脚本分别是 [drawing_history_to_conversation.py](plugins/drawing-history-to-conversation/drawing_history_to_conversation.py) 和 [intent_input_json.py](plugins/intent-input-json/intent_input_json.py)，仍可完整复制到 Inline Python。各子目录及之前的独立 WEP ZIP 不是单独的 ComfyUI 安装包。

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

这些测试验证转换逻辑、两节点串联，以及按 ComfyUI 的包加载方式导入、三个节点注册、STRING 输入输出、可选字段、风格路由和 Lazy Evaluation 请求协议；不代表已在实际 ComfyUI 调度器或每个 ComfyUI / WEP / ByteArtist 版本中实测界面或安装行为。各插件目录内提供接口说明、独立测试和虚构示例。

## 公开发布范围

- 本包只包含三个节点及其公开说明、测试、虚构示例。
- 不包含真实用户历史、业务 PE、完整工作流、内网地址、节点 ID、API Key 或账户配置。
- GitHub 上传步骤见 [PUBLISH_TO_GITHUB.md](PUBLISH_TO_GITHUB.md)。
- 本包未指定开源许可证。公开可见不等于授权他人自由修改和分发；发布前请确认代码权属，并由有权人选择许可证。若代码来自公司项目，须先确认有权公开。

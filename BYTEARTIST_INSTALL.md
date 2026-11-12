# ByteArtist / ComfyUI 安装说明

## Git 插件下载入口填写

| 字段 | 内容 |
| --- | --- |
| 仓库地址 | `https://github.com/Alexxxkim/wep-conversation-tools.git` |
| 下载模式 | `branch` |
| Branch | `main` |

不需要同时填写 branch 和 commit。若切换为 `commit` 模式，截图所示入口支持留空取最新提交；若要锁定版本，填写新版完整提交 ID，而不是任意旧提交。

**最早的提交只包含 WEP Inline Python 脚本，不能通过 ComfyUI Custom Node 入口加载。** 最新版仓库根目录有 `__init__.py`，导出 `NODE_CLASS_MAPPINGS` 和 `NODE_DISPLAY_NAME_MAPPINGS`，并由 `nodes.py` 注册三个节点。下载包含 `style_selector.py` 的新版 `main` 才能使用风格选择器。

## 下载后的操作

1. 在插件下载页面下载 / 更新仓库，等待平台显示下载成功。
2. 按平台实际提供的操作，将插件安装或应用到当前工作台。如果插件库只完成下载，还需要执行平台的后续安装操作。
3. 重启或重新加载当前 ComfyUI 后端，再刷新工作流页面。不要仅靠刷新网页加载新 Python 节点。
4. 添加节点时，在 `DM Canvas/Conversation` 分类中搜索：
   - `Drawing History to Conversation · 绘画历史转换`
   - `Intent Input JSON`
5. 将绘画历史转换节点的 `conversation` 接到 Intent 节点的 `conversation`，将 `json` 接到下游文本输入。
6. 风格选择器在 `DM Canvas/Style` 分类下，名称是 `Style Selector · 风格选择器`。按 [STYLE_SELECTOR.md](STYLE_SELECTOR.md) 将 `style` 与五路 PE 文本接入，`out` 接到原 Merge 的下游。

绘画历史转换的 `text` 与 Intent Input JSON 的 `conversation`、`region`、`style` 已默认改为 STRING 输入接口，不再出现这四个文本控件，无需手动转换。`text` 和 `conversation` 必须连接上游文本输出；`region` 和 `style` 可不连接。不连接时默认空值，省略对应 JSON 字段。`warnings` 只接可选文本预览。

旧工作流中已保存的节点不一定自动更换布局。先保留旧节点里的文本和接线信息，更新插件并重启后重新添加新版节点，把原文本放入上游 Text / String 节点并接线，再切换使用新节点。不要只刷新网页或把旧节点显示的 Cached 当成新版接口已经加载。

风格选择器的文本控件仍可直接填写；如需连线，在节点菜单中将对应控件转换为输入端口。

## 找不到节点时

- 确认下载的是新版 `main`，不是最初的纯 WEP commit。
- 确认安装目录根部直接包含 `__init__.py`、`nodes.py`、`style_selector.py`、`plugins/`，没有多套一层目录。
- 确认保留了 `plugins/` 下的两个完整脚本。ComfyUI 适配层复用它们的解析函数。
- 确认插件已经安装到当前工作台，而非只进入平台下载库。
- 检查 ComfyUI 启动日志是否有该插件的 `IMPORT FAILED` 或缺失文件错误。
- 如果同时安装过旧的 Intent 插件，查看内部节点类型：新版是 `DMCanvasIntentInputJSONWithMetadata`，旧版 `DMCanvasIntentInputJSON` 不会被覆盖。

本插件只依赖 Python 标准库，不需要额外安装第三方 Python 包。风格选择器需使用支持 Lazy Evaluation 的 ComfyUI 后端。当前验证范围是 Python 加载与节点协议、转换单元测试、串联测试和 Lazy 请求逻辑；未在 ByteArtist 真实工作台执行安装或生图。

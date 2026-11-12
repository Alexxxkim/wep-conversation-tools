# ByteArtist / ComfyUI 安装说明

## Git 插件下载入口填写

| 字段 | 内容 |
| --- | --- |
| 仓库地址 | `https://github.com/Alexxxkim/wep-conversation-tools.git` |
| 下载模式 | `branch` |
| Branch | `main` |

不需要同时填写 branch 和 commit。若切换为 `commit` 模式，截图所示入口支持留空取最新提交；若要锁定版本，填写新版完整提交 ID，而不是任意旧提交。

**旧提交只包含 WEP Inline Python 脚本，不能通过 ComfyUI Custom Node 入口加载。** 新版仓库根目录有 `__init__.py`，导出 `NODE_CLASS_MAPPINGS` 和 `NODE_DISPLAY_NAME_MAPPINGS`，并由 `nodes.py` 注册两个节点。

## 下载后的操作

1. 在插件下载页面下载 / 更新仓库，等待平台显示下载成功。
2. 按平台实际提供的操作，将插件安装或应用到当前工作台。如果插件库只完成下载，还需要执行平台的后续安装操作。
3. 重启或重新加载当前 ComfyUI 后端，再刷新工作流页面。不要仅靠刷新网页加载新 Python 节点。
4. 添加节点时，在 `DM Canvas/Conversation` 分类中搜索：
   - `Drawing History to Conversation · 绘画历史转换`
   - `Intent Input JSON`
5. 将绘画历史转换节点的 `conversation` 接到 Intent 节点的 `conversation`，将 `json` 接到下游文本输入。

文本控件默认可直接填写内容；如需连线，在节点菜单中将 `text`、`conversation`、`region` 或 `style` 转换为输入端口。`warnings` 只接可选文本预览。

## 找不到节点时

- 确认下载的是新版 `main`，不是最初的纯 WEP commit。
- 确认安装目录根部直接包含 `__init__.py`、`nodes.py`、`plugins/`，没有多套一层目录。
- 确认保留了 `plugins/` 下的两个完整脚本。ComfyUI 适配层复用它们的解析函数。
- 确认插件已经安装到当前工作台，而非只进入平台下载库。
- 检查 ComfyUI 启动日志是否有该插件的 `IMPORT FAILED` 或缺失文件错误。
- 如果同时安装过旧的 Intent 插件，查看内部节点类型：新版是 `DMCanvasIntentInputJSONWithMetadata`，旧版 `DMCanvasIntentInputJSON` 不会被覆盖。

本插件只依赖 Python 标准库，不需要额外安装第三方 Python 包。当前验证范围是 Python 加载与节点协议、转换单元测试和串联测试；未在 ByteArtist 真实工作台执行安装或生图。

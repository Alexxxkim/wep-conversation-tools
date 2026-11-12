# ByteArtist / ComfyUI 安装说明

新版风格选择器默认提供 `cutout`、`3d emoji`、`retro game`、`cartoon`、`none` 五个外接端口，名称可修改，接口可增加或删除。

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
6. 风格选择器在 `DM Canvas/Style` 分类下，名称是 `Style Selector · 风格选择器`。按 [STYLE_SELECTOR.md](STYLE_SELECTOR.md) 将 `style` 与各路 PE 文本接入，`out` 接到原 Merge 的下游。

绘画历史转换的 `text` 与 Intent Input JSON 的 `conversation`、`region`、`style` 已改为通配类型 `*` 的连接接口，运行时仍只接受文本，不再声明为会生成文本控件的 STRING 输入。`text` 和 `conversation` 必须连接上游文本输出；`region` 和 `style` 可不连接。不连接时默认空值，省略对应 JSON 字段。输出保持 STRING；`warnings` 只接可选文本预览。

旧工作流中已保存的节点不一定自动更换布局。先保留旧节点里的文本和接线信息，更新插件并重启后重新添加新版节点，把原文本放入上游 Text / String 节点并接线，再切换使用新节点。不要只刷新网页或把旧节点显示的 Cached 当成新版接口已经加载。

新版风格选择器的 `style` 与各路 PE 都是外接端口；默认只声明五个具体风格，没有 `style_names` 配置框或编号占位列表。底部按钮增加风格，右键菜单修改名称或删除接口。需要安装并加载 `web/external_inputs.js` 才能使用这些界面操作。更新后旧节点已保存的自定义名称不会被覆盖，请重新添加节点以使用新的默认名称。

## 有节点但没有接口 / 出现几十个 style 输入时

2026-11-12 在一个 BA 工作台只读检查发现：`/object_info/DMCanvasStyleSelector` 已含新版 `forceInput` 定义，但 `/extensions` 没有本包的前端脚本。上一版依赖前端隐藏预铺的编号接口，脚本没加载就会全部露出；旧工作流还可能保留文本控件布局。

本版移除后端预铺的编号接口，并用通配端口避免 STRING 文本控件。检查当前工作台的 `/extensions` 是否包含 `wep-conversation-tools/external_inputs.js`；如果没有，即使 Python 节点出现，也不能使用按钮新增和改名功能。需确认平台完整安装了 `web/`，且支持通过根目录 `WEB_DIRECTORY` 加载扩展；平台未暴露该扩展时，应请平台维护方排查，不能靠填 branch / commit 解决。

只读检查并不表示 BA 已安装本版或执行通过。更新目录还需用本包的兼容入口覆盖旧版 `web/style_selector.js`，重启后端、刷新前端，并在备份工作流后重新添加节点进行验证。

## 找不到节点时

- 确认下载的是新版 `main`，不是最初的纯 WEP commit。
- 确认安装目录根部直接包含 `__init__.py`、`nodes.py`、`style_selector.py`、`plugins/`，没有多套一层目录。
- 确认保留了 `plugins/` 下的两个完整脚本。ComfyUI 适配层复用它们的解析函数。
- 确认插件已经安装到当前工作台，而非只进入平台下载库。
- 检查 ComfyUI 启动日志是否有该插件的 `IMPORT FAILED` 或缺失文件错误。
- 如果同时安装过旧的 Intent 插件，查看内部节点类型：新版是 `DMCanvasIntentInputJSONWithMetadata`，旧版 `DMCanvasIntentInputJSON` 不会被覆盖。

本插件只依赖 Python 标准库，不需要额外安装第三方 Python 包。风格选择器需使用支持 Lazy Evaluation 的 ComfyUI 后端。当前验证范围是 Python 加载与节点协议、转换单元测试、串联测试和 Lazy 请求逻辑；未在 ByteArtist 真实工作台执行安装或生图。

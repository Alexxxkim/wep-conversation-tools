# 一步步上传到 GitHub 公共仓库

三个节点放在**一个公共仓库**：`https://github.com/Alexxxkim/wep-conversation-tools`。ComfyUI 安装整个仓库，一次注册绘画历史转换、Intent Input JSON 和风格选择器；WEP 使用者仍可分别复制两个原始脚本。

## 更新已经创建的仓库

- 仓库根目录必须包含 `__init__.py`、`nodes.py`、`style_selector.py`、`plugins/`。根目录的 ComfyUI 适配层缺一不可。
- 上传新增入口、节点接口、安装说明和测试，并更新根目录 README。
- 将变更提交到 `main` 后，ByteArtist 插件下载入口选择 `branch`，填写 `main`。
- 旧的纯 WEP commit 和早期独立 WEP ZIP 不会自动变为 ComfyUI 插件；应下载最新完整仓库。

## 第 1 步：检查公开内容

只上传本说明所在的 `wep-conversation-tools` 文件夹的内容，**不要上传外层 dmcanvas 项目**。发布前确认你有权公开这些源码；公司或合作项目的代码须先获得授权。

本包没有 LICENSE 文件。请按实际权属选择许可证，不要把 Public 仓库误认为已经完成开源授权。决定许可证后，可在 GitHub 添加相应 LICENSE 文件。

## 第 2 步：创建 Public 仓库

1. 登录 <https://github.com>。
2. 打开 <https://github.com/new>。
3. Repository name 填 `wep-conversation-tools`（或你喜欢的名称）。
4. Description 可填：`ComfyUI custom nodes for drawing history conversion, intent JSON and style PE selection, with WEP scripts preserved.`
5. 选择 **Public**。README 已在包内准备好，不必再让 GitHub 初始化 README。
6. 点击 **Create repository**。

## 第 3 步：上传解压后的源码

1. 如果仓库为空，在页面上选择 **uploading an existing file**；如果已有文件，选择 **Add file → Upload files**。
2. 解压仓库 ZIP，打开里面的 `wep-conversation-tools` 文件夹。
3. 拖入**文件夹里面的内容**：`__init__.py`、`nodes.py`、`style_selector.py`、`README.md`、`STYLE_SELECTOR.md`、本说明、`BYTEARTIST_INSTALL.md`、`plugins` 文件夹、`tests` 文件夹等。不要只上传 ZIP，也不要再套一层 `wep-conversation-tools` 目录。
4. 检查预览：仓库根目录应有 `__init__.py`、`nodes.py`、`README.md`；两个原始脚本应在 `plugins/` 的对应子目录中。
5. Commit message 填：`Add ComfyUI style selector`。
6. 点击 **Commit changes**。

若浏览器没有带上隐藏文件 `.gitignore`，它不是运行必需文件；可稍后用 **Add file → Create new file**，按包内内容补充。

正确的仓库结构：

```text
wep-conversation-tools/
├── __init__.py
├── nodes.py
├── style_selector.py
├── README.md
├── STYLE_SELECTOR.md
├── BYTEARTIST_INSTALL.md
├── PUBLISH_TO_GITHUB.md
├── .gitignore
├── plugins/
│   ├── drawing-history-to-conversation/
│   │   ├── drawing_history_to_conversation.py
│   │   ├── README.md
│   │   ├── examples/
│   │   └── tests/
│   └── intent-input-json/
│       ├── intent_input_json.py
│       ├── README.md
│       ├── examples/
│       └── tests/
└── tests/
    ├── test_comfyui_nodes.py
    ├── test_pipeline.py
    └── test_style_selector.py
```

## 第 4 步：检查展示与下载

- 打开仓库首页，确认 README 正常显示，两个源码链接都能打开。
- 使用未登录窗口确认仓库是公开可见的。
- 用户可点 **Code → Download ZIP** 下载全部源码，将整个仓库目录安装到 ComfyUI `custom_nodes`；WEP 用户按 README 复制原始脚本。
- 如需发布固定版本，在仓库的 **Releases** 页面选择创建 Release，设置标签（例如首个仓库版本 `v1.0.0`），将两个独立插件 ZIP 作为附件上传后发布。这里的仓库标签不改变各脚本已有版本。
- 建议 Release 说明区分：最新完整仓库支持 ComfyUI Custom Node；早期独立 WEP ZIP 只包含 Inline Python 脚本。

## 独立 WEP 包与 ComfyUI 安装包的区别

之前的两个独立 WEP 包仍用于 Script / Inline Python，不提供 ComfyUI 根目录入口。ComfyUI / ByteArtist Custom Node 下载入口必须使用本说明所在的完整仓库或新版 ComfyUI 整包。

本说明不表示 ByteArtist 已完成安装；仓库发布与工作台安装是两个独立步骤。

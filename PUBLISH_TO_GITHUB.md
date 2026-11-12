# 一步步上传到 GitHub 公共仓库

推荐把这两个相互配合的节点放在**一个公共仓库**，例如 `wep-conversation-tools`。也可以拆成两个仓库，各自上传对应插件目录里的文件。

## 第 1 步：检查公开内容

只上传本说明所在的 `wep-conversation-tools` 文件夹的内容，**不要上传外层 dmcanvas 项目**。发布前确认你有权公开这些源码；公司或合作项目的代码须先获得授权。

本包没有 LICENSE 文件。请按实际权属选择许可证，不要把 Public 仓库误认为已经完成开源授权。决定许可证后，可在 GitHub 添加相应 LICENSE 文件。

## 第 2 步：创建 Public 仓库

1. 登录 <https://github.com>。
2. 打开 <https://github.com/new>。
3. Repository name 填 `wep-conversation-tools`（或你喜欢的名称）。
4. Description 可填：`WEP Inline Python nodes for drawing history conversion and structured intent JSON.`
5. 选择 **Public**。README 已在包内准备好，不必再让 GitHub 初始化 README。
6. 点击 **Create repository**。

## 第 3 步：上传解压后的源码

1. 如果仓库为空，在页面上选择 **uploading an existing file**；如果已有文件，选择 **Add file → Upload files**。
2. 解压仓库 ZIP，打开里面的 `wep-conversation-tools` 文件夹。
3. 拖入**文件夹里面的内容**：`README.md`、本说明、`plugins` 文件夹、`tests` 文件夹等。不要只上传 ZIP，也不要再套一层 `wep-conversation-tools` 目录。
4. 检查预览：仓库根目录应有 `README.md`；两个源码文件应在 `plugins/` 的对应子目录中。
5. Commit message 填：`Add WEP conversation tools`。
6. 点击 **Commit changes**。

若浏览器没有带上隐藏文件 `.gitignore`，它不是运行必需文件；可稍后用 **Add file → Create new file**，按包内内容补充。

正确的仓库结构：

```text
wep-conversation-tools/
├── README.md
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
    └── test_pipeline.py
```

## 第 4 步：检查展示与下载

- 打开仓库首页，确认 README 正常显示，两个源码链接都能打开。
- 使用未登录窗口确认仓库是公开可见的。
- 用户可点 **Code → Download ZIP** 下载全部源码，再按 README 在 WEP 中安装。
- 如需发布固定版本，在仓库的 **Releases** 页面选择创建 Release，设置标签（例如首个仓库版本 `v1.0.0`），将两个独立插件 ZIP 作为附件上传后发布。这里的仓库标签不改变各脚本已有版本。
- 建议 Release 说明注明：这是 WEP Inline Python 脚本，不是 ComfyUI 插件；没有 WEP 环境也能本地测试转换逻辑。

## 如果要拆成两个仓库

分别创建 `drawing-history-to-conversation-wep` 和 `intent-input-json-wep`，各自解压对应的独立插件 ZIP。把每个插件文件夹**内部的内容**上传到各自仓库根目录即可。每个包都有 README、源码、示例与独立测试。

本次只准备本地文件，没有替你创建 GitHub 仓库、推送代码或公开任何内容。

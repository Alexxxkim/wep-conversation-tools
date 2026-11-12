# Style Selector · 风格选择器

ComfyUI 注册名称：`DMCanvasStyleSelector`。分类：`DM Canvas/Style`。

将 Switch 和 Merge 合并为一个节点：根据 `style` 选一份 PE，从 `out` 输出。默认五路只是初始配置，所有名称可修改，并可新增、删除风格，最多 64 路。

## 输入与输出

| 输入 | 类型 | 作用 |
| --- | --- | --- |
| `style` | 外接文本，必需 | 上游输出的风格名称 |
| `cutout` | 外接文本，可选 | `cutout` 的 PE 文本 |
| `3d emoji`（内部 ID：`emoji`） | 外接文本，可选 | `3d emoji` 的 PE 文本 |
| `retro game`（内部 ID：`retro`） | 外接文本，可选 | `retro game` 的 PE 文本 |
| `cartoon` | 外接文本，可选 | `cartoon` 的 PE 文本 |
| `none`（内部 ID：`empty`） | 外接文本，可选 | 无风格的 PE 文本，可为空 |

输出只有 `out`（STRING），内容是选中输入的原始文本。不会拼接多份 PE，不修改换行、空白或模板占位符。

`style` 与每一路具体风格 PE 都默认显示为左侧连接端口；PE 内容放在外接 Text / String 节点。不需要 Convert widget to input。所有默认及新增输入均使用 `STRING` 与 `forceInput: true`，前端同步保持 STRING 圆点连接口并移除文本控件；输出保持 STRING，不再使用通配输入 `*`。

## 修改、增加和删除风格

1. **新增**：点击底部 **+ 新增风格接口**，输入名称（如 `水彩`），出现同名输入口，接入对应 PE 文本。
2. **重命名**：右键节点 → **修改风格名称** → 选择原名称 → 输入新名称。连线保留；上游 `style` 使用新名称。
3. **删除**：右键节点 → **删除风格接口（断开该接口连线）** → 选择名称。不删除上游文本节点。
4. 名称留空表示空风格。名称不能重复，忽略大小写和多余空白；每个选择器最多 64 路。

名称、接口和连线随工作流保存、加载和复制。内部接口 ID 固定，显示名称可以修改，重命名不破坏连线。名称配置保存在节点 properties 的 `dmcanvas_style_names` 中，通过 `EXTRA_PNGINFO.workflow` 交给后端；没有 `style_names` 文本控件，无需手写 JSON。使用 API 执行自定义风格时，需同时提供该工作流元数据。

## 风格映射

| `style` 的值 | 选中的输入 |
| --- | --- |
| `Cutout` / `cutout` | `cutout` |
| `3D Emoji` / `3d emoji` / `3demoji` | `emoji` |
| `Retro Game` / `retro game` / `retrogame` | `retro` |
| `Cartoon` / `cartoon` | `cartoon` |
| `none` / `None` / 空文本或仅空白字符 | `none`（内部 ID：`empty`） |

新节点默认按 `cutout`、`3d emoji`、`retro game`、`cartoon`、`none` 显示小写名称。内部接口 ID 保持不变，避免破坏旧工作流连线。旧节点已经保存的自定义名称不自动覆盖；需要新默认配置时，请重新添加节点，或自行修改名称。

匹配时忽略风格名称大小写、首尾空白，并规范化名称中的连续空白；也接受 `style: cartoon`、`style： Retro Game` 这样的字段文本。

直接连接上游拆分出的风格字符串即可。若上游输出完整 JSON，应先提取其中的 `style` 字段；此节点不解析完整 JSON、不做多候选随机选择。

上述是默认映射，可以改成任意名称或新增例如水彩、油画。修改名称后以新名称为准，旧名称与旧别名不再匹配。**未知风格会报错，不会偷偷回退到 `empty`。** 选中的 PE 未连接或为空时输出空字符串，不改选其他分支。`None` 等非文本不是合法的 Style / 选中 PE。

## 替换原有 Switch＋Merge

```text
上游风格字符串 ─────────────→ style
Cutout PE 文本 ────────────→ cutout
3D Emoji PE 文本 ──────────→ emoji
Retro Game PE 文本 ────────→ retro
Cartoon PE 文本 ───────────→ cartoon
无风格 PE 文本或空文本 ────→ none（内部 ID：empty）

Style Selector.out ────────→ 原 Merge.out 连接的下游文本输入
```

迁移时将原来五个 PE 文本来源分别接入新节点，将原 Merge 的下游连接改接 `out`。WEP 和 ComfyUI 的工作流格式不同，本包不会直接导入或修改完整 WEP 工作流。

## 分支执行

所有 PE 输入使用 `lazy`。`style` 先求值，名称配置从工作流 properties 读取；`check_lazy_status` 仅请求选中且尚未求值的输入，不主动请求其他分支。其他节点如果也使用那些上游，它们仍可能因为其他连接执行。选择器每次排队重新检查路由，避免只修改工作流名称配置时误用旧缓存；上游仍可正常缓存。

后端可见定义只有五个默认风格接口，不再预声明 `style_1…`。点击新增按钮后才创建新的 STRING 接口；后端动态识别其内部 ID 并按 lazy 协议请求选中分支。最多允许 64 个已配置风格。所有分支都应接 STRING 输出；默认接口即使未选中也要满足执行前的类型校验。ComfyUI 旧式动态输入协议可能不校验新增分支的连线，因此选中后仍检查 PE 必须是文本，不自动转成字符串。类型兼容但内容解析失败的未选中分支仍不会主动执行。

需使用支持 Lazy Evaluation 的 ComfyUI 后端。若 ByteArtist 未加载本包的前端扩展，只能使用五个默认接口，不能使用新增、重命名菜单；不能把本地通过测试当成 BA 已更新。

## 安装与公开范围

安装 [整个仓库](README.md)，必须保留 `web/external_inputs.js`。`web/style_selector.js` 现在仅是兼容入口，更新时必须用本包文件覆盖旧实现，避免两个扩展冲突。更新后重启后端并刷新页面，再重新添加三个节点。旧节点里的文本先保存到外部文本节点；扩展会在 properties 中备份旧文本，但不自动生成上游文本节点。

公开源码只有通用选择逻辑、接口和测试。**不包含截图中的业务 PE 文本、完整工作流、内部节点 ID、接口配置或账户信息。** 测试中的 PE 都是虚构占位文本。节点本身不上传数据、不联网、不调用模型。

## 本地验证

在仓库根目录运行：

```sh
python3 -B -m unittest discover -s tests -p 'test_style_selector.py' -v
node --experimental-vm-modules tests/test_style_selector_frontend.mjs
```

测试覆盖默认与自定义风格、超过五路、重命名、删除、配置校验、原样输出和 lazy 协议。JavaScript 测试覆盖端口增删、名称修改保留连线、重复名称、保存/加载和容量限制。协议测试不等于实际前端与调度器验收。

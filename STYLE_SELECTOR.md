# Style Selector · 风格选择器

ComfyUI 注册名称：`DMCanvasStyleSelector`。分类：`DM Canvas/Style`。

将截图中的「05a 风格选择器」Switch 和「05b 选中风格」Merge 合并为一个 ComfyUI Custom Node：根据 `style` 选取一份 PE 文本，从 `out` 输出。无需再手动连接五个 Case trigger 和 Merge branch。

## 输入与输出

| 输入 | 类型 | 作用 |
| --- | --- | --- |
| `style` | STRING，必需 | 风格名称；默认空文本 |
| `cutout` | STRING，可选 | Cutout 的 PE 文本 |
| `emoji` | STRING，可选 | 3D Emoji 的 PE 文本 |
| `retro` | STRING，可选 | Retro Game 的 PE 文本 |
| `cartoon` | STRING，可选 | Cartoon 的 PE 文本 |
| `empty` | STRING，可选 | 未选择风格时的 PE 文本，可为空 |

输出只有 `out`（STRING），内容是选中输入的原始文本。不会拼接多份 PE，不修改换行、空白或模板占位符。

所有输入默认可直接填写文本。需要连线时，在节点菜单中选择 **Convert widget to input / 转换为输入**，将对应控件转成输入端口。

## 风格映射

| `style` 的值 | 选中的输入 |
| --- | --- |
| `Cutout` / `cutout` | `cutout` |
| `3D Emoji` / `3d emoji` / `3demoji` | `emoji` |
| `Retro Game` / `retro game` / `retrogame` | `retro` |
| `Cartoon` / `cartoon` | `cartoon` |
| 空文本或仅空白字符 | `empty` |

匹配时忽略风格名称大小写、首尾空白，并规范化名称中的连续空白；也接受 `style: cartoon`、`style： Retro Game` 这样的字段文本。

直接连接上游拆分出的风格字符串即可。若上游输出完整 JSON，应先提取其中的 `style` 字段；此节点不解析完整 JSON、不做多候选随机选择。

**未知风格会报错，不会偷偷回退到 `empty`。** 截图只包含上述四种风格与空风格，本节点不额外加入 Goofy。选中的 PE 未连接或为空时输出空字符串，不改选其他分支。`None` 等非文本不是合法的 Style / 选中 PE。

## 替换原有 Switch＋Merge

```text
上游风格字符串 ─────────────→ style
Cutout PE 文本 ────────────→ cutout
3D Emoji PE 文本 ──────────→ emoji
Retro Game PE 文本 ────────→ retro
Cartoon PE 文本 ───────────→ cartoon
无风格 PE 文本或空文本 ────→ empty

Style Selector.out ────────→ 原 Merge.out 连接的下游文本输入
```

迁移时将原来五个 PE 文本来源分别接入新节点，将原 Merge 的下游连接改接 `out`。WEP 和 ComfyUI 的工作流格式不同，本包不会直接导入或修改完整 WEP 工作流。

## 分支执行

五个 PE 输入使用 ComfyUI 的 `lazy` 输入协议。`style` 先求值，`check_lazy_status` 仅请求选中且尚未求值的输入；此节点不主动请求其他四路上游。若其他节点也连接并使用了那些上游，仍可能因为其他连接而执行。

需使用支持 Lazy Evaluation 的 ComfyUI 后端；ByteArtist 的实际后端版本与前端连接行为尚未实测。

## 安装与公开范围

安装 [整个仓库](README.md)，不是只复制 `style_selector.py`。更新后重启或重新加载 ComfyUI 后端，再搜索 `Style Selector`。

公开源码只有通用选择逻辑、接口和测试。**不包含截图中的业务 PE 文本、完整工作流、内部节点 ID、接口配置或账户信息。** 测试中的 PE 都是虚构占位文本。节点本身不上传数据、不联网、不调用模型。

## 本地验证

在仓库根目录运行：

```sh
python3 -B -m unittest discover -s tests -p 'test_style_selector.py' -v
```

测试覆盖五路映射、风格别名、空风格、PE 原样输出、未知值校验、Lazy Evaluation 协议以及 Intent JSON 中的风格字段串联。Lazy 协议测试不等于在实际 ComfyUI 调度器或 ByteArtist 工作台中运行过。

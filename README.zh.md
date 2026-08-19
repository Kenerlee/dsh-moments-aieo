# dsh-moments-aieo

[English](README.md) | 中文

一套 AIEO（AI Engine Optimization，也就是 GEO/AEO —— 让品牌被 ChatGPT、DeepSeek、豆包、Kimi、Perplexity 这类 AI 搜索引用）的交付方法论，打包成 DeepSeek Harness 的一个 bundle。装上以后，agent 就带了完整的四段服务流程：**诊断 → 定位 → 内容 → 监控**，注册为一个独立命名的 skill provider。

## 插件

需要 `ctx.skills`（`inject: ['skills']`）。

插件本体刻意做得很薄：以 `includeDefaultRoots: false` 挂载 [`@deepseek-ai/dsh-skill-filesystem`](https://github.com/deepseek-ai/deepseek-harness/tree/main/packages/skill/skill-filesystem)，扫描自己的 `skills/` 目录。所以这套 skill 注册在一个独立 provider 名下，不会跟 `~/.dsh/skills`、`~/.agents/skills` 里的同名 skill 打架。扫描、watch、frontmatter 解析一行都没有重写。

### 配置

| 字段 | 默认值 | 含义 |
|---|---|---|
| `skillsDir` | 包自带的 `skills/` | 存放 `<name>/SKILL.md` 的目录。开发时指向工作树。 |
| `providerName` | `moments-aieo` | 注册到 `ctx.skills` 的 provider 名，与用户自己的 skill 根隔离。 |

## 安装

```sh
dsh plugin --profile web add dsh-moments-aieo      # 发布到 npm 之后
dsh plugin --profile web add file:/clone/的路径     # 从本地 clone 装
```

然后在 `~/.dsh/profiles/web/package.json` 的 bundle 列表里加上包名：

```json
{ "dsh": { "profile": { "bundles": [
  "@deepseek-ai/dsh-base",
  "@deepseek-ai/dsh-web-app",
  "dsh-moments-aieo"
] } } }
```

bundle 自带的 `cordis.patch.yml` 会插入那一行，所以不需要你写 profile patch。想换成自己的 skill 目录，在 `~/.dsh/profiles/web/cordis.patch.yml` 里按 id 覆盖：

```yaml
- id: moments-aieo
  config:
    skillsDir: /你的绝对路径/skills
```

不启动就验证：

```sh
dsh --profile web --dump-config | grep -A 4 'id: moments-aieo'
```

## 包含的 skills

| Skill | 用途 |
|---|---|
| `aieo-diagnosis` | 品牌 AI 可见性诊断，产出诊断报告 + 问题库初稿 |
| `aieo-positioning` | 基于 AIEO 改造版 April Dunford 方法论的定位分析，迭代问题库 |
| `aieo-query-miner` | 只认白名单平台后台导出数据挖真实搜索热词，拒绝凭空编造 |
| `aieo-monitoring` | 定期监测可见性、SoV、内容质量与业务转化 |
| `moments-aieo-dashboard` | 把监控报告渲染成交互式 HTML 面板 |
| `content-creator` | 品牌调性一致的 SEO 内容生产 |
| `humanizer-zh` | 去除中文文本里的 AI 写作痕迹 |
| `landing-page-cloner` | 落地页高保真复刻 |

四个 AIEO skill 共享同一条产物链：诊断起草的问题库，由定位修正、内容消费、监控度量。不按顺序跑不会报错，只会得到一个更弱的问题库。

## Model Experience

间接生效，通过 `@deepseek-ai/dsh-tool-skill`：本 provider 的 skill 名和截断后的描述进入模型的 skill catalog，`skill(name)` 加载选中的 `SKILL.md` 正文和资源根。路径、provider 优先级、挂载配置对模型不可见。

#### KV Cache 影响

只影响 catalog。注册一次性给 catalog 摘要加 8 行；skill 正文只有模型主动加载时才进历史。

## 已知限制与待办

- **工具名是 Claude 口径** —— skill 正文里写的是 `Read`、`Write`、`mcp__playwright__browser_*`。在 dsh 里对应的是 `bash`、`str_replace_editor`、`fs` 工具，以及 `dsh-mcp-client` 挂的 MCP。frontmatter 里的 `allowed-tools` 会被 dsh 的解析器忽略：既不报错，也不限制任何东西。
- **Web 模式禁用了 host 层 provider** —— `dsh-web-app` 把 `skill-filesystem` 设为 disabled，因为本地发现由 agent preset 拥有。本 bundle 注册在全局层，preset 里的 agent 读到的是合并后的 catalog，所以照常可见；但一个把 preset 与全局注册隔离的部署就看不到它。
- **没有构建步骤** —— 插件就是一个 `.mjs`，没有 TypeScript 源码、没有 `lib/`、没有类型声明。总共二十行；需要类型的使用者自己写。
- **参考案例不随仓库分发** —— 诊断 skill 引用的客户实例留在本地工作目录。
- **中文优先** —— 所有 AIEO skill 正文都是中文，评分标准也假定了中文 AI 搜索平台。

## License

MIT

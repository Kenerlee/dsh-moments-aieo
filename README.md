# moments-aieo

把一整套 AIEO（GEO / AEO，生成引擎优化）交付方法论，打包成 [DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness) 的一个 cordis 插件。

装上以后，agent 就带了「诊断 → 定位 → 内容 → 监控」四段服务流程的完整 skill 集。

## 包含的 skills

| Skill | 用途 |
|---|---|
| `aieo-diagnosis` | 品牌 AI 可见性诊断，产出诊断报告 + 问题库初稿 |
| `aieo-positioning` | 基于 April Dunford 方法论的 AIEO 定位分析，迭代问题库 |
| `aieo-query-miner` | 只认白名单平台后台导出数据，提取真实搜索热词并生成问题库 |
| `aieo-monitoring` | 定期监测 AI 平台可见性、SoV、内容质量与转化 |
| `moments-aieo-dashboard` | 把监控报告渲染成交互式 HTML 面板 |
| `content-creator` | 品牌调性一致的 SEO 内容生产 |
| `humanizer-zh` | 去除中文文本里的 AI 写作痕迹 |
| `landing-page-cloner` | 落地页高保真复刻 |

## 安装

```sh
git clone https://github.com/Kenerlee/moments-aieo.git
```

把插件放进 profile（bare specifier 需要能解析到 harness 的包，所以插件文件放在 profile 目录下）：

```sh
mkdir -p ~/.dsh/profiles/web/plugins/moments-aieo
cp <clone 路径>/index.mjs ~/.dsh/profiles/web/plugins/moments-aieo/
```

在 `~/.dsh/profiles/web/cordis.patch.yml` 里挂一行：

```yaml
- insert:
    - id: moments-aieo
      name: './plugins/moments-aieo/index.mjs'
      config:
        skillsDir: /绝对路径/moments-aieo/skills
```

验证：

```sh
node ~/.dsh/profiles/node_modules/@deepseek-ai/dsh/lib/bin.js --profile web --dump-config | grep -A 4 'id: moments-aieo'
```

## 配置

| 字段 | 默认值 | 含义 |
|---|---|---|
| `skillsDir` | 本仓库的 `skills/` | skill bundle 所在目录 |
| `providerName` | `moments-aieo` | 注册到 `ctx.skills` 的 provider 名，与用户自己的 skill 根隔离 |

插件本身只做一件事：以 `includeDefaultRoots: false` 复用 `@deepseek-ai/dsh-skill-filesystem`，把这套 skills 注册成一个独立命名的 provider——所以它不会跟 `~/.dsh/skills`、`~/.agents/skills` 里的同名 skill 打架。

## 已知限制

- **工具名是 Claude 口径**：skill 正文里的 `Read` / `Write` / `mcp__playwright__browser_*` 在 dsh 里不存在，对应的是 `bash` / `str_replace_editor` / `fs` 工具和 `dsh-mcp-client` 挂的 MCP。frontmatter 里的 `allowed-tools` 也会被 dsh 忽略（不报错，但不生效）。
- **Web 模式**：`dsh-web-app` 会禁用 host 层的 `skill-filesystem`，skill 由 agent preset 挂载；本插件注册在全局层，preset 读到的是合并后的 catalog，所以照常可见。
- **参考案例不随仓库分发**：诊断 skill 引用的客户材料留在本地工作目录。

## License

MIT

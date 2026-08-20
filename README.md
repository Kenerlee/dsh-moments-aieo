# dsh-moments-aieo

English | [中文](README.zh.md)

An AIEO (AI Engine Optimization — the GEO/AEO practice of getting a brand cited by ChatGPT, DeepSeek, Doubao, Kimi, Perplexity and friends) delivery method, packaged as one DeepSeek Harness bundle. Installing it gives an agent the whole four-stage service flow — **diagnosis → positioning → content → monitoring** — as a named skill provider.

## Plugin

Requires `ctx.skills` (`inject: ['skills']`).

The plugin body is deliberately thin: it mounts [`@deepseek-ai/dsh-skill-filesystem`](https://github.com/deepseek-ai/deepseek-harness/tree/main/packages/skill/skill-filesystem) with `includeDefaultRoots: false` over its own `skills/` directory, so this set registers under one provider name and never collides with same-named skills in `~/.dsh/skills` or `~/.agents/skills`. No scanner, watcher, or frontmatter parser is reimplemented here.

### Config

| Field | Default | Meaning |
|---|---|---|
| `skillsDir` | the package's own `skills/` | Directory holding the `<name>/SKILL.md` bundles. Point it at a working tree during development. |
| `providerName` | `moments-aieo` | Provider name registered on `ctx.skills`, keeping this set separable from the user's own roots. |

## Install

```sh
dsh plugin --profile web add github:Kenerlee/dsh-moments-aieo   # straight from GitHub
dsh plugin --profile web add file:/path/to/clone                # from a local clone
```

Then add the package to the profile's bundle list in `~/.dsh/profiles/web/package.json`:

```json
{ "dsh": { "profile": { "bundles": [
  "@deepseek-ai/dsh-base",
  "@deepseek-ai/dsh-web-app",
  "dsh-moments-aieo"
] } } }
```

The bundle's own `cordis.patch.yml` inserts the row, so no profile patch is required. Override it by id in `~/.dsh/profiles/web/cordis.patch.yml` when you want your own skill directory:

```yaml
- id: moments-aieo
  config:
    skillsDir: /absolute/path/to/your/skills
```

Verify without booting:

```sh
dsh --profile web --dump-config | grep -A 4 'id: moments-aieo'
```

## Browser automation

`aieo-diagnosis` and `aieo-monitoring` drive real AI search platforms through Playwright. dsh reaches MCP servers through [`dsh-mcp-client`](https://github.com/deepseek-ai/deepseek-harness/tree/main/packages/mcp/mcp-client), which registers their tools under `mcp__<serverName>__<rawName>` — the same server-qualified shape Claude Code uses, so the `mcp__playwright__browser_*` names in these skill bodies resolve as long as the server is named `playwright`:

```yaml
- insert:
    - id: mcp-playwright
      name: '@deepseek-ai/dsh-mcp-client'
      config:
        serverName: playwright
        command: npx
        args: ['@playwright/mcp@latest']
```

Without it the two skills still produce a technical audit and a report skeleton; the platform-visibility measurements are what go missing.

## Screenshots

A diagnosis report and the monitoring dashboard, both from real client runs with the brand redacted.

![Monitoring dashboard](assets/screenshot-dashboard.png)
![Diagnosis report](assets/screenshot-diagnosis-report.png)
![Dashboard on a narrow screen](assets/screenshot-dashboard-mobile.png)

## Skills

| Skill | Purpose |
|---|---|
| `moments-aieo-diagnosis` | Brand AI-visibility diagnosis; emits a report plus the first draft of the question bank |
| `moments-aieo-positioning` | Positioning analysis on an AIEO-adapted April Dunford method; iterates the question bank |
| `moments-aieo-query-miner` | Real search-term mining from whitelisted platform exports only; refuses to invent terms |
| `moments-aieo-monitoring` | Periodic visibility, share-of-voice, content-quality and conversion tracking |
| `moments-aieo-dashboard` | Renders monitoring reports into an interactive HTML dashboard |
| `content-creator` | Brand-voice-consistent SEO content production (third-party skill, MIT, by Alireza Rezvani) |
| `landing-page-cloner` | High-fidelity landing-page replication |

The five `moments-aieo-*` skills are this method; the prefix is what keeps them apart from same-named skills in a user's own roots. A Chinese AI-tell remover used to ship here and was dropped — it is a public method that belongs to nobody in particular, sourced from [Wikipedia: Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing); write it into your own skill root rather than taking a copy from here.

The four AIEO skills share one artifact chain: the question bank the diagnosis drafts is what positioning corrects, content consumes, and monitoring measures against. Running them out of order is allowed and produces a weaker bank.

## Model Experience

Indirectly, through `@deepseek-ai/dsh-tool-skill`: this provider's names and capped descriptions appear in the model's skill catalog, and `skill(name)` loads the selected `SKILL.md` body plus its resource base. Paths, provider ranks, and the mount configuration stay hidden from the model.

#### KV Cache effect

Catalog only. Registration adds eight rows to the catalog digest once; skill bodies enter history only when the model loads one.

## Known Limitations and Deferred Work

- **The frontmatter `allowed-tools` key does nothing under dsh** — the parser reads `name`, `description`, `whenToUse`, `metadata` and the two invocation flags, and ignores the rest. It neither errors nor restricts anything; the key is kept for Claude Code compatibility. Harness tool names in the bodies were corrected to dsh spellings (`read`, `glob`, `web_fetch`); MCP names need the server configured above.
- **Web mode disables the host-level provider** — `dsh-web-app` sets `skill-filesystem: disabled` because agent presets own local discovery. This bundle registers globally and preset agents read the merged catalog, so the set stays visible; a deployment that isolates its presets from global registrations would not see it.
- **No build step** — the plugin ships as plain `.mjs` with no TypeScript source, no `lib/`, and no type declarations. It is twenty lines; a consumer wanting types writes them.
- **Reference cases are not distributed** — the diagnosis skill's worked client examples live outside this repository.
- **Chinese-first content** — every AIEO skill body is written in Chinese, and the scoring rubrics assume Chinese-language AI search platforms.

## Who built this

The method comes from real AIEO delivery work — brand diagnosis, positioning, question-bank construction and monitoring for consumer, healthcare, SaaS and franchise clients. The tooling is open source; the industry baselines and the judgement of what to do with a low score are not things a Markdown file can carry. [moments.top](https://moments.top)

**Ran a diagnosis?** Open a [Discussion](https://github.com/Kenerlee/dsh-moments-aieo/discussions) with your score and industry (no brand name needed). Real numbers across industries are what turn a scoring rubric into a benchmark, and the aggregate goes back into this repo.

## License

MIT

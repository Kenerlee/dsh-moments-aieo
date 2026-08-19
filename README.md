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
dsh plugin --profile web add dsh-moments-aieo      # once published to npm
dsh plugin --profile web add file:/path/to/clone   # from a local clone
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

## Skills

| Skill | Purpose |
|---|---|
| `aieo-diagnosis` | Brand AI-visibility diagnosis; emits a report plus the first draft of the question bank |
| `aieo-positioning` | Positioning analysis on an AIEO-adapted April Dunford method; iterates the question bank |
| `aieo-query-miner` | Real search-term mining from whitelisted platform exports only; refuses to invent terms |
| `aieo-monitoring` | Periodic visibility, share-of-voice, content-quality and conversion tracking |
| `moments-aieo-dashboard` | Renders monitoring reports into an interactive HTML dashboard |
| `content-creator` | Brand-voice-consistent SEO content production |
| `humanizer-zh` | Strips AI writing tells from Chinese text |
| `landing-page-cloner` | High-fidelity landing-page replication |

The four AIEO skills share one artifact chain: the question bank the diagnosis drafts is what positioning corrects, content consumes, and monitoring measures against. Running them out of order is allowed and produces a weaker bank.

## Model Experience

Indirectly, through `@deepseek-ai/dsh-tool-skill`: this provider's names and capped descriptions appear in the model's skill catalog, and `skill(name)` loads the selected `SKILL.md` body plus its resource base. Paths, provider ranks, and the mount configuration stay hidden from the model.

#### KV Cache effect

Catalog only. Registration adds eight rows to the catalog digest once; skill bodies enter history only when the model loads one.

## Known Limitations and Deferred Work

- **Tool names are written in Claude dialect** — the skill bodies name `Read`, `Write`, and `mcp__playwright__browser_*`. Under dsh those are `bash`, `str_replace_editor`, the `fs` tools, and whatever `dsh-mcp-client` mounts. The frontmatter `allowed-tools` key is ignored by dsh's parser: it neither errors nor restricts anything.
- **Web mode disables the host-level provider** — `dsh-web-app` sets `skill-filesystem: disabled` because agent presets own local discovery. This bundle registers globally and preset agents read the merged catalog, so the set stays visible; a deployment that isolates its presets from global registrations would not see it.
- **No build step** — the plugin ships as plain `.mjs` with no TypeScript source, no `lib/`, and no type declarations. It is twenty lines; a consumer wanting types writes them.
- **Reference cases are not distributed** — the diagnosis skill's worked client examples live outside this repository.
- **Chinese-first content** — every AIEO skill body is written in Chinese, and the scoring rubrics assume Chinese-language AI search platforms.

## License

MIT

---
name: moments-aieo-dashboard
description: "Generate an interactive AIEO monitoring dashboard for any brand from existing monitoring reports. Triggers when users mention 'dashboard', 'AIEO dashboard', '监控面板', '可视化报告', 'monitoring dashboard', '生成面板', '生成dashboard', or want to visualize AIEO monitoring trends. Requires existing monitoring reports (format: {Brand}_AIEO监控报告_{date}.md) in the 04_monitoring/ directory."
---

# AIEO Monitoring Dashboard Generator (v2)

Generate an interactive HTML dashboard from AIEO monitoring reports for any brand. The dashboard visualizes 4 core monitoring capabilities:

1. **问题库监控** — Question bank heatmap by type (品牌词/品类词/对比词/场景词/长尾), trend charts, risk alerts
2. **SoV / 引用监控** — Share of Voice trends, platform coverage bars, interception analysis
3. **内容效果归因** — Content type effectiveness ranking, positioning consistency radar, event timeline
4. **竞品变化追踪** — Competitor mention trends, threat assessment table, radar comparison

**Parser schema: v2** — handles both legacy reports (single combined platform table) and new per-platform sub-table format (e.g. `### 2.1 豆包测试结果 — N题`).

## Workflow

### Step 1: Confirm Brand and Report Location

Ask the user to confirm:

1. **Brand name** — Must exactly match the prefix in monitoring report filenames (e.g. `Moments`, `摸摸底`, `SIITD`, `IKOO_Glass`)
2. **Report directory** — Default: `04_monitoring/` in the current project root

Scan for available brands:

```bash
ls 04_monitoring/*_AIEO监控报告_*.md 2>/dev/null | sed 's|.*/||' | sed 's/_AIEO监控报告_.*//' | sort -u
```

### Step 2: Validate Reports Exist

Run the parser:

```bash
python3 scripts/parse_monitoring_reports.py "<brand>" "<dir>" --output /tmp/aieo_dashboard_data.json
```

- **0 reports**: list available brands and ask user to correct.
- **Reports found**: parser prints `Schema version: 2` and a count to stderr. Each report gets a `[N warnings]` annotation when extraction is partial. Proceed to Step 3.

### Step 3: Verify Parser Output Quality (NEW — v2)

Before generating the HTML, sanity-check the JSON. The parser is non-trivial; format drift causes silent data loss.

```bash
python3 -c "
import json
d = json.load(open('/tmp/aieo_dashboard_data.json'))
print('platforms:', d['metadata']['platforms'])
print('latest_metrics:', list(d['latest_metrics'].keys()))
print('platform_perf:', [(p['name'], p['mention_rate']) for p in d['latest_platform_performance']])
print('competitors:', len(d['latest_competitors']))
print('interceptions:', len(d['interceptions']))
print('warnings:', list(d.get('warnings', {}).keys()))
"
```

**Expected**:
- `platforms` ⊆ known list: 豆包/元宝/Kimi/DeepSeek/ChatGPT/Perplexity/文心一言/Claude
- `latest_metrics` includes ai_mention_rate, ai_first_recommend_rate, positioning_consistency_rate, sentiment_positive_rate
- `latest_platform_performance` has at least one entry
- `competitors` count ≥ 3 (otherwise dedicated competitor table is missing; consider passing curated names — see "Manual enrichment" below)

If any expected field is empty, follow **Manual Enrichment** below before generating the HTML.

### Step 4: Generate Dashboard HTML

1. Read template: `assets/dashboard_template.html`
2. Read JSON: `/tmp/aieo_dashboard_data.json`
3. Replace `{{BRAND_NAME}}` and `{{DASHBOARD_DATA}}`
4. Write to: `<report_dir>/dashboard_<brand>.html`
5. Open: `open <report_dir>/dashboard_<brand>.html`

Inline Python one-liner:
```python
from pathlib import Path
tpl = Path('assets/dashboard_template.html').read_text(encoding='utf-8')
data = Path('/tmp/aieo_dashboard_data.json').read_text(encoding='utf-8')
out = tpl.replace('{{BRAND_NAME}}', '<brand>').replace('{{DASHBOARD_DATA}}', data)
Path('<report_dir>/dashboard_<brand>.html').write_text(out, encoding='utf-8')
```

### Step 5: Validate Rendering & Iterate

Open in browser and check:
- **Header date badge** shows latest report date (auto-populated from `metadata.latest_date`)
- **Footer** shows dashboard generation time + parser schema version
- **Tab 2 (SoV)**: platform bars show real platform names, not `undefined`
- **Tab 4 (Competitors)**: trend chart + radar + table all populated, not "暂无竞品数据"

If something is broken, common causes:

| Symptom | Root cause | Fix |
|---------|-----------|-----|
| `undefined` in platform bar names | parser produced `platform`/`first_rec_rate` instead of `name`/`first_recommend_rate` | parser v2 emits correct names |
| "暂无竞品数据" | dedicated competitor table absent + auto-detect found 0 orgs | manual enrichment (see below) |
| Empty competitor trend chart | `competitor_timeseries` keys point to flat arrays not `{dates, rates}` | parser v2 emits correct structure |
| Health score = "--" | `latest_metrics.aieo_health_score` is null AND no other metrics for fallback computation | parser v2 falls back to `0.35*m + 0.25*f + 0.20*p + 0.20*s` |
| Latest date badge empty | `metadata.latest_date` missing | parser v2 always populates from filename |

## Manual Enrichment (when parser output is sparse)

For brands where reports don't follow the canonical format, manually inject richer data **before** generating the HTML. Edit `/tmp/aieo_dashboard_data.json` and overwrite specific keys.

### JSON Schema Reference

```python
{
  "schema_version": 2,
  "metadata": {
    "brand": "SIITD",
    "report_count": 14,
    "date_range": "2026-03-01 ~ 2026-05-17",
    "latest_date": "2026-05-17",     # auto from latest filename
    "first_date": "2026-03-01",
    "platforms": ["豆包", "元宝", "Kimi"],   # must be real AI platform names
    "question_count": 10
  },
  "timeseries": {
    "dates": ["2026-03-01", ...],
    "ai_mention_rate":           [65, 65, ..., 50],   # %
    "ai_first_recommend_rate":   [25, ..., 25],       # %
    "positioning_consistency_rate": [...],            # % (extracted from numeric OR text e.g. "极高"=90)
    "sentiment_positive_rate":   [...],
    "aieo_health_score":         [...]                # auto-computed if missing
  },
  "latest_metrics": {  # subset of timeseries keys, latest values only
    "ai_mention_rate": 50.0, "ai_first_recommend_rate": 25.0,
    "positioning_consistency_rate": 90.0, "sentiment_positive_rate": 100.0,
    "aieo_health_score": 60.8, "platform_coverage": "2/3",
    "overall_assessment": "..."
  },
  "first_metrics": { /* same shape as latest_metrics for delta computation */ },
  "latest_platform_performance": [
    {"name": "豆包", "mention_rate": 40.0, "first_recommend_rate": 10.0, "tested": 10}
  ],
  "latest_platform_results": {
    "platforms": ["豆包", "元宝"],
    "questions": [
      {"text": "Q01", "type": "brand", "q": "上海产业转型...",
       "results": {"豆包": "first_recommend", "元宝": "first_recommend"}}
    ]
  },
  "question_type_stats": {
    "brand":      {"total": 16, "mentioned": 12, "first_rec": 6},
    "category":   {"total": 8,  "mentioned": 1,  "first_rec": 1},
    "comparison": {"total": 10, "mentioned": 10, "first_rec": 10},
    "scenario":   {"total": 11, "mentioned": 2,  "first_rec": 1},
    "longtail":   {"total": 7,  "mentioned": 5,  "first_rec": 4}
  },
  "question_type_timeseries": {
    "dates": [...],
    "brand": [70, 75, ...], "category": [...], "comparison": [...], "scenario": [...], "longtail": [...]
  },
  "latest_competitors": [
    {"name": "上海规划院", "mention_rate": 90, "change": "↑", "note": "..."}
    # mention_rate is required for radar/table. mention_count is allowed as fallback.
  ],
  "competitor_timeseries": {
    "上海规划院": {"dates": ["2026-03-01", ...], "rates": [30, ..., 90]}
    # CRITICAL: must be {dates, rates} object, NOT flat array
  },
  "interceptions": [
    {"question": "BR-14 SLOGAN", "platform": "豆包+元宝", "type": "brand"}
  ],
  "latest_recommendations": {
    "highlights": ["⭐ ..."], "issues": ["🔴 ..."], "actions": ["P0 ..."]
  }
}
```

### Result classification values

`results` field values (per platform per question):
- `"first_recommend"` — SIITD is #1 or 🌟
- `"mentioned"` — SIITD appears in response (✅, 提及, 识别)
- `"compared"` — Comparison response (CP questions)
- `"not_mentioned"` — SIITD absent (❌, 未提及, —)

## Report Format Conventions Parser Handles

### New format (v2-recommended) — per-platform sub-tables

```markdown
## 二、AI可见性详情

### 2.1 豆包（Doubao）测试结果 — 10题

| 编号 | 类型 | 问题 | 结果 | 情感 | 定位词数 | 关键发现 |
|------|------|------|------|------|---------|---------|
| Q01 | BR | 上海产业... | 🌟首推（...） | 极正面 | **10** | ... |
| BR-13 | METHOD | SIITD的... | ❌未提及 | — | — | ... |

### 2.2 元宝测试结果 — 10题
| ... |
```

### Legacy format — single combined table

```markdown
## 二、AI可见性详情

### 2.1 各平台测试结果

| 问题 | 豆包 | Kimi | 文心 | DeepSeek |
|------|------|------|------|----------|
| Q1: ... | ✅首推 | ✅提及 | ❌ | ✅首推 |
```

Both formats produce the same internal `latest_platform_results` structure.

## File Structure

```
moments-aieo-dashboard/
├── SKILL.md                              # This file (v2)
├── scripts/
│   └── parse_monitoring_reports.py       # v2 parser → JSON
└── assets/
    └── dashboard_template.html           # v2 template with date badge + footer
```

## Output

- Single self-contained HTML file with inline CSS/JS + Chart.js CDN
- Interactive charts (line, radar, doughnut, heatmap) with tooltips
- 4-tab layout covering all monitoring capabilities
- Dark theme, responsive layout, auto-populated date badge + footer
- Saved to: `{report_dir}/dashboard_{brand}.html`

## Changelog

**v2 (2026-05-18)**:
- Parser: known-platform list (eliminates "table header as platform" bug)
- Parser: per-platform sub-table aggregation builds platform_performance
- Parser: textual positioning_consistency_rate ("极高" → 90)
- Parser: result classification respects negation ("未提及" no longer matches "提及")
- Parser: question type uses code prefix (BR-/CR-/SC-) before keyword fallback
- Parser: competitor auto-detection with denylist + brand-self filter
- Parser: emits `schema_version: 2` and per-report warnings
- Template: header date badge + generation timestamp footer + JSON schema doc comment
- SKILL.md: new Step 3 (verify quality) + Manual Enrichment with full schema reference + troubleshooting table

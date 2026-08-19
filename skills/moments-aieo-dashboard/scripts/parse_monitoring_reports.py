#!/usr/bin/env python3
"""
AIEO Monitoring Report Parser (v2)
Scans a directory for AIEO monitoring reports matching a brand name,
extracts structured data, and outputs JSON for dashboard generation.

Usage:
    python parse_monitoring_reports.py <brand_name> <report_directory> [--output <output.json>]

v2 changes (vs v1):
    - Known-platform list eliminates "table header as platform" bug
    - Multi-format core_metrics extraction (supports legacy "AI提及率 | X%" and new comparison-table format "AI提及率 | **X%** (Y/Z) | ...")
    - Per-platform sub-table aggregation builds platform_performance even without "平台表现分析" section
    - Competitor extraction combines dedicated table + recommendation narrative
    - Cleaner bold-stripped recommendation extraction
    - Emits SCHEMA_VERSION + warnings array so caller can detect format issues
"""

import os
import re
import json
import sys
import glob

SCHEMA_VERSION = 2

# Known AI platform names — used to anchor per-platform sub-table parsing
KNOWN_PLATFORMS = [
    '豆包', '元宝', 'Kimi', 'DeepSeek', 'ChatGPT', 'Perplexity',
    '文心一言', '文心', 'Claude', 'Gemini', '通义千问', '通义', '智谱', '讯飞星火', '星火',
]

# Mentioned-keyword positive markers; only checked AFTER 未提及/未识别 negation
_POS_TOKENS = ['✅', '正确识别', '完整阐释', '提及', '识别']


def find_reports(brand_name, report_dir):
    """Find all monitoring reports for a given brand in the directory."""
    pattern = os.path.join(report_dir, f"{brand_name}_AIEO监控报告_*.md")
    files = sorted(glob.glob(pattern))
    summary_pattern = os.path.join(report_dir, f"{brand_name}_监控摘要_*.md")
    summaries = sorted(glob.glob(summary_pattern))
    return files, summaries


def extract_date(filename):
    """Extract date from filename like Brand_AIEO监控报告_2026-03-01.md"""
    match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
    return match.group(1) if match else None


def strip_md(s):
    """Strip markdown bold/italic/emoji emphasis from a string."""
    s = re.sub(r'\*\*([^*]+)\*\*', r'\1', s)
    s = re.sub(r'\*([^*]+)\*', r'\1', s)
    return s.strip()


def classify_result_text(cell):
    """Classify a result cell. Priority order matters; negation checked before positive markers
    to avoid 未提及 being mis-classified as 提及."""
    if not cell or cell in ('—', '--', '-'):
        return 'not_mentioned'
    # 1. First-recommend wins: 🌟 (star) or explicit "首推" / "首位"
    if '🌟' in cell or '首推' in cell or '首位' in cell:
        return 'first_recommend'
    # 2. Compared
    if '对比' in cell and ('完整' in cell or 'UNLIKE' in cell or 'vs' in cell.lower()):
        return 'compared'
    # 3. Negation (check BEFORE positive markers to handle "❌未提及")
    if '❌' in cell or '未提及' in cell or '未识别' in cell or '消失' in cell or '🔴' in cell:
        return 'not_mentioned'
    # 4. Mentioned positive markers
    if any(tok in cell for tok in _POS_TOKENS):
        return 'mentioned'
    return cell  # unknown — keep raw


def classify_question(q_text):
    """Classify a question into brand/category/comparison/scenario/longtail.
    Code prefix (BR-/CR-/CP-/SC-/LT-/Q-) takes ABSOLUTE priority over keyword heuristics."""
    # Step 1: code prefix wins, no exceptions
    if re.search(r'\bBR[-\s]?\d', q_text): return 'brand'
    if re.search(r'\bCP[-\s]?\d', q_text): return 'comparison'
    if re.search(r'\bCR[-\s]?\d', q_text): return 'category'
    if re.search(r'\bSC[-\s]?\d', q_text): return 'scenario'
    if re.search(r'\bLT[-\s]?\d', q_text): return 'longtail'
    if re.search(r'\bQ\d+\b', q_text): return 'scenario'  # legacy Q1-Q13 are SC-type
    # Step 2: keyword fallback (only for un-coded questions)
    if re.search(r'品牌|怎么样|是什么|介绍|官网|院长|招聘|联系', q_text): return 'brand'
    if re.search(r'对比|vs|哪个好|比较|区别', q_text): return 'comparison'
    if re.search(r'推荐|哪家|有哪些|哪个机构|哪家机构|排名', q_text): return 'category'
    if re.search(r'场景|找谁|做方案|想做', q_text): return 'scenario'
    return 'longtail'


def parse_core_metrics(content, warnings):
    """Extract core metrics. Supports both legacy and new comparison-table formats."""
    metrics = {}

    # Strategy 1: capture FIRST percentage after metric name in any table row
    # Handles: "AI提及率 | 52.9% | ..." and "AI提及率 | **40%** (4/10) | ..."
    metric_names = {
        'ai_mention_rate': 'AI提及率',
        'ai_first_recommend_rate': 'AI首推率',
        'positioning_consistency_rate': '定位一致率',
        'sentiment_positive_rate': '情感正面率',
        'content_accuracy_rate': '内容准确率',
    }
    # Textual qualitative → numeric mapping (for cells like "极高" / "高" / "中" / "低")
    text_score = {'极高': 90, '高': 75, '中高': 70, '中': 60, '中低': 45, '低': 30, '极低': 15}
    for key, cn_name in metric_names.items():
        row_match = re.search(
            r'\|\s*' + re.escape(cn_name) + r'[^|]*\|([^\n]+)',
            content
        )
        if row_match:
            row = row_match.group(1)
            num_match = re.search(r'\*{0,2}\s*([\d.]+)\s*%', row)
            if num_match:
                metrics[key] = float(num_match.group(1))
            else:
                # Try qualitative cell
                for word, score in text_score.items():
                    if word in row:
                        metrics[key] = float(score)
                        break

    # Platform coverage
    pc_match = re.search(r'\|\s*平台覆盖率\s*\|([^\n]+)', content)
    if pc_match:
        cov_match = re.search(r'(\d+\s*/\s*\d+|[\d.]+%)', pc_match.group(1))
        if cov_match:
            metrics['platform_coverage'] = cov_match.group(1).strip()

    # AIEO health score
    health_match = re.search(r'AIEO\s*健康度\D*([\d.]+)\s*(?:分|/100)?', content)
    if health_match:
        try:
            metrics['aieo_health_score'] = float(health_match.group(1))
        except ValueError:
            pass

    # Overall assessment (first line after "整体评价:" / "整体评价**:")
    assess_match = re.search(r'\*?\*?整体评价\*?\*?\s*[：:]\s*(.+?)(?:\n\n|\n---|\n##)', content, re.DOTALL)
    if assess_match:
        metrics['overall_assessment'] = strip_md(assess_match.group(1).strip().replace('\n', ' '))[:500]

    if not any(k in metrics for k in metric_names):
        warnings.append('No core metrics extracted — report may use unrecognized format')

    return metrics


def parse_per_platform_tables(content, warnings):
    """Find sub-section headers like '### 2.1 豆包测试结果 — N题' and parse the following table.
    Returns: dict {platform_name: [{text, type, raw_cells}, ...]}
    """
    result = {}
    # Look for any heading containing a known platform name
    for platform in KNOWN_PLATFORMS:
        # Match headings like "### 2.1 豆包（Doubao）测试结果 — 10题" or "### 2.2 元宝测试结果"
        heading_pat = re.compile(
            r'#{2,4}[^\n]*' + re.escape(platform) + r'[^\n]*?(?:测试结果|测试|结果)[^\n]*'
        )
        m = heading_pat.search(content)
        if not m:
            continue
        # Find the next markdown table after this heading
        after = content[m.end():]
        # Stop at next ### heading
        next_heading = re.search(r'\n#{2,4}\s', after)
        section_end = next_heading.start() if next_heading else len(after)
        section = after[:section_end]
        table_match = re.search(
            r'(\|[^\n]+\|)\n(\|[-\s|:]+\|)\n((?:\|[^\n]+\|\n?)+)',
            section
        )
        if not table_match:
            continue
        header_cells = [strip_md(c) for c in table_match.group(1).split('|') if c.strip()]
        rows_raw = table_match.group(3).strip().split('\n')

        questions = []
        # Determine column indices
        col_map = {h: i for i, h in enumerate(header_cells)}
        # Common columns: 编号, 类型, 问题, 结果, 情感, 定位词数, 关键发现
        idx_id     = col_map.get('编号', 0)
        idx_q      = col_map.get('问题', 2 if '问题' not in col_map else col_map['问题'])
        idx_result = col_map.get('结果', 3)

        for row in rows_raw:
            cells = [strip_md(c) for c in row.split('|') if c.strip()]
            if len(cells) < 3:
                continue
            qcode = cells[idx_id] if idx_id < len(cells) else ''
            qtext = cells[idx_q] if idx_q < len(cells) else qcode
            result_cell = cells[idx_result] if idx_result < len(cells) else ''
            qtype = classify_question(qcode + ' ' + qtext)
            label = classify_result_text(result_cell)
            questions.append({
                'code': qcode,
                'text': qcode if qcode else qtext[:30],
                'q': qtext,
                'type': qtype,
                'result': label,
            })
        if questions:
            result[platform] = questions

    if not result:
        warnings.append('No per-platform sub-tables found — falling back to combined table parsing')
    return result


def parse_combined_platform_table(content):
    """Legacy: a single table with multiple platform columns. Used as fallback."""
    table_match = re.search(
        r'(?:各平台测试结果)\s*\n+(\|[^\n]+\|)\n(\|[-\s|:]+\|)\n((?:\|[^\n]+\|\n?)+)',
        content, re.DOTALL
    )
    if not table_match:
        return {'platforms': [], 'questions': []}
    header_cells = [strip_md(c) for c in table_match.group(1).split('|') if c.strip()]
    # First column = question; rest = platforms (filtered against known list when possible)
    platforms_raw = header_cells[1:]
    platforms = [p for p in platforms_raw if any(kp in p for kp in KNOWN_PLATFORMS)] or platforms_raw
    questions = []
    for row in table_match.group(3).strip().split('\n'):
        cells = [strip_md(c) for c in row.split('|') if c.strip()]
        if len(cells) < 2:
            continue
        q_text = cells[0]
        results = {}
        for i, p in enumerate(platforms_raw):
            if i + 1 < len(cells) and p in platforms:
                results[p] = classify_result_text(cells[i + 1])
        questions.append({'text': q_text, 'type': classify_question(q_text), 'results': results})
    return {'platforms': platforms, 'questions': questions}


def build_platform_performance(per_platform):
    """Aggregate per-platform questions into [{name, mention_rate, first_recommend_rate, tested}]."""
    out = []
    for platform, questions in per_platform.items():
        tested = len(questions)
        mentioned = sum(1 for q in questions if q['result'] in ('first_recommend', 'mentioned', 'compared'))
        first_rec = sum(1 for q in questions if q['result'] == 'first_recommend')
        out.append({
            'name': platform,
            'tested': tested,
            'mention_rate': round(mentioned / tested * 100, 1) if tested else 0,
            'first_recommend_rate': round(first_rec / tested * 100, 1) if tested else 0,
        })
    # Sort by mention rate desc
    out.sort(key=lambda x: x['mention_rate'], reverse=True)
    return out


def build_combined_platform_results(per_platform):
    """Convert per-platform dict into the {platforms, questions} structure the template expects.
    Questions are keyed by code (e.g. Q01, BR-13) across platforms."""
    platforms = list(per_platform.keys())
    by_code = {}
    for platform, questions in per_platform.items():
        for q in questions:
            code = q['code'] or q['text']
            if code not in by_code:
                by_code[code] = {
                    'text': code, 'q': q['q'], 'type': q['type'], 'results': {}
                }
            by_code[code]['results'][platform] = q['result']
    return {'platforms': platforms, 'questions': list(by_code.values())}


def parse_competitor_data(content, warnings, brand_aliases=None):
    """Extract competitors from dedicated table OR by auto-detecting org-name patterns in narrative.
    brand_aliases: list of brand-self phrases to exclude (e.g. ['SIITD', '上海产业转型发展研究院'])."""
    brand_aliases = brand_aliases or []
    competitors = []
    # Strategy 1: dedicated table
    comp_match = re.search(
        r'竞品(?:提及率|动态)[^\n]*\n+(\|[^\n]+\|)\n(\|[-\s|:]+\|)\n((?:\|[^\n]+\|\n?)+)',
        content, re.DOTALL
    )
    if comp_match:
        for row in comp_match.group(3).strip().split('\n'):
            cells = [strip_md(c) for c in row.split('|') if c.strip()]
            if len(cells) >= 2:
                entry = {'name': cells[0]}
                num = re.search(r'([\d.]+)%', cells[1])
                if num:
                    entry['mention_rate'] = float(num.group(1))
                if len(cells) >= 3:
                    entry['change'] = cells[2]
                if len(cells) >= 4:
                    entry['note'] = cells[3]
                competitors.append(entry)
        return competitors

    # Strategy 2: auto-detect Chinese org names in "关键发现" cells + recommendation narrative.
    # Org-name regex: requires named identifier (geographic/proper noun) + org-type suffix.
    # Generic phrases like "实战派头部智库" / "官方背景智库" will NOT match because they lack a place/proper-noun prefix.
    candidates = {}
    # Pattern: place/proper noun (1-8 chars) directly + named identifier (1-6 chars) + org-type suffix (2-4 chars)
    # Org-type suffix must be a strict noun: 研究院/设计院/规划院/科学院/工程院/智库/集团/事务所/有限公司
    pattern = r'(?<![一-龥A-Za-z])([一-龥]{2,3}(?:[一-龥A-Za-z]{0,8})?(?:研究院|设计院|规划院|科学院|工程院|发展研究院|城建院|建筑院))|((?:上海|北京|深圳|杭州|广州|南京|苏州|武汉|长沙|国家|中国|中关村|清华|同济|复旦|交大|华东|华南|华北|西北|西南|东南|长三角|大湾区)[一-龥]{0,6}(?:智库|集团|研究中心|事务所|有限公司))|((?:麦肯锡|贝恩|BCG|波士顿咨询|普华永道|德勤|安永|毕马威|戴德梁行|仲量联行|罗兰贝格|赛迪|前瞻|中咨|中机院|中商|中投|福睿|东滩|上咨|临港|华建|创邑|蕾奥|深规院|清华同衡|济邦|远博志城|思董|和君|建发|天安|合一))'
    for match in re.finditer(pattern, content):
        org = (match.group(1) or match.group(2) or match.group(3) or '').strip()
        if not org or len(org) < 2 or len(org) > 20:
            continue
        # Drop brand-self
        if any(alias and alias in org for alias in brand_aliases if alias):
            continue
        candidates[org] = candidates.get(org, 0) + 1

    # Denylist: generic nouns and parser fragments
    DENYLIST = {
        '规划设计院', '设计院', '研究院', '咨询公司', '咨询机构', '智库',
        '产业规划', '城市更新', '推规划', '甲级规划院',
    }
    DENYLIST_PREFIXES = ('双平台', '推', '找', '该', '此', '那', '这', '说明', '类似', '其他')

    filtered = []
    for name, cnt in candidates.items():
        if cnt < 2:
            continue
        if name in DENYLIST:
            continue
        if any(name.startswith(p) for p in DENYLIST_PREFIXES):
            continue
        filtered.append((name, cnt))
    filtered.sort(key=lambda x: -x[1])
    top = filtered[:15]
    # Normalize mention_count → mention_rate (0-100 proxy, top competitor = 90)
    if top:
        max_cnt = top[0][1]
        for name, cnt in top:
            rate = round(cnt / max_cnt * 90, 1) if max_cnt > 0 else 0
            competitors.append({
                'name': name,
                'mention_count': cnt,
                'mention_rate': rate,
                'change': '→',  # neutral default; can be enriched manually
            })

    if not competitors:
        warnings.append('No competitor data extracted')
    return competitors


def parse_recommendations(content, warnings):
    """Extract highlights, issues, and recommendations from §5 / §五 sections."""
    result = {'highlights': [], 'issues': [], 'actions': []}

    def extract_items(section_text):
        """Pull bullet/numbered items, stripping bold markers, dropping fragmentary code-suffix lines."""
        items = []
        for line in section_text.split('\n'):
            line = line.strip()
            if not line:
                continue
            # Match bullets and numbered list items
            m = re.match(r'^(?:[-*•✅⭐⚠️🔴🟠🟡🟢🌟]+\s+|\d+\.\s+)(.+)', line)
            if not m:
                continue
            item = strip_md(m.group(1)).strip()
            # Drop fragments that start with a digit (likely "24 持续..." cut from "**CR-24** 持续...")
            if re.match(r'^\d+\s+', item):
                continue
            if len(item) < 5:
                continue
            items.append(item)
        return items

    # Highlights — anchor to "### 5.1 本期亮点" style; stop at "### 5.2" or any next heading/hr
    h = re.search(r'###[^\n]*本期亮点[^\n]*\n(.*?)(?=\n###|\n---|\n## )', content, re.DOTALL)
    if h:
        result['highlights'] = extract_items(h.group(1))[:8]

    # Issues — same anchoring strategy
    i = re.search(r'###[^\n]*(?:需关注问题|需关注|问题与挑战)[^\n]*\n(.*?)(?=\n###|\n---|\n## )', content, re.DOTALL)
    if i:
        result['issues'] = extract_items(i.group(1))[:8]

    # Actions / next-period optimizations
    a = re.search(r'###[^\n]*(?:下期优化重点|下期优化|优化重点|推进建议|行动建议)[^\n]*\n(.*?)(?=\n---|\n## )', content, re.DOTALL)
    if a:
        result['actions'] = extract_items(a.group(1))[:10]

    return result


def parse_single_report(filepath, brand_aliases=None):
    """Parse a single monitoring report."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    warnings = []
    date = extract_date(filepath)
    per_platform = parse_per_platform_tables(content, warnings)

    if per_platform:
        platform_results = build_combined_platform_results(per_platform)
        platform_perf = build_platform_performance(per_platform)
    else:
        platform_results = parse_combined_platform_table(content)
        platform_perf = []  # legacy reports may have it under "平台表现分析"

    return {
        'date': date,
        'filename': os.path.basename(filepath),
        'core_metrics': parse_core_metrics(content, warnings),
        'platform_results': platform_results,
        'platform_performance': platform_perf,
        'competitors': parse_competitor_data(content, warnings, brand_aliases=brand_aliases),
        'recommendations': parse_recommendations(content, warnings),
        'warnings': warnings,
    }


def aggregate_data(reports):
    """Aggregate all parsed reports into dashboard-ready data."""
    reports.sort(key=lambda r: r['date'] or '')

    dates = [r['date'] for r in reports]
    mention_rates = [r['core_metrics'].get('ai_mention_rate') for r in reports]
    first_rec_rates = [r['core_metrics'].get('ai_first_recommend_rate') for r in reports]
    positioning_rates = [r['core_metrics'].get('positioning_consistency_rate') for r in reports]
    sentiment_rates = [r['core_metrics'].get('sentiment_positive_rate') for r in reports]
    health_scores = [r['core_metrics'].get('aieo_health_score') for r in reports]

    # Compute health score where missing: 0.35*mention + 0.25*first + 0.20*pos + 0.20*sent
    def _compute_health(m, f, p, s):
        if None in (m, f, p, s):
            return None
        return round(0.35*m + 0.25*f + 0.20*p + 0.20*s, 1)

    for i, h in enumerate(health_scores):
        if h is None:
            health_scores[i] = _compute_health(
                mention_rates[i], first_rec_rates[i], positioning_rates[i], sentiment_rates[i]
            )

    latest = reports[-1] if reports else None
    first = reports[0] if reports else None

    # Backfill latest_metrics / first_metrics with computed health score + latest_date
    if latest and latest['core_metrics'].get('aieo_health_score') is None:
        cm = latest['core_metrics']
        latest['core_metrics']['aieo_health_score'] = _compute_health(
            cm.get('ai_mention_rate'), cm.get('ai_first_recommend_rate'),
            cm.get('positioning_consistency_rate'), cm.get('sentiment_positive_rate')
        )
    if first and first['core_metrics'].get('aieo_health_score') is None:
        cm = first['core_metrics']
        first['core_metrics']['aieo_health_score'] = _compute_health(
            cm.get('ai_mention_rate'), cm.get('ai_first_recommend_rate'),
            cm.get('positioning_consistency_rate'), cm.get('sentiment_positive_rate')
        )

    # Question type stats from latest
    question_type_stats = {t: {'total': 0, 'mentioned': 0, 'first_rec': 0}
                           for t in ['brand', 'category', 'comparison', 'scenario', 'longtail']}
    if latest:
        for q in latest['platform_results'].get('questions', []):
            qtype = q.get('type', 'longtail')
            if qtype not in question_type_stats:
                question_type_stats[qtype] = {'total': 0, 'mentioned': 0, 'first_rec': 0}
            for platform, result in q.get('results', {}).items():
                question_type_stats[qtype]['total'] += 1
                if result in ('first_recommend', 'mentioned', 'compared'):
                    question_type_stats[qtype]['mentioned'] += 1
                if result == 'first_recommend':
                    question_type_stats[qtype]['first_rec'] += 1

    # Per-type timeseries
    type_timeseries = {t: [] for t in ['brand', 'category', 'comparison', 'scenario', 'longtail']}
    for r in reports:
        type_counts = {t: {'total': 0, 'mentioned': 0} for t in type_timeseries}
        for q in r['platform_results'].get('questions', []):
            qtype = q.get('type', 'longtail')
            if qtype in type_counts:
                for platform, result in q.get('results', {}).items():
                    type_counts[qtype]['total'] += 1
                    if result in ('first_recommend', 'mentioned', 'compared'):
                        type_counts[qtype]['mentioned'] += 1
        for t in type_timeseries:
            tc = type_counts[t]
            type_timeseries[t].append(round(tc['mentioned'] / tc['total'] * 100, 1) if tc['total'] else None)
    type_timeseries['dates'] = dates

    # Competitor timeseries
    competitor_timeseries = {}
    for r in reports:
        for c in r['competitors']:
            name = c['name']
            if name not in competitor_timeseries:
                competitor_timeseries[name] = {'dates': [], 'rates': []}
            competitor_timeseries[name]['dates'].append(r['date'])
            competitor_timeseries[name]['rates'].append(c.get('mention_rate'))

    # Interceptions from latest (group by question; merge platforms)
    interceptions = []
    if latest:
        seen = {}
        for q in latest['platform_results'].get('questions', []):
            missing_platforms = [p for p, r in q.get('results', {}).items() if r == 'not_mentioned']
            if missing_platforms:
                key = q.get('text', '')
                seen[key] = {
                    'question': key,
                    'platform': '+'.join(missing_platforms),
                    'type': q.get('type', 'longtail'),
                }
        interceptions = list(seen.values())

    # Platform list — from latest platform_results, filtered against known list
    platforms_meta = []
    if latest:
        for p in latest['platform_results'].get('platforms', []):
            if any(kp in p for kp in KNOWN_PLATFORMS):
                platforms_meta.append(p)
        if not platforms_meta:
            # fall back to per-platform performance keys
            platforms_meta = [pp['name'] for pp in latest.get('platform_performance', [])]

    return {
        'schema_version': SCHEMA_VERSION,
        'metadata': {
            'report_count': len(reports),
            'date_range': f"{dates[0]} ~ {dates[-1]}" if dates else 'N/A',
            'latest_date': dates[-1] if dates else None,
            'first_date': dates[0] if dates else None,
            'platforms': platforms_meta,
            'question_count': len(latest['platform_results'].get('questions', [])) if latest else 0,
        },
        'timeseries': {
            'dates': dates,
            'ai_mention_rate': mention_rates,
            'ai_first_recommend_rate': first_rec_rates,
            'positioning_consistency_rate': positioning_rates,
            'sentiment_positive_rate': sentiment_rates,
            'aieo_health_score': health_scores,
        },
        'question_type_stats': question_type_stats,
        'question_type_timeseries': type_timeseries,
        'latest_metrics': latest['core_metrics'] if latest else {},
        'first_metrics': first['core_metrics'] if first else {},
        'latest_platform_results': latest['platform_results'] if latest else {},
        'latest_platform_performance': latest['platform_performance'] if latest else [],
        'latest_competitors': latest['competitors'] if latest else [],
        'competitor_timeseries': competitor_timeseries,
        'interceptions': interceptions,
        'latest_recommendations': latest['recommendations'] if latest else {},
        'all_recommendations': [
            {'date': r['date'], **r['recommendations']}
            for r in reports if any(r['recommendations'].values())
        ],
        'warnings': {r['date']: r['warnings'] for r in reports if r.get('warnings')},
    }


def main():
    if len(sys.argv) < 3:
        print("Usage: python parse_monitoring_reports.py <brand_name> <report_directory> [--output <file.json>]")
        sys.exit(1)

    brand_name = sys.argv[1]
    report_dir = sys.argv[2]
    output_file = None

    if '--output' in sys.argv:
        idx = sys.argv.index('--output')
        if idx + 1 < len(sys.argv):
            output_file = sys.argv[idx + 1]

    if not os.path.isdir(report_dir):
        print(json.dumps({'error': f'Directory not found: {report_dir}'}))
        sys.exit(1)

    files, _summaries = find_reports(brand_name, report_dir)

    if not files:
        print(json.dumps({
            'error': f'No monitoring reports found for brand "{brand_name}" in {report_dir}',
            'searched_pattern': f'{brand_name}_AIEO监控报告_*.md',
            'files_found': 0
        }))
        sys.exit(1)

    print(f"Found {len(files)} reports for {brand_name}", file=sys.stderr)

    # Derive brand aliases to filter self-references in competitor extraction.
    # Heuristic: brand_name + any "{brand_name}是...全称" found in first report.
    brand_aliases = [brand_name]
    try:
        with open(files[-1], 'r', encoding='utf-8') as f:
            first_content = f.read()
        # Look for "Brand (FullName)" or "FullName (Brand)" patterns
        for m in re.finditer(r'(?:' + re.escape(brand_name) + r'[（(]([一-龥]{4,20})[)）]|([一-龥]{4,20})[（(]' + re.escape(brand_name) + r'[)）])', first_content):
            alias = m.group(1) or m.group(2)
            if alias:
                brand_aliases.append(alias)
        # Also pick up "全称：XXX" lines
        for m in re.finditer(r'(?:全称|品牌全称)[：:]\s*([一-龥A-Za-z]{4,30})', first_content):
            brand_aliases.append(m.group(1).strip())
    except Exception:
        pass
    brand_aliases = list(set(brand_aliases))

    reports = []
    for f in files:
        try:
            parsed = parse_single_report(f, brand_aliases=brand_aliases)
            reports.append(parsed)
            warn_str = f" [{len(parsed['warnings'])} warnings]" if parsed['warnings'] else ''
            print(f"  Parsed: {os.path.basename(f)} ({parsed['date']}){warn_str}", file=sys.stderr)
        except Exception as e:
            print(f"  Warning: Failed to parse {os.path.basename(f)}: {e}", file=sys.stderr)

    aggregated = aggregate_data(reports)
    aggregated['metadata']['brand'] = brand_name
    aggregated['metadata']['source_files'] = [os.path.basename(f) for f in files]

    output = json.dumps(aggregated, ensure_ascii=False, indent=2)

    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"Output written to {output_file}", file=sys.stderr)
        print(f"Schema version: {SCHEMA_VERSION}", file=sys.stderr)
    else:
        print(output)


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Build an offline AIEO report from reviewed evidence, using only the stdlib."""
import argparse
from collections import Counter
from datetime import date, datetime
from html import escape
import json
import re
from pathlib import Path
import base64
from string import Template
from urllib.parse import urlsplit

import visuals as viz

STATUS = {'complete': '已取得', 'timeout': '超时', 'login_required': '需登录', 'captcha': '验证码拦截', 'rate_limited': '限流',
          'refused': '拒答', 'truncated': '回答截断', 'error': '采集错误', 'missing': '未取得'}
STATUSES = set(STATUS)
COHORT = {'natural': '自然发现（未点名品牌）', 'branded': '点名品牌', 'comparison': '点名比较', 'constrained': '限定条件'}
VERDICT = {'correct': '与核验依据一致', 'incorrect': '与核验依据不符', 'unverified': '未核实'}
CITATION = {'complete': '已完整采集', 'partial': '部分采集', 'unavailable': '未能采集'}
KIND = {'body': '正文引用', 'panel': '来源面板'}
PRIORITIES = ('P0', 'P1', 'P2')
CHARTS = {'journey', 'visibility', 'matrix', 'sources', 'gaps', 'facts', 'site'}
CHECK_STATUS = {'good', 'warning', 'critical'}
IMAGE_TYPES = {'.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.webp': 'image/webp'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def web_url(value):
    u = urlsplit(value)
    return u.scheme in {'https', 'http'} and bool(u.hostname) and not u.username and not u.password


def check_shot(shot):
    require(isinstance(shot.get('caption'), str) and shot['caption'].strip(), 'screenshot caption required')
    path = Path(shot.get('path', ''))
    require(shot.get('path') and not path.is_absolute() and '..' not in path.parts and path.suffix.lower() in IMAGE_TYPES, 'screenshot path must be relative png/jpg/webp inside the report folder')


def validate(d):
    for key in ('brand', 'target', 'date', 'summary', 'scope_note', 'methodology'):
        require(isinstance(d.get(key), str) and d[key].strip(), f'{key}: required text')
    date.fromisoformat(d['date'])
    for key in ('entities', 'platforms', 'limitations'):
        values = d.get(key)
        require(isinstance(values, list) and values and all(isinstance(x, str) and x.strip() for x in values), f'{key}: nonempty text list')
        require(len(values) == len(set(values)), f'{key}: duplicates')
    require(d['target'] in d['entities'], 'target must be in frozen entities')
    require(isinstance(d.get('questions'), list) and d['questions'], 'questions required')
    qs = {}
    for q in d['questions']:
        for k in ('id', 'text', 'topic', 'cohort'):
            require(isinstance(q.get(k), str) and q[k].strip(), f'question {k} required')
        require(q['cohort'] in {'natural', 'branded', 'comparison', 'constrained'}, 'invalid cohort')
        require(q['id'] not in qs, 'duplicate question id')
        qs[q['id']] = q
    sections = d.get('sections', [])
    require(isinstance(sections, list), 'sections must be a list')
    require({'context', 'website'} <= {s.get('id') for s in sections}, 'sections must include context and website (rendered as appendix)')
    require(not {'findings', 'actions'} & {s.get('id') for s in sections}, 'findings/actions are structured fields now: use key_findings, priorities, actions')
    def texts(obj, keys, where):
        for k in keys:
            require(isinstance(obj.get(k), str) and obj[k].strip(), f'{where}: {k} required text')
    def check_table(c, where):
        texts(c, ('title',), where)
        require(isinstance(c.get('headers'), list) and c['headers'] and isinstance(c.get('rows'), list) and c['rows'], f'{where}: headers/rows required')
        require(all(isinstance(r, list) and len(r) == len(c['headers']) for r in c['rows']), f'{where}: row width must match headers')
    actions = d.get('actions')
    require(isinstance(actions, list) and actions, 'actions: nonempty list')
    action_ids = set()
    for a in actions:
        texts(a, ('id', 'title', 'action', 'deliverable', 'owner', 'timing', 'acceptance'), 'action')
        require(a.get('priority') in PRIORITIES, 'action priority must be P0/P1/P2')
        require(a['id'] not in action_ids, f'duplicate action id {a["id"]}')
        action_ids.add(a['id'])
    findings = d.get('key_findings')
    require(isinstance(findings, list) and 1 <= len(findings) <= 5, 'key_findings: 1-5 items')
    for f in findings:
        texts(f, ('title', 'impact', 'detail'), 'key_finding')
        require(isinstance(f.get('evidence'), list) and f['evidence'] and all(x in qs for x in f['evidence']), 'key_finding evidence must list question ids')
        require(isinstance(f.get('actions'), list) and f['actions'] and all(x in action_ids for x in f['actions']), 'key_finding actions must list action ids')
        for c in f.get('tables', []):
            check_table(c, 'finding table')
    linked = {x for f in findings for x in f['actions']} | {x for n in d.get('notes', []) for x in n.get('actions', [])}
    require(action_ids <= linked, f'every action must answer a finding or note: {sorted(action_ids - linked)}')
    for n in d.get('notes', []):
        texts(n, ('title', 'detail'), 'note')
        require(all(x in qs for x in n.get('evidence', [])) and all(x in action_ids for x in n.get('actions', [])), 'note evidence/actions must reference known ids')
    answers = {}
    for r in d.get('records', []):
        if r.get('status') == 'complete':
            answers.setdefault(r.get('question_id'), []).append(r.get('answer', ''))
    for f in findings:
        require(set(f.get('charts', [])) <= CHARTS - {'journey'}, f'finding charts must be from {sorted(CHARTS - {"journey"})}')
        for qt in f.get('quotes', []):
            require(qt.get('question') in qs and isinstance(qt.get('text'), str) and qt['text'] and any(qt['text'] in a for a in answers.get(qt['question'], [])), 'finding quote must occur verbatim in that question\'s answer')
        for shot in f.get('screenshots', []):
            check_shot(shot)
    if 'site' in {c for f in findings for c in f.get('charts', [])}:
        require(d.get('site_checks'), 'site chart needs site_checks')
    for c in d.get('site_checks', []):
        texts(c, ('item', 'note'), 'site_check')
        require(c.get('status') in CHECK_STATUS, 'site_check status must be good/warning/critical')
    for c in d.get('source_categories', []):
        texts(c, ('label',), 'source_category')
        require(isinstance(c.get('match'), list) and c['match'] and all(isinstance(x, str) and x for x in c['match']), 'source_category match: nonempty substrings')
    if d.get('provider'):
        texts(d['provider'], ('name',), 'provider')
    if d.get('engagement'):
        e = d['engagement']
        texts(e, ('title', 'intro', 'contact'), 'engagement')
        require(isinstance(e.get('offers'), list) and 1 <= len(e['offers']) <= 4, 'engagement offers: 1-4')
        for o in e['offers']:
            texts(o, ('name', 'desc', 'deliverable', 'timing'), 'engagement offer')
    require('priorities' not in d and 'comparisons' not in d, 'priorities/comparisons were folded in: put tables under key_findings[].tables and link actions by id')
    require(isinstance(d.get('records'), list), 'records must be a list')
    seen = set()
    for r in d['records']:
        key = (r.get('platform'), r.get('question_id'))
        require(key[0] in d['platforms'] and key[1] in qs, 'record outside sampling plan')
        require(key not in seen, f'duplicate sample {key}; keep retries in raw evidence')
        seen.add(key)
        require(r.get('status') in STATUSES, f'invalid status: {key}')
        if r['status'] != 'complete':
            require(isinstance(r.get('reason'), str) and r['reason'].strip(), f'failure reason required: {key}')
            continue
        for k in ('answer', 'captured_at', 'mode', 'url', 'evidence_id'):
            require(isinstance(r.get(k), str) and r[k].strip(), f'{key}: {k} required')
        require(datetime.fromisoformat(r['captured_at']).tzinfo is not None, 'captured_at requires timezone')
        require(web_url(r['url']), 'invalid conversation URL')
        mentions = r.get('mentions')
        require(isinstance(mentions, list) and all(x in d['entities'] for x in mentions), 'mentions must use frozen entity names in first-occurrence order')
        require(len(mentions) == len(set(mentions)), 'mentions must be deduplicated per answer')
        require(r.get('citation_status') in {'complete', 'partial', 'unavailable'}, 'citation_status required')
        require(isinstance(r.get('sources'), list), 'sources required (empty allowed)')
        for src in r['sources']:
            require(src.get('kind') in {'body', 'panel'}, 'source kind must be body or panel')
            require(isinstance(src.get('title'), str), 'source title required')
            require(isinstance(src.get('url'), str) and (not src['url'] or web_url(src['url'])), 'invalid source URL')
            require(src['url'] or src['title'], 'source needs title or URL')
            require(not (r['citation_status'] == 'complete' and src['kind'] == 'body' and not src['url']), 'body citation without URL is not complete')
        note = r.get('sentiment')
        if note is not None:
            require(d['target'] in mentions, 'sentiment requires target mention')
            require(isinstance(note.get('label'), str) and note['label'].strip(), 'sentiment label required')
            require(isinstance(note.get('quote'), str) and note['quote'] and note['quote'] in r['answer'], 'sentiment quote must occur in answer')
        for claim in r.get('claims', []):
            require(claim.get('verdict') in {'correct', 'incorrect', 'unverified'}, 'invalid fact verdict')
            require(isinstance(claim.get('quote'), str) and claim['quote'] and claim['quote'] in r['answer'], 'claim quote must occur in answer')
            require(isinstance(claim.get('note'), str) and claim['note'].strip(), 'claim note required')
            require(isinstance(claim.get('source'), str) and (web_url(claim['source']) or (claim['verdict'] == 'unverified' and not claim['source'])), 'verified claim needs authoritative source URL')
            require(isinstance(claim.get('sensitive', False), bool), 'claim sensitive must be boolean')
        for shot in r.get('key_screenshots', []):
            check_shot(shot)
    require(isinstance(d.get('owned_domains', []), list), 'owned_domains must be a list')
    for domain in d.get('owned_domains', []):
        require(isinstance(domain, str) and domain == (urlsplit('https://' + domain).hostname or '') and '/' not in domain, 'owned_domains must contain lowercase hostnames')
    return qs


def ratio(n, denominator):
    return {'numerator': n, 'denominator': denominator, 'value': n / denominator if denominator else None}


def metrics(rows, target, entities, owned):
    good = [r for r in rows if r['status'] == 'complete']
    counts = {e: sum(e in r['mentions'] for r in good) for e in entities}
    hit, n = counts[target], len(good)
    ranks = [r['mentions'].index(target) + 1 for r in good if target in r['mentions']]
    domains = Counter()
    citations = own = 0
    for r in good:
        domains.update({urlsplit(s['url']).hostname.lower().removeprefix('www.') for s in r['sources'] if s['url']})
        urls = {s['url'] for s in r['sources'] if s['kind'] == 'body' and s['url']}
        citations += len(urls)
        own += sum(any(urlsplit(u).hostname == d or urlsplit(u).hostname.endswith('.' + d) for d in owned) for u in urls)
    citation_ready = bool(good) and bool(owned) and all(r['citation_status'] == 'complete' for r in good)
    return dict(planned=len(rows), valid=n, missing=len(rows)-n, counts=counts,
                coverage=ratio(hit, n), visibility=ratio(hit, sum(bool(r['mentions']) for r in good)),
                sov=ratio(hit, sum(counts.values())), position=ratio(sum(ranks), len(ranks)),
                citation_share=ratio(own, citations) if citation_ready else None,
                citation_note='正文 URL 按回答去重的项目口径' if citation_ready else 'N/A：未声明自有域名、无有效样本或正文引用未完整采集',
                observed_domains=dict(domains.most_common()),
                sentiment=dict(Counter(r['sentiment']['label'] for r in good if r.get('sentiment'))))


def planned_rows(d):
    records = {(r['platform'], r['question_id']): r for r in d['records']}
    return [records.get((p, q['id']), dict(platform=p, question_id=q['id'], status='missing', reason='计划内未取得记录'))
            for p in d['platforms'] for q in d['questions']]


def esc(value):
    return escape(str(value), quote=True)


def link(url, label):
    return f'<a href="{esc(url)}" target="_blank" rel="noopener noreferrer">{esc(label)}</a>' if url and web_url(url) else esc(label + '（URL 未取得）')


def table(headers, rows):
    return '<div class="scroll"><table><thead><tr>' + ''.join(f'<th scope="col">{esc(x)}</th>' for x in headers) + '</tr></thead><tbody>' + ''.join('<tr>' + ''.join(f'<td>{esc(x)}</td>' for x in row) + '</tr>' for row in rows) + '</tbody></table></div>'


def display(r, percent=True):
    if r is None or r['value'] is None:
        return 'N/A'
    value = f"{r['value'] * 100:.1f}%" if percent else f"{r['value']:.2f}"
    return f"{value}（{r['numerator']}/{r['denominator']}）"


def embed(base, shot):
    # check_shot already rejects absolute paths and '..'; symlinked evidence folders are allowed.
    path = base / shot['path']
    require(path.is_file(), f'screenshot not found: {shot["path"]}')
    data = base64.b64encode(path.read_bytes()).decode()
    return f'<figure><img src="data:{IMAGE_TYPES[path.suffix.lower()]};base64,{data}" alt="{esc(shot["caption"])}"><figcaption>{esc(shot["caption"])}</figcaption></figure>'


def render(d, base=None, appendix=False):
    """base: folder that screenshot paths are relative to. appendix=False gives the client edition;
    appendix=True adds method, metrics and full answers (the copy that ships inside the evidence zip)."""
    qs = validate(d)
    base = Path(base or '.')
    rows = planned_rows(d)
    natural = [r for r in rows if qs[r['question_id']]['cohort'] == 'natural']
    calc = lambda rs: metrics(rs, d['target'], d['entities'], d.get('owned_domains', []))
    m = calc(natural)
    output = dict(definition='Profound 公开指标的项目适配；按回答去重；主口径仅 natural',
                  entities=d['entities'], primary=m,
                  platforms={p: calc([r for r in natural if r['platform'] == p]) for p in d['platforms']},
                  topics={t: calc([r for r in natural if qs[r['question_id']]['topic'] == t]) for t in dict.fromkeys(q['topic'] for q in qs.values() if q['cohort'] == 'natural')})
    # ---- visuals computed from records (never hand-typed) ----
    target, owned = d['target'], d.get('owned_domains', [])
    done = [r for r in rows if r['status'] == 'complete']
    nat_done = [r for r in done if qs[r['question_id']]['cohort'] == 'natural']
    other_done = [r for r in done if qs[r['question_id']]['cohort'] != 'natural']
    cats = d.get('source_categories', [])
    def category(host):
        if any(host == o or host.endswith('.' + o) for o in owned):
            return '品牌官网'
        return next((c['label'] for c in cats if any(x in host for x in c['match'])), '其他网站')
    cat_order = ['品牌官网'] + [c['label'] for c in cats] + ['其他网站']
    hosts = lambda r: {urlsplit(s['url']).hostname.lower().removeprefix('www.') for s in r['sources'] if s['url']}
    rating = {'good': '良好', 'warning': '一般', 'critical': '较弱', 'neutral': '未测'}
    def level(hit, n):
        return 'neutral' if not n else 'critical' if hit == 0 else 'warning' if hit * 2 < n else 'good'
    claims_all = [c for r in done for c in r.get('claims', [])]
    verdicts = Counter(c['verdict'] for c in claims_all)
    stages = []
    def stage(name, ask, rs):
        hit = sum(target in r['mentions'] for r in rs)
        st = level(hit, len(rs))
        stages.append(dict(name=name, ask=ask, stat=f'{hit} / {len(rs)} 条回答提到品牌', status=st, label=rating[st]))
    # Only stages where the answer was not forced: a named question always 'mentions' the brand, so it is no stage.
    stage('被发现', '不提品牌名，问“有哪些供应商”', nat_done)
    if claims_all:
        st = 'critical' if verdicts['incorrect'] else 'warning' if verdicts['unverified'] else 'good'
        stages.append(dict(name='被说对', ask='核对参数、质保、资质等事实', stat=f'{verdicts["correct"]} 项一致 · {verdicts["incorrect"]} 项答错', status=st, label=rating[st]))
    if owned and done:
        own_hit = sum('品牌官网' in {category(h) for h in hosts(r)} for r in done)
        st = level(own_hit, len(done))
        stages.append(dict(name='被引用', ask='回答是否以品牌官网为依据', stat=f'{own_hit} / {len(done)} 条回答引用官网', status=st, label=rating[st]))
    if d.get('site_checks'):
        sc = Counter(c['status'] for c in d['site_checks'])
        st = 'warning' if sc['critical'] else 'good'
        stages.append(dict(name='官网基础', ask='AI 能否读取官网内容', stat=f'{sc["good"]} / {len(d["site_checks"])} 项已具备', status=st, label=rating[st]))
    snapshot = viz.journey(stages)

    def chart(key):
        if key == 'visibility':
            n = len(nat_done)
            rs = sorted(((e, sum(e in r['mentions'] for r in nat_done), n, e == target) for e in d['entities']), key=lambda x: (-x[1], not x[3]))
            return viz.bars('未点名品牌的问题中，各品牌被提到的次数', f'每条回答按品牌去重计数；共 {n} 条有效回答。被提到不等于被推荐。', rs, '条回答提到')
        if key == 'matrix':
            groups = []
            for cohort in ('natural', 'branded', 'comparison', 'constrained'):
                items = [(r['question_id'] + (f' · {r["platform"]}' if len(d['platforms']) > 1 else ''), qs[r['question_id']]['text'], r['mentions'])
                         for r in done if qs[r['question_id']]['cohort'] == cohort]
                if items:
                    groups.append((COHORT[cohort], items))
            miss = len(rows) - len(done)
            return viz.matrix('逐题出现情况：每个问题里，谁被提到了', '数字为该品牌在回答中首次出现的顺序' + (f'；另有 {miss} 条缺测未列出' if miss else '') + '。', groups, d['entities'], target)
        if key == 'sources':
            series = [(name, [(sum(cat in {category(h) for h in hosts(r)} for r in rs), len(rs)) for cat in cat_order]) for name, rs in
                      [('未点名品牌的问题', nat_done), ('点名品牌 / 比较的问题', other_done)] if rs]
            html = viz.grouped_bars('AI 回答引用了哪些类型的来源', '出现该类来源的回答数 / 有效回答数；来源采集不完整时为下限观察。', cat_order, series, '条回答')
            plays = [c for c in cats if c.get('play')]
            if plays:
                html += '<ul class="plays">' + ''.join(f'<li><b>{esc(c["label"])}</b>{esc(c["play"])}</li>' for c in plays) + '</ul>'
            return html
        if key == 'gaps':
            gap_rows = [r for r in done if target not in r['mentions'] and set(r['mentions']) - {target}]
            counter = Counter(h for r in gap_rows for h in hosts(r) if category(h) != '品牌官网')
            top = sorted(counter.items(), key=lambda kv: (-kv[1], kv[0]))[:8]  # ties by name: same output every run
            html = viz.bars('竞品被提到、你缺席的回答里，AI 最常用的来源', f'共 {len(gap_rows)} 条回答提到比较品牌但没有提到{target}；这些网站是优先争取出现的外部渠道。',
                            [(f'{h}（{category(h)}）', c, len(gap_rows), True) for h, c in top], '条回答出现')
            return html
        if key == 'facts':
            segs = [('与官网或权威资料一致', verdicts['correct'], 'good'), ('答错', verdicts['incorrect'], 'critical'), ('缺依据 / 未核实', verdicts['unverified'], 'warning')]
            return viz.stacked('AI 对品牌事实的回答准确吗', f'逐条核验回答中的具体说法，共 {len(claims_all)} 项；未核实不等于错误。', segs)
        if key == 'site':
            return viz.checklist('官网 AI 就绪度检查', '抽查页面的可抓取性、结构与内容；不代表全站结论。', d['site_checks'])
        raise ValueError(key)

    # Client-facing body: finding -> its own evidence -> linked actions. No bare percentages on the first screen.
    finding_no = {}
    for i, f in enumerate(d['key_findings']):
        for x in f['actions']:
            finding_no.setdefault(x, []).append(str(i + 1))
    for n in d.get('notes', []):
        for x in n.get('actions', []):
            finding_no.setdefault(x, []).append('另需关注')
    ordered = sorted(d['actions'], key=lambda a: PRIORITIES.index(a['priority']))
    alink = lambda ids: '、'.join(f'<a href="#action-{esc(x)}">{esc(x)}</a>' for x in ids)
    finding_titles = ''.join(f'<li><a href="#finding-{i}">{esc(f["title"])}</a></li>' for i, f in enumerate(d['key_findings']))
    first = ordered[:3]
    first_actions = ''.join(f'<li><a href="#action-{esc(a["id"])}">{esc(a["id"])}</a> {esc(a["title"])}</li>' for a in first)
    findings = ''
    for i, f in enumerate(d['key_findings']):
        tables = ''.join(f'<h4>{esc(c["title"])}</h4>' + table(c['headers'], c['rows']) + (f'<p class="scope">{esc(c["note"])}</p>' if c.get('note') else '') for c in f.get('tables', []))
        charts = ''.join(chart(k) for k in f.get('charts', []))
        quotes = ''
        by_q = {}  # quotes from one question share one card, so the question is cited once
        for qt in f.get('quotes', []):
            by_q.setdefault(qt['question'], []).append(qt['text'])
        for qid, texts_ in by_q.items():
            plat = next(r['platform'] for r in done if r['question_id'] == qid and texts_[0] in r['answer'])
            quotes += '<blockquote class="quote">' + ''.join(f'<p>{esc(t)}</p>' for t in texts_) + f'<cite>{esc(plat)} 原话 · {esc(qid)} {esc(qs[qid]["text"])}</cite></blockquote>'
        shots = ''.join(embed(base, shot) for shot in f.get('screenshots', []))
        findings += (f'<article class="finding" id="finding-{i}"><div class="finding-no">发现 {i + 1:02d}</div><h3>{esc(f["title"])}</h3><p class="impact">业务影响：{esc(f["impact"])}</p>'
                     f'<p>{esc(f["detail"])}</p>{charts}{quotes}{tables}{shots}<p class="meta">证据：{esc("、".join(f["evidence"]))}（{{EVIDENCE_REF}}） · 对应行动：{alink(f["actions"])}</p></article>')
    notes = ''
    if d.get('notes'):
        notes = '<section id="notes" class="chapter"><h2>另需关注</h2><p class="scope">以下情况不是本轮主结论，但可能影响采购信任或客户预期。</p>' + ''.join(
            f'<article class="note"><h3>{esc(n["title"])}</h3><p>{esc(n["detail"])}</p>'
            + (f'<p class="meta">证据：{esc("、".join(n.get("evidence", [])))}' if n.get('evidence') else '<p class="meta">')
            + (f' · 对应行动：{alink(n["actions"])}' if n.get('actions') else '') + '</p></article>' for n in d['notes']) + '</section>'
    heads = ['编号', '优先级', '动作', '交付物', '负责人', '时间', '验收方式', '对应发现']
    actions = '<div class="scroll"><table><thead><tr>' + ''.join(f'<th scope="col">{h}</th>' for h in heads) + '</tr></thead><tbody>' + ''.join(
        f'<tr id="action-{esc(a["id"])}">' + ''.join(f'<td>{esc(x)}</td>' for x in [a['id'], a['priority'], a['title'] + '：' + a['action'], a['deliverable'], a['owner'], a['timing'], a['acceptance'], '、'.join(finding_no[a['id']])]) + '</tr>'
        for a in ordered) + '</tbody></table></div>'
    roadmap = viz.gantt('90 天路线图', '横条为计划时间段，颜色深浅对应优先级。', ordered)
    engagement = ''
    if d.get('engagement'):
        e = d['engagement']
        engagement = (f'<section id="engage" class="engage"><div class="engage-inner"><div class="eyebrow">下一步</div><h2>{esc(e["title"])}</h2><p class="lead">{esc(e["intro"])}</p><div class="offers">'
                      + ''.join(f'<article class="offer"><div class="offer-no">{i + 1:02d}</div><h3>{esc(o["name"])}</h3><p>{esc(o["desc"])}</p><dl><dt>交付</dt><dd>{esc(o["deliverable"])}</dd><dt>周期</dt><dd>{esc(o["timing"])}</dd></dl></article>' for i, o in enumerate(e['offers']))
                      + '</div><p class="contact">' + esc(e['contact']) + '{cta}</p></div></section>')
    pv = d.get('provider') or {}
    cta = f'<a class="cta" href="{esc(pv["url"])}" target="_blank" rel="noopener noreferrer">预约结果解读 →</a>' if pv.get('url') and web_url(pv['url']) else ''
    engagement = engagement.replace('{cta}', cta)
    provider = esc(pv.get('name', 'AIEO 诊断'))
    provider_line = ' · '.join(esc(x) for x in [pv.get('tagline'), pv.get('contact')] if x)
    if pv.get('url') and web_url(pv['url']):
        provider_line += (' · ' if provider_line else '') + link(pv['url'], urlsplit(pv['url']).hostname)
    card_specs = [('全部回答覆盖率', 'coverage'), ('条件可见率', 'visibility'), ('限定集合声量份额', 'sov'), ('平均首次文字位置', 'position')]
    cards = ''.join(f'<article class="card"><h3>{label}</h3><strong>{display(m[k], k != "position")}</strong></article>' for label, k in card_specs)
    sections = ''.join(f'<section id="section-{i}"><h2>附录 · {esc(s["title"])}</h2>' + ''.join(f'<p>{esc(p)}</p>' for p in s['paragraphs']) + '</section>' for i, s in enumerate(d['sections']))
    metric_html = '<h3>平台切片：自然发现题</h3>' + table(['平台', '有效/计划', '覆盖率', '条件可见率', '声量份额', '文字位置'],
        [[p, f'{s["valid"]}/{s["planned"]}', display(s['coverage']), display(s['visibility']), display(s['sov']), display(s['position'], False)] for p, s in output['platforms'].items()])
    metric_html += '<h3>主题切片：自然发现题</h3>' + table(['主题', '有效/计划', '覆盖率', '声量份额'], [[t, f'{s["valid"]}/{s["planned"]}', display(s['coverage']), display(s['sov'])] for t, s in output['topics'].items()])
    metric_html += f'<h3>引用来源</h3><p>自有域名引用份额：{display(m["citation_share"])}。{esc(m["citation_note"])}各类来源与域名见正文发现中的来源图表。</p>'
    metric_html += '<p>各品牌提及次数见正文可见度图表；逐项事实核验的原句、判定与依据见下方证据附录的每条回答。</p>'
    evidence = []
    for r in rows:
        q = qs[r['question_id']]
        detail = f'<p>{esc(q["text"])}</p><p>题型：{esc(COHORT[q["cohort"]])} · 主题：{esc(q["topic"])}</p>'
        if r['status'] == 'complete':
            detail += f'<p>{esc(r["captured_at"])} · {esc(r["mode"])} · 证据编号 {esc(r["evidence_id"])}</p><p>{link(r["url"], "原会话")}</p><pre>{esc(r["answer"])}</pre>'
            detail += '<p>比较集合首次出现顺序：' + esc(' → '.join(r['mentions']) or '未提及比较集合') + '</p>'
            detail += ''.join(embed(base, shot) for shot in r.get('key_screenshots', []))
            if r.get('sentiment'):
                detail += f'<p>叙事：{esc(r["sentiment"]["label"])}；原句：{esc(r["sentiment"]["quote"])}</p>'
            detail += f'<p>正文引用：{esc(CITATION[r["citation_status"]])}</p>'
            detail += '<ul>' + ''.join(f'<li>{esc(KIND[s["kind"]])} · {link(s["url"], s["title"] or s["url"])}</li>' for s in r['sources']) + '</ul>'
            if not r['sources']:
                detail += '<p>未取得来源记录；不推断平台未检索。</p>'
            for c in r.get('claims', []):
                label = '未核实的企业背景说法（模型原句，非本报告认定）' if c.get('sensitive') else '事实核验'
                detail += f'<p>{label}：{esc(c["quote"])} — {esc(VERDICT[c["verdict"]])}。{esc(c["note"])} {link(c["source"], "核验依据") if c["source"] else ""}</p>'
        else:
            detail += '<p>缺测原因：' + esc(r['reason']) + '</p>'
        evidence.append(f'<details class="evidence" data-platform="{esc(r["platform"])}" data-question="{esc(q["id"])}"><summary>{esc(r["platform"])} · {esc(q["id"])} · {esc(STATUS[r["status"]])}</summary>{detail}</details>')
    scope = esc(d['scope_note']) + f'。主结论基于 {m["valid"]} 条未点名品牌的自然发现回答' + (f'（另有 {m["missing"]} 条缺测）' if m['missing'] else '') + '；{METHOD_REF}。'
    template = Template((Path(__file__).resolve().parent.parent / 'assets/report.html').read_text(encoding='utf-8'))
    html = template.substitute(title=esc(d['brand'] + ' · AI 搜索可见度诊断'), scope_chip=esc(f'{len(qs)} 个问题 · {len(done)} 条有效回答'), date=esc(d['date']), summary=esc(d['summary']), scope=scope,
        finding_titles=finding_titles, first_actions=first_actions, findings=findings, notes=notes,
        notes_nav='<a href="#notes">另需关注</a>' if notes else '', actions=roadmap + actions, snapshot=snapshot,
        engagement=engagement, engage_nav='<a href="#engage">合作方式</a>' if engagement else '', provider=provider, provider_line=provider_line,
        platform=esc('、'.join(d['platforms'])),
        methodology=esc(d['methodology']), entities=esc('、'.join(d['entities'])),
        limitations=''.join(f'<li>{esc(x)}</li>' for x in d['limitations']), cards=cards, sections=sections, metrics=metric_html,
        navigation=''.join(f'<a href="#section-{i}">{esc(s["title"])}</a> · ' for i, s in enumerate(d['sections'])),
        platforms=''.join(f'<option>{esc(p)}</option>' for p in d['platforms']),
        questions=''.join(f'<option value="{esc(q["id"])}">{esc(q["id"] + " · " + q["text"])}</option>' for q in qs.values()), evidence=''.join(evidence))
    if appendix:
        refs = {'{EVIDENCE_REF}': '见证据附录', '{METHOD_REF}': '方法与限制见附录',
                '{FOOTER_NOTE}': '正文、指标、完整回答与关键截图均内嵌，单文件可离线阅读。原会话和外部来源链接需要网络及相应访问权限。'}
    else:  # client edition: body only; method, metrics and full answers live in the evidence-zip copy
        html = re.sub(r'<section id="appendix".*?</main>', '</main>', html, flags=re.S).replace('<a href="#appendix">附录</a>', '')
        refs = {'{EVIDENCE_REF}': '完整回答见证据包', '{METHOD_REF}': '方法、限制与完整回答见证据包',
                '{FOOTER_NOTE}': '正文与关键截图内嵌，单文件可离线阅读；采样方法、指标口径与全部回答见配套证据包。'}
    for k, v in refs.items():
        html = html.replace(k, v)
    return html, output


def check():
    import copy
    d = dict(brand='测试品牌 <script>alert(1)</script>', target='甲', date='2026-09-25', summary='合成样例，非客户诊断', scope_note='平台 5 题 · 单日单账号',
             methodology='固定样本，人工复核', entities=['甲', '乙'], platforms=['平台'], limitations=['合成数据'], owned_domains=['example.com'],
             sections=[dict(id=i, title=i, paragraphs=['合成数据']) for i in ['context', 'website']],
             provider=dict(name='测试机构', url='https://example.com'),
             source_categories=[dict(label='测试平台', match=['example'], play='合成打法')],
             site_checks=[dict(item='可访问', status='good', note='合成'), dict(item='替代文本', status='warning', note='合成')],
             engagement=dict(title='合作', intro='合成', contact='联系', offers=[dict(name='监测', desc='合成', deliverable='报告', timing='按月')]),
             key_findings=[dict(title='自然题未获提及', impact='合成影响', detail='合成细节', evidence=['1'], actions=['A2'],
                                charts=['visibility', 'matrix', 'sources', 'gaps', 'facts', 'site'], quotes=[dict(question='1', text='乙，甲')],
                                tables=[dict(title='对照', headers=['项', '值'], rows=[['a', 'b']])]),
                           dict(title='事实偏差', impact='合成影响', detail='合成细节', evidence=['4'], actions=['A1'])],
             notes=[dict(title='背景评价', detail='合成', evidence=['4'], actions=['A1'])],
             actions=[dict(id='A2', title='复测', priority='P1', action='复测', deliverable='报告', owner='市场', timing='61–90 天', acceptance='同口径'),
                      dict(id='A1', title='纠错', priority='P0', action='纠错', deliverable='参数表', owner='技术', timing='0–30 天', acceptance='复测无误')],
             questions=[dict(id=str(i), text='测试问题', topic='选购', cohort='natural' if i < 4 else 'branded') for i in range(5)], records=[])
    for i, mentions in enumerate([['乙', '甲'], ['乙'], [], None, ['甲']]):
        r = dict(platform='平台', question_id=str(i), status='complete', answer='乙，甲 <script>alert(1)</script>',
                 captured_at='2026-09-25T12:00:00+08:00', mode='测试', url='https://example.com/chat', evidence_id=str(i),
                 mentions=mentions, citation_status='complete', sources=[dict(kind='body', title='来源', url='https://example.com/a')]*2)
        if mentions is None:
            r = dict(platform='平台', question_id=str(i), status='timeout', reason='合成超时')
        d['records'].append(r)
    d['records'][4]['claims'] = [dict(quote='乙', verdict='unverified', source='', note='合成', sensitive=True)]
    html, out = render(d)
    m = out['primary']
    body = html.split('<body>')[1].split('id="appendix"')[0]
    text = re.sub(r'<[^>]+>', '', body)
    assert '%' not in text and 'natural' not in text, 'first screen and body must not show bare metrics or field names'
    assert body.index('>P0<') < body.index('>P1<'), 'actions sorted by priority'
    assert 'href="#action-A1"' in body and 'id="action-A1"' in body, 'findings link to actions'
    assert body.index('id="findings"') < body.index('id="notes"') < body.index('id="actions"')
    for marker in ('class="journey"', 'class="matrix"', 'class="stacked"', 'class="checks"', 'class="gantt"', 'class="quote"', 'id="engage"', 'class="cta"', '查看数据表'):
        assert marker in html, f'missing visual {marker}'
    assert '1 / 3 条回答提到品牌' in html, 'journey stat shows counts'
    assert '被认识' not in html, 'named questions are not a visibility stage'
    assert 'id="appendix"' not in html and 'id="evidence"' not in html and '附录' not in re.sub(r'<[^>]+>', '', html.split('<body>')[1]), 'client edition has no appendix'
    assert '模型原句' not in html, 'sensitive claims never reach the client edition'
    assert '{' + 'FOOTER_NOTE}' not in html and '完整回答与关键截图均内嵌' not in html, 'client footer describes the client edition'
    full = render(d, appendix=True)[0]
    assert '模型原句，非本报告认定' in full.split('id="evidence"')[1] and '模型原句' not in full.split('id="evidence"')[0], 'full edition labels sensitive claims only in the evidence appendix'
    assert (m['planned'], m['valid'], m['missing']) == (4, 3, 1)
    assert m['coverage']['value'] == 1/3 and m['visibility']['value'] == 1/2 and m['sov']['value'] == 1/3
    assert m['position']['value'] == 2 and m['citation_share']['denominator'] == 3
    assert '<script>alert(1)</script>' not in html and '&lt;script&gt;' in html
    assert metrics([], '甲', ['甲'], [])['coverage']['value'] is None
    bad = copy.deepcopy(d); bad['records'][0]['sources'][0]['url'] = 'javascript:alert(1)'
    old = copy.deepcopy(d); old['sections'].append(dict(id='findings', title='x', paragraphs=['x']))
    escape_shot = copy.deepcopy(d); escape_shot['records'][0]['key_screenshots'] = [dict(path='../x.png', caption='x')]
    badchart = copy.deepcopy(d); badchart['key_findings'][0]['charts'] = ['pie']
    badquote = copy.deepcopy(d); badquote['key_findings'][0]['quotes'] = [dict(question='1', text='答案里没有这句')]
    orphan = copy.deepcopy(d); orphan['actions'].append(dict(id='A9', title='x', priority='P2', action='x', deliverable='x', owner='x', timing='x', acceptance='x'))
    for sample in [bad, old, escape_shot, orphan, badchart, badquote, {**d, 'records': d['records'] + [d['records'][0]]}]:
        try:
            render(sample)
        except ValueError:
            pass
        else:
            raise AssertionError('unsafe/duplicate input accepted')
    partial = copy.deepcopy(d); partial['records'][0]['citation_status'] = 'partial'
    assert render(partial)[1]['primary']['citation_share'] is None
    missing = copy.deepcopy(d); missing['records'] = []; missing['key_findings'][0]['quotes'] = []
    assert render(missing)[1]['primary']['missing'] == 4
    print('PASS: denominators, cohorts, missingness, URL deduplication, escaping, client layout, visuals and invalid input')
    return d


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', nargs='?', type=Path)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    if args.check:
        check()
        return
    if args.input is None:
        parser.error('provide report.json or --check')
    require(args.input.suffix == '.json' and not args.input.name.endswith('.metrics.json'), 'input must be the report .json')
    data = json.loads(args.input.read_text(encoding='utf-8'))
    content, output = render(data, args.input.parent)
    full, _ = render(data, args.input.parent, appendix=True)
    full_path = args.input.with_name(args.input.stem + '_含证据附录.html')
    args.input.with_suffix('.html').write_text(content, encoding='utf-8')
    full_path.write_text(full, encoding='utf-8')
    args.input.with_suffix('.metrics.json').write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding='utf-8')
    print(args.input.with_suffix('.html'))
    print(full_path)


if __name__ == '__main__':
    main()

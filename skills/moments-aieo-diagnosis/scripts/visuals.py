"""Chart builders for the AIEO report: plain HTML/CSS marks (readable at phone width), stdlib only.

Every figure ships a data-table twin (<details>) and a title-attribute tooltip on each mark,
so no value is gated behind hover or colour. Colours are CSS roles defined in assets/report.html.
"""
from html import escape
import re

STATUS_ICON = {'good': '✓', 'warning': '!', 'critical': '✕', 'neutral': '·'}


def esc(value):
    return escape(str(value), quote=True)


def data_table(headers, rows):
    return ('<details class="dataview"><summary>查看数据表</summary><div class="scroll"><table><thead><tr>'
            + ''.join(f'<th scope="col">{esc(h)}</th>' for h in headers) + '</tr></thead><tbody>'
            + ''.join('<tr>' + ''.join(f'<td>{esc(c)}</td>' for c in r) + '</tr>' for r in rows)
            + '</tbody></table></div></details>')


def figure(title, subtitle, body, table='', legend=''):
    sub = f'<p>{esc(subtitle)}</p>' if subtitle else ''
    return f'<figure class="viz"><figcaption><h4>{esc(title)}</h4>{sub}</figcaption>{legend}{body}{table}</figure>'


def status_chip(status, label):
    return f'<span class="chip chip-{status}"><span class="chip-icon" aria-hidden="true">{STATUS_ICON[status]}</span>{esc(label)}</span>'


def journey(stages):
    """stages: [{name, ask, stat, status, label}] - the buyer journey strip on the first screen."""
    cells = ''.join(
        f'<li class="stage stage-{s["status"]}"><div class="stage-step">{i + 1:02d}</div><h3>{esc(s["name"])}</h3>'
        f'<p class="stage-ask">{esc(s["ask"])}</p><p class="stage-stat">{esc(s["stat"])}</p>{status_chip(s["status"], s["label"])}</li>'
        for i, s in enumerate(stages))
    return f'<ol class="journey" aria-label="AI 采购旅程诊断">{cells}</ol>'


def bars(title, subtitle, rows, denominator_label):
    """Single-series horizontal bars. rows: [(label, value, denominator, emphasized)]. Emphasis, not a rainbow."""
    top = max([r[2] for r in rows] + [1])
    body = ''.join(
        f'<div class="bar-row{" is-focus" if emph else ""}"><span class="bar-label">{esc(label)}</span>'
        f'<span class="bar-track"><span class="bar-mark" style="width:{value / top * 100:.1f}%" title="{esc(label)}：{value} / {den} {esc(denominator_label)}" tabindex="0"></span></span>'
        f'<span class="bar-value">{value} / {den}</span></div>'
        for label, value, den, emph in rows)
    table = data_table(['对象', f'{denominator_label}（分子 / 分母）'], [[l, f'{v} / {d}'] for l, v, d, _ in rows])
    return figure(title, subtitle, f'<div class="bars">{body}</div>', table)


def grouped_bars(title, subtitle, categories, series, unit):
    """categories: [label]; series: [(name, [(value, denominator)])] - at most two series (slots 1-2)."""
    legend = '<div class="legend">' + ''.join(f'<span><i class="swatch s{i + 1}"></i>{esc(name)}</span>' for i, (name, _) in enumerate(series)) + '</div>'
    top = max([d for _, vals in series for _, d in vals] + [1])
    body = ''
    for ci, cat in enumerate(categories):
        marks = ''.join(
            f'<span class="bar-track"><span class="bar-mark s{si + 1}" style="width:{vals[ci][0] / top * 100:.1f}%" '
            f'title="{esc(cat)} · {esc(name)}：{vals[ci][0]} / {vals[ci][1]} {esc(unit)}" tabindex="0"></span>'
            f'<span class="bar-value">{vals[ci][0]} / {vals[ci][1]}</span></span>'
            for si, (name, vals) in enumerate(series))
        body += f'<div class="bar-row grouped"><span class="bar-label">{esc(cat)}</span><span class="bar-stack">{marks}</span></div>'
    table = data_table(['来源类型'] + [n for n, _ in series], [[cat] + [f'{vals[ci][0]} / {vals[ci][1]}' for _, vals in series] for ci, cat in enumerate(categories)])
    return figure(title, subtitle, f'<div class="bars">{body}</div>', table, legend)


def matrix(title, subtitle, groups, entities, target):
    """groups: [(group label, [(qid, question, mentions)])] - prompt x brand coverage grid."""
    head = '<tr><th scope="col">问题</th>' + ''.join(f'<th scope="col" class="{"col-target" if e == target else ""}">{esc(e)}</th>' for e in entities) + '</tr>'
    rows = ''
    table_rows = []
    for label, items in groups:
        rows += f'<tr class="group-row"><th colspan="{len(entities) + 1}" scope="rowgroup">{esc(label)}</th></tr>'
        for qid, text, mentions in items:
            cells = ''
            for e in entities:
                cls = ' col-target' if e == target else ''
                if e in mentions:
                    pos = mentions.index(e) + 1
                    cells += f'<td class="cell{cls}"><span class="dot hit{" target" if e == target else ""}" title="{esc(qid)} · {esc(e)}：第 {pos} 个出现" tabindex="0">{pos}</span></td>'
                else:
                    cells += f'<td class="cell{cls}"><span class="dot miss" title="{esc(qid)} · {esc(e)}：未提及" tabindex="0"><span class="sr">未提及</span></span></td>'
            rows += f'<tr><th scope="row"><b>{esc(qid)}</b> {esc(text)}</th>{cells}</tr>'
            table_rows.append([qid, text] + [f'第 {mentions.index(e) + 1} 个' if e in mentions else '未提及' for e in entities])
    legend = '<div class="legend"><span><i class="dot hit target">1</i>目标品牌出现（数字为首次出现顺序）</span><span><i class="dot hit">1</i>比较品牌出现</span><span><i class="dot miss"></i>未提及</span></div>'
    body = f'<div class="scroll"><table class="matrix"><thead>{head}</thead><tbody>{rows}</tbody></table></div>'
    return figure(title, subtitle, body, data_table(['题号', '问题'] + entities, table_rows), legend)


def stacked(title, subtitle, segments):
    """Part-to-whole in status colours. segments: [(label, count, status)]; icon + label, never colour alone."""
    total = sum(c for _, c, _ in segments) or 1
    marks = ''.join(f'<span class="seg seg-{st}" style="flex:{c}" title="{esc(l)}：{c} 项" tabindex="0"></span>' for l, c, st in segments if c)
    legend = '<div class="legend">' + ''.join(f'<span>{status_chip(st, l)} <b>{c}</b> 项</span>' for l, c, st in segments) + '</div>'
    table = data_table(['判定', '数量', '占已核验说法'], [[l, c, f'{c}/{total}'] for l, c, _ in segments])
    return figure(title, subtitle, f'<div class="stacked" role="img" aria-label="{esc(title)}">{marks}</div>{legend}', table)


def checklist(title, subtitle, checks):
    """checks: [{item, status: good|warning|critical, note}] - website readiness scorecard."""
    label = {'good': '已具备', 'warning': '可加强', 'critical': '缺失'}
    body = '<ul class="checks">' + ''.join(
        f'<li>{status_chip(c["status"], label[c["status"]])}<b>{esc(c["item"])}</b><span>{esc(c["note"])}</span></li>' for c in checks) + '</ul>'
    return figure(title, subtitle, body, data_table(['检查项', '状态', '说明'], [[c['item'], label[c['status']], c['note']] for c in checks]))


DAYS = re.compile(r'(\d+)\s*[–\-~至到]\s*(\d+)\s*天')


def gantt(title, subtitle, actions, horizon=90):
    """actions: sorted action dicts; timing like '0–30 天'. Colour = ordinal priority ramp (P0 darkest)."""
    ticks = ''.join(f'<span style="left:{t / horizon * 100:.1f}%">{t} 天</span>' for t in range(0, horizon + 1, 30))
    rows = ''
    for a in actions:
        m = DAYS.search(a['timing'])
        start, end = (int(m.group(1)), int(m.group(2))) if m else (0, horizon)
        end = min(max(end, start + 1), horizon)
        rows += (f'<div class="gantt-row"><span class="bar-label"><b>{esc(a["id"])}</b> {esc(a["title"])}</span><span class="gantt-track">'
                 f'<span class="gantt-bar pr-{a["priority"]}" style="left:{start / horizon * 100:.1f}%;width:{(end - start) / horizon * 100:.1f}%" '
                 f'title="{esc(a["id"])} {esc(a["title"])}：{esc(a["timing"])} · {esc(a["owner"])}" tabindex="0">{esc(a["priority"])}</span></span></div>')
    legend = '<div class="legend">' + ''.join(f'<span><i class="swatch pr-{p}"></i>{p}</span>' for p in ('P0', 'P1', 'P2')) + '</div>'
    body = f'<div class="gantt"><div class="gantt-axis"><span class="bar-label"></span><span class="gantt-ticks">{ticks}</span></div>{rows}</div>'
    return figure(title, subtitle, body, data_table(['编号', '动作', '优先级', '时间', '负责人'], [[a['id'], a['title'], a['priority'], a['timing'], a['owner']] for a in actions]), legend)

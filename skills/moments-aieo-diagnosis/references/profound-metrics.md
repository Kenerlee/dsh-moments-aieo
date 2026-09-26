# Profound 参考口径与 HTML 输入

## 公开定义与项目适配

核对日期：2026-09-25。参考 [Profound AEI](https://help.tryprofound.com/articles/3443229936-answer-engine-insights-overview?lang=en) 和 [指标解读](https://help.tryprofound.com/articles/6240000968-interpret-answer-engine-insights)。这是公开概念的项目实现，不是 Profound 平台数据或算法复刻。

先冻结目标实体及竞争集合 C、别名、问题/平台/日期/语言/地区/模式。主分析只取不点名任何品牌的 `natural` 题；品牌题 `branded`、竞品对比 `comparison`、带倾向限制的 `constrained` 题保留证据但不混入主指标。每个平台/题目一个主记录，重试仅选预先约定的一条有效结果进入本批；复测另建批次。

N＝自然发现有效回答数；M(e)＝其中提及实体 e 的回答数（每条每实体去重）；E＝其中提及 C 中任意实体的回答数；T＝Σ M(e)。失败、截断、拒答和未取得记录不进入 N，同时展示有效/计划覆盖。不含任何实体的完整回答进入 N，不进入 E。

| 模块 | 本项目计算 | 必须说明的限制 |
|---|---|---|
| 全部回答覆盖率 | M(目标)/N | 补充指标，不冒称 Profound 原生 Visibility |
| Visibility 条件可见率 | M(目标)/E | 公开条件分母的限定集合适配；声明 C，未纳入的品牌不进入 E |
| Share of Voice | M(目标)/T | 回答级去重、限定 C；不是市场份额或推荐率 |
| Position | 各命中回答中目标首次文字序位之和/命中回答数 | 仅在 C 内排序，未出现不填末位；不称原生 Average Position |
| Citations | 自有域名正文引用 URL 数/全部正文引用 URL 数；每回答内按完整 URL 去重 | 只有本切片每条正文引用均完整且已声明自有域名时计算；否则 N/A。URL 规范化规则需固定 |
| 来源域名覆盖 | 含可见来源域名的回答数/N | 正文＋面板已取得 URL 的观察值，来源不全时为下界；不能冒充 Citation Share |
| Sentiment | 人工叙事标签计数，逐条附原句 | 标明已标注样本量，未标注不计中性；不生成专有情感总分 |
| FactCheck | 原句→正确/错误/未核实→权威证据→校正建议 | 逐项列示，未审核不算正确；默认不计算整体准确率 |

分母为零用 N/A，不用 0%。`sources=[]` 不自动表示平台未检索；`citation_status=complete` 必须是确实检查完该回答全部正文引用（包括确认无引用），不能从“采集到了几条链接”推断完整。仅来源面板或只有标题的引用不得填 complete。

别名合并在人工标注阶段完成；`mentions` 使用规范实体名，按首次文字出现顺序排列并去重。公司、商品名、通用名和品类不要混成同一个指标；如有多层实体分析，分别冻结集合计算，在正文补充对应证据与定义。合理风险提示不应被医药/金融诊断直接当成负面形象问题。

无对应数据时，Prompt Volumes、Agent Analytics、用户转化、ROI、历史趋势均为 N/A，并说明补充什么数据才可计算。不得用合成数值填满仪表板。

## 报告 JSON

构建命令：`python3 <skill目录>/scripts/render_report.py <诊断目录>/品牌_AIEO诊断报告_日期.json`。

要求 Python 3.9+，无第三方依赖。输出同目录的 `.html` 与 `.metrics.json`。文本字段用纯文本，HTML/Markdown 标记不会作为页面代码执行。下列为**合成格式示例**，不能作为客户实测数据；执行诊断时全部替换。

```json
{
  "brand": "示例品牌（合成示例）",
  "target": "示例品牌",
  "date": "2026-09-25",
  "entities": ["示例品牌", "示例竞品"],
  "owned_domains": ["example.com"],
  "platforms": ["示例平台"],
  "summary": "2–3 句一页结论：现状、偏差、建议方向（合成格式示例）。",
  "scope_note": "示例平台 · 15 题 · 2026-09-25 单日单账号",
  "methodology": "bb-browser；每题新会话；地区/语言/模式/账号记忆、题库版本及别名字典在此说明（仅含证据附录版显示）。",
  "limitations": ["合成数据，不能用于客户结论"],
  "key_findings": [
    {"title": "采购者不点名品牌提问时，示例品牌没有出现", "impact": "客户在初筛阶段看不到品牌", "detail": "事实、竞品出现情况与推断边界。",
     "charts": ["visibility", "matrix"],
     "quotes": [{"question": "Q01", "text": "示例竞品可供比较"}],
     "screenshots": [{"path": "evidence/batch01/platform_Q01/answer.png", "caption": "Q01 回答截图"}],
     "evidence": ["Q01"], "actions": ["A2"]},
    {"title": "点名询问时，型号参数答错了", "impact": "客户可能按错误规格选型", "detail": "哪些答对、哪些答错。",
     "charts": ["facts", "sources", "gaps", "site"],
     "tables": [{"title": "型号参数：AI 回答 vs 官网公开值", "headers": ["参数", "AI 回答", "官网公开值"], "rows": [["工作压力", "0–16 MPa", "0–8 MPa"]], "note": "核对日期与口径。"}],
     "evidence": ["Q01"], "actions": ["A1"]}
  ],
  "provider": {"name": "我们的机构名", "tagline": "AI 搜索可见度诊断与优化", "url": "https://example.com"},
  "source_categories": [{"label": "B2B 黄页", "match": ["b2b168", "1688"], "play": "统一店铺页参数与官网链接"}],
  "site_checks": [{"item": "页面可正常访问", "status": "good", "note": "抽查 10 页均返回 200"}],
  "engagement": {"title": "从一次诊断，到持续被 AI 正确推荐", "intro": "单平台单日快照，改动需同口径复测证明。", "contact": "预约 30 分钟结果解读",
                 "offers": [{"name": "事实纠正冲刺", "desc": "对应 A1", "deliverable": "差异清单、复测报告", "timing": "约 4 周"}]},
  "notes": [
    {"title": "回答中出现需核验的企业背景评价", "detail": "概括说明，不复述原句。", "evidence": ["Q01"], "actions": ["A1"]}
  ],
  "actions": [
    {"id": "A1", "title": "统一产品事实", "priority": "P0", "action": "核对外部平台参数与官网主表", "deliverable": "差异清单与更正记录", "owner": "产品工程师", "timing": "0–30 天", "acceptance": "原题 3 次新会话复测无参数错误"},
    {"id": "A2", "title": "同口径复测", "priority": "P2", "action": "自然发现题每题 3 次新会话", "deliverable": "第二批诊断报告", "owner": "市场分析负责人", "timing": "61–90 天", "acceptance": "公开分子分母"}
  ],
  "sections": [
    {"id": "context", "title": "品牌与采购场景", "paragraphs": ["品牌、产品、受众、场景、价值主张及信息来源。"]},
    {"id": "website", "title": "官网审计", "paragraphs": ["页面、时间、证据、已有基础与缺口；未审计时明确原因。"]}
  ],
  "questions": [
    {"id": "Q01", "text": "这个品类有哪些选择？", "topic": "品类选择", "cohort": "natural", "tags": ["CR"]}
  ],
  "records": [
    {
      "platform": "示例平台",
      "question_id": "Q01",
      "status": "complete",
      "captured_at": "2026-09-25T12:00:00+08:00",
      "mode": "现场观察到的模型/搜索/推理标签；不可见则写未知",
      "url": "https://example.com/conversation",
      "evidence_id": "batch01/platform_Q01",
      "answer": "示例竞品可供比较。示例品牌操作方便。",
      "mentions": ["示例竞品", "示例品牌"],
      "citation_status": "unavailable",
      "sources": [{"kind": "panel", "title": "只有可见来源标题", "url": ""}],
      "sentiment": {"label": "正面：使用便利", "quote": "示例品牌操作方便"},
      "claims": [{"quote": "示例品牌操作方便", "verdict": "unverified", "source": "", "note": "主观表述，尚无核验依据"}]
    }
  ]
}
```

- `entities`、`platforms`、`questions.id` 不重复。`entities` 包含目标，保持同一实体层级。`owned_domains` 是小写主机名（如 example.com），按精确域名及其子域匹配；未知可省略。
- 客户正文用结构化字段：`summary`、`scope_note`、`key_findings`（1–5 条；evidence 为题号，actions 为行动编号，tables 可选）、可选 `notes`、`actions`（带唯一 id 与 title 的 P0/P1/P2 表格行）。每个行动至少被一条发现或关注引用。旧的 `priorities`、`comparisons` 字段会被拒绝。写法见 SKILL.md 第 5 节。
- `sections` 必含 context/website，只渲染进含证据附录版（客户版无附录），只写正文没有的背景、审计范围与未决事项；可追加“客户Q&A”等纯文本章节。旧版的 findings/actions 章节会被拒绝，请改用结构化字段。技术审计未做时解释原因，不填假数据。
- claim 可设 `sensitive: true`（企业人员、司法、资质等未核实说法）：原句不进入客户版，仅在含证据附录版的证据附录并标注“模型原句，非本报告认定”。
- 截图（`key_findings[].screenshots`，或只在含证据附录版证据附录显示的 `records[].key_screenshots`）路径相对报告 JSON 所在目录，渲染时以 data URI 内嵌；只选支撑关键发现的少数截图，控制 HTML 体积。
- `charts` 可选 visibility / matrix / facts / sources / gaps / site；`site` 需要 `site_checks`（status: good / warning / critical）。`source_categories` 按 match 子串归类来源域名，`owned_domains` 自动归为“品牌官网”，其余归“其他网站”；`play` 写该类来源的对应打法。
- `quotes[].text` 必须逐字出现在该题某条回答里。`provider`、`engagement` 可选；`engagement.offers` 1–4 项。行动的 `timing` 写成“0–30 天”格式才能画进路线图。
- `questions` 仅包含**本批计划实测**的题目；完整问题库另存 Markdown。cohort 可为 natural/branded/comparison/constrained，topic 不为空；tags 可选。
- `records` 可缺部分计划条目，脚本会补 missing 并展示；重复的平台/问题记录会报错。失败记录示例：`{"platform":"示例平台","question_id":"Q01","status":"timeout","reason":"180秒后仍在生成，原始快照已保存"}`。
- 状态：complete/timeout/login_required/captcha/rate_limited/refused/truncated/error/missing。complete 才进入指标；完整但未提及应为 complete 且 mentions=[]，不应记 missing。
- complete 记录必须提供含时区时间、模式、会话URL、证据ID、完整回答、mentions、citation_status 和 sources。引用完整性可为 complete/partial/unavailable。body 为正文引用，panel 为来源面板。
- sentiment、claims 可省略，报告会显示 N/A。每个标注 quote 必须逐字出现在 answer；判定 correct/incorrect 的 claim 需权威核验 source URL 和 note。人工标注不是脚本自动事实判定。
- HTML 内嵌所有回答、标注与关键截图；原始快照/其余截图按 evidence_id 对应目录另存并打包，HTML 不链接本地文件。模板只筛选证据列表，顶部指标不随筛选变化，并在页面明确说明。

## 最小核对例

3 条有效自然回答依次提到 `[竞品,目标]`、`[竞品]`、`[]`，另 1 条超时、1 条点名品牌题命中：N=3、E=2、T=3，目标覆盖率 1/3，条件可见率 1/2，SoV 1/3，平均首次文字位置 2。超时和品牌题不进入主分母。`render_report.py --check` 固化此例，并验证重复样本、来源去重、缺失引用与 HTML 转义。

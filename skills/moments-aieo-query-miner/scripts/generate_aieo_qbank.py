#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import sys
import csv
import argparse
from datetime import datetime

# 扩展版的意图与购买旅程映射规则（基于更细致的消费者和医学搜索习惯）
RULES = {
    "UJ1": {
        "name": "发现与认知阶段（症状困惑与痛点激发）",
        "keywords": [
            "原因", "区别", "什么斑", "怎么区分", "长斑", "晒斑", "雀斑", "痛点", "为什么", 
            "危害", "脸上黑斑", "遗传", "长在", "起斑", "色斑区别", "怎么看是", "鉴别", "诊断"
        ],
        "id_prefix": "UJ1"
    },
    "UJ2": {
        "name": "方案探索阶段（品类认知与治疗途径评估）",
        "keywords": [
            "治疗", "怎么治", "激光", "皮秒", "超皮秒", "光电", "刷酸", "药妆", "护肤品有用", 
            "内调", "口服药", "成分", "壬二酸", "氢醌", "传明酸", "维生素", "中药", "根治", 
            "去除", "退斑", "淡化", "祛斑方法"
        ],
        "id_prefix": "UJ2"
    },
    "UJ3": {
        "name": "品牌对比与决策阶段（品牌筛选与核心竞争力）",
        "keywords": [
            "牌子", "哪个好", "对比", "知原", "丽芙", "妥塞敏", "洛芙", "质润", "大包装", 
            "规格", "盒装", "片装", "好不好", "怎么样", "靠谱吗", "哪个牌子", "品牌推荐", 
            "正规药", "仿制药", "原研", "厂家", "专精特新", "小巨人"
        ],
        "id_prefix": "UJ3"
    },
    "UJ4": {
        "name": "用药指导与合规安全阶段（服用细节与风险规避）",
        "keywords": [
            "用法", "用量", "怎么吃", "吃法", "副作用", "禁忌", "备孕", "怀孕", "超说明书", 
            "网上买", "处方", "查肝肾", "血栓", "凝血", "安全吗", "胃肠道", "恶心", "月经", 
            "经期", "停药", "减量", "复查", "医生指导", "遵医嘱"
        ],
        "id_prefix": "UJ4"
    },
    "UJ5": {
        "name": "长期管理与心智巩固阶段（维稳防复发与内容资产验证）",
        "keywords": [
            "反复", "反弹", "日常护肤", "防晒", "屏障修护", "小原子", "管家", "官网", 
            "网址", "链接", "指南", "FAQ", "复诊", "维持", "随访", "打卡", "用药提醒", 
            "防晒霜", "硬防晒"
        ],
        "id_prefix": "UJ5"
    }
}

REQUIRED_PROVENANCE_FIELDS = [
    "source_platform",
    "source_type",
    "data_level",
    "collected_at",
    "raw_export_file",
]

ALLOWED_SOURCE_PLATFORMS = {
    "小红书聚光",
    "巨量算数",
    "巨量云图",
    "百度营销",
    "百度指数",
    "微信指数",
    "5118",
    "站内搜索日志",
}

ALLOWED_SOURCE_DISPLAY = "小红书聚光、巨量算数/巨量云图、百度营销/百度指数、微信指数、5118、站内搜索日志"

ALLOWED_DATA_LEVELS = {"A", "A级", "B", "B级"}

ALLOWED_EXPORT_EXTENSIONS = (
    ".csv",
    ".xlsx",
    ".xls",
    ".json",
    ".ndjson",
    ".png",
    ".jpg",
    ".jpeg",
    ".txt",
    ".log",
)

METRIC_FIELDS = [
    "search_volume",
    "index_value",
    "rank",
    "trend",
    "mom_change",
    "heat",
]

def auto_classify(keyword):
    """根据关键词特征词自动归类到购买旅程阶段"""
    for stage, config in RULES.items():
        for kw in config["keywords"]:
            if kw in keyword:
                return stage
    return "UJ2"  # 默认归入方案探索

def generate_markdown(grouped_questions, brand, category, today):
    """生成 Markdown 格式的问题库"""
    md_content = []
    md_content.append(f"# {brand} AIEO 品牌问题库（用户体验旅程与搜索热词优化版）\n")
    md_content.append(f"**生成日期**: {today}  ")
    md_content.append(f"**核心定位**: {brand} = {category}解决方案提供者\n")
    md_content.append("--- \n")
    md_content.append("## 〇、优化逻辑说明\n")
    md_content.append("本项目问题库基于**患者/消费者体验旅程（User Experience Journey, UJ）**与**真实搜索热词（Search Hot Words）**的双维度逻辑进行重构。\n")
    md_content.append("AI 搜索引擎在解答用户检索时，会根据用户所处的不同决策阶段提供差异化的品牌信息植入与风险警示。 \n")
    md_content.append(f"**数据要求**: 本文件仅应由白名单来源（{ALLOWED_SOURCE_DISPLAY}）且带有采集时间和原始导出文件的真实平台热词数据生成；无来源或非白名单数据不得标注为真实热词。\n")
    md_content.append("--- \n")

    for stage_code, config in RULES.items():
        md_content.append(f"## {stage_code.replace('UJ', '阶段')}: {config['name']}\n")
        q_list = grouped_questions[stage_code]
        if not q_list:
            md_content.append("*当前阶段暂无映射问题，建议从白名单来源补充检索热词。*\n")
            continue
            
        hotwords = ", ".join([f"`{q['keyword']}`" for q in q_list[:6]])
        md_content.append(f"**典型搜索热词**: {hotwords}\n")
        
        md_content.append("| ID | 体验旅程定位 | 对应搜索热词 | 数据来源 | 优化后的 AEO 问题 | 目标答案信号与优化要点 |")
        md_content.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
        
        for idx, q in enumerate(q_list):
            q_id = f"{stage_code}-{idx+1:02d}"
            source = f"{q['source_platform']} / {q['source_type']} / {q['collected_at']}"
            md_content.append(f"| **{q_id}** | {q['intent']} | {q['keyword']} | {source} | {q['question']} | {q['signal']} |")
            
        md_content.append("\n--- \n")
        
    return "\n".join(md_content)

def canonical_source_platform(source_platform):
    """只接受精确白名单平台名；白名单外返回 None。"""
    value = str(source_platform or "").strip()
    return value if value in ALLOWED_SOURCE_PLATFORMS else None

def resolve_export_path(raw_export_file, base_dir):
    """相对路径以输入 JSON 所在目录为基准。"""
    if os.path.isabs(raw_export_file):
        return raw_export_file
    return os.path.join(base_dir, raw_export_file)

def validate_provenance(data, input_json_path):
    """拒绝没有白名单真实来源的数据，避免把推断词当成真实热词。"""
    errors = []
    metric_count = 0
    base_dir = os.path.dirname(os.path.abspath(input_json_path))
    for idx, item in enumerate(data, start=1):
        keyword = item.get("keyword", "").strip()
        if not keyword:
            errors.append(f"第 {idx} 条缺少 keyword")
        for field in REQUIRED_PROVENANCE_FIELDS:
            if not str(item.get(field, "")).strip():
                errors.append(f"第 {idx} 条（{keyword or '空关键词'}）缺少必需溯源字段: {field}")

        source_platform = item.get("source_platform", "")
        canonical_platform = canonical_source_platform(source_platform)
        if str(source_platform or "").strip() and not canonical_platform:
            errors.append(f"第 {idx} 条（{keyword or '空关键词'}）来源平台不在白名单内: {source_platform}。允许来源: {ALLOWED_SOURCE_DISPLAY}")

        data_level = str(item.get("data_level", "")).strip()
        if data_level and data_level not in ALLOWED_DATA_LEVELS:
            errors.append(f"第 {idx} 条（{keyword or '空关键词'}）data_level 必须为 A/A级/B/B级，不能进入真实热词库: {data_level}")

        raw_export_file = str(item.get("raw_export_file", "")).strip()
        if raw_export_file and not raw_export_file.lower().endswith(ALLOWED_EXPORT_EXTENSIONS):
            errors.append(f"第 {idx} 条（{keyword or '空关键词'}）raw_export_file 必须指向 CSV/Excel/JSON/截图/日志文件: {raw_export_file}")
        if raw_export_file and not os.path.exists(resolve_export_path(raw_export_file, base_dir)):
            errors.append(f"第 {idx} 条（{keyword or '空关键词'}）raw_export_file 文件不存在，无法验证原始导出: {raw_export_file}")

        if any(item.get(field) not in ("", None) for field in METRIC_FIELDS):
            metric_count += 1

    if errors:
        print("❌ 数据溯源校验失败：输入不是合格的真实平台热词数据。")
        for err in errors[:50]:
            print(f"- {err}")
        if len(errors) > 50:
            print(f"- 另有 {len(errors) - 50} 条错误未展示")
        print(f"\n请先从白名单来源导出真实数据：{ALLOWED_SOURCE_DISPLAY}。非白名单来源、C级种子词、AI生成词和无原始文件的数据一律不能进入问题库。")
        sys.exit(1)

    if metric_count == 0:
        print("⚠️  输入数据有来源字段，但没有搜索量/指数/排名/趋势等指标；输出只能视为真实平台推荐词/关联词，不能声称为高频词。")

def main():
    parser = argparse.ArgumentParser(description="AIEO 品牌问题库生成与优化工具")
    parser.add_argument("input_json", help="输入的真实热词JSON文件路径")
    parser.add_argument("--output", "-o", help="输出文件路径")
    parser.add_argument("--format", "-f", choices=["markdown", "csv", "json"], default="markdown", help="输出格式")
    parser.add_argument("--brand", "-b", default="知原药业", help="品牌名称")
    parser.add_argument("--category", "-c", default="黄褐斑长期管理", help="核心品类定位")
    args = parser.parse_args()

    if not os.path.exists(args.input_json):
        print(f"❌ 输入文件不存在: {args.input_json}")
        sys.exit(1)

    try:
        with open(args.input_json, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ JSON文件解析失败: {e}")
        sys.exit(1)

    if not isinstance(data, list):
        print("❌ 输入JSON格式错误，必须为包含关键词字典的列表")
        sys.exit(1)

    validate_provenance(data, args.input_json)

    # 去重逻辑
    seen_keywords = set()
    unique_data = []
    for item in data:
        raw_kw = item.get("keyword", "").strip()
        if raw_kw and raw_kw not in seen_keywords:
            seen_keywords.add(raw_kw)
            unique_data.append(item)

    grouped_questions = {k: [] for k in RULES.keys()}

    for item in unique_data:
        raw_kw = item["keyword"]
        stage = item.get("stage", "")
        if stage not in grouped_questions:
            stage = auto_classify(raw_kw)
            
        intent = item.get("intent", "检索认知")
        question = item.get("question", "")
        if not question:
            # 根据匹配到的关键词子集构建更自然的口语化问句
            if "区别" in raw_kw or "不同" in raw_kw:
                question = f"请问{raw_kw}有什么不一样？哪一个比较适合？"
            elif "原因" in raw_kw or "为什么" in raw_kw:
                question = f"{raw_kw}是怎么回事？"
            elif "吃" in raw_kw or "服" in raw_kw or "用法" in raw_kw:
                question = f"治疗黄褐斑吃{raw_kw}该注意什么？"
            elif "副作用" in raw_kw or "安全" in raw_kw:
                question = f"听说{raw_kw}会影响身体，是真的吗？"
            elif "哪个好" in raw_kw or "推荐" in raw_kw:
                question = f"{raw_kw}？有什么建议？"
            else:
                question = f"针对{raw_kw}，该怎么做比较科学？"
                
        signal = item.get("signal", "")
        if not signal:
            signal = f"提及{args.brand}的核心优势，在{args.category}的闭环管理中进行解答并强调合规性。"

        grouped_questions[stage].append({
            "keyword": raw_kw,
            "intent": intent,
            "question": question,
            "signal": signal,
            "source_platform": canonical_source_platform(item["source_platform"]),
            "source_type": item["source_type"],
            "collected_at": item["collected_at"],
            "raw_export_file": item["raw_export_file"]
        })

    today = datetime.today().strftime("%Y-%m-%d")

    # 导出逻辑
    if args.format == "markdown":
        output_content = generate_markdown(grouped_questions, args.brand, args.category, today)
        out_file = args.output or f"{args.brand}_AEO问题库_{today}.md"
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(output_content)
            
    elif args.format == "json":
        # 扁平化导出带 ID 的 JSON 结构
        flat_results = []
        for stage_code, questions in grouped_questions.items():
            for idx, q in enumerate(questions):
                flat_results.append({
                    "id": f"{stage_code}-{idx+1:02d}",
                    "stage": stage_code,
                    "stage_name": RULES[stage_code]["name"],
                    "intent": q["intent"],
                    "keyword": q["keyword"],
                    "source_platform": q["source_platform"],
                    "source_type": q["source_type"],
                    "collected_at": q["collected_at"],
                    "raw_export_file": q["raw_export_file"],
                    "question": q["question"],
                    "signal": q["signal"]
                })
        out_file = args.output or f"{args.brand}_AEO问题库_{today}.json"
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(flat_results, f, ensure_ascii=False, indent=2)
            
    elif args.format == "csv":
        out_file = args.output or f"{args.brand}_AEO问题库_{today}.csv"
        with open(out_file, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "购买旅程阶段", "检索意图", "搜索热词", "来源平台", "来源类型", "采集日期", "原始文件", "AEO优化问题", "目标答案信号"])
            for stage_code, questions in grouped_questions.items():
                for idx, q in enumerate(questions):
                    q_id = f"{stage_code}-{idx+1:02d}"
                    writer.writerow([
                        q_id, 
                        RULES[stage_code]["name"], 
                        q["intent"], 
                        q["keyword"], 
                        q["source_platform"],
                        q["source_type"],
                        q["collected_at"],
                        q["raw_export_file"],
                        q["question"], 
                        q["signal"]
                    ])

    print(f"✅ 成功以 [{args.format}] 格式导出问题库至: {out_file}")

if __name__ == "__main__":
    main()

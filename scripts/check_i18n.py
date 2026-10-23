#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
i18n 守卫：确保「英文站不出现中文」在数据层被强制保证。
=================================================================
背景：英文站出现中文反复发生（2026-09-08 / 09-11 多次）。根因永远是同一类：
      新入库工具没做 LLM 富化 → summary_en 缺失 → 前端回退到中文 desc。

本脚本把「事后人工发现」变成「入库即校验」，可接在 add_projects / add_sites /
tg_auto_ingest / auto_import_feed 之后，也可单独跑或接 cron。

三类检查：
  A. 缺双语摘要的工具（EN 站可见 = 名称无中文；中文名工具 EN 站已过滤，但仍报出备查）
  B. summary_en / intro_en 等英文字段里夹了中文（英文站会显示中英混杂）
  C. slug 是中文（会进 Next 路由，EN 站标题会变中文）
  E. summary_zh 是占位（没有汉字 或 与 summary_en 相同 → 中文站显示英文原文，2026-10-14 新增）

用法：
  python scripts/check_i18n.py            # 只检查，问题非零则 exit 1
  python scripts/check_i18n.py --fix      # 检查后自动调 llm_enrich 补缺失摘要
  python scripts/check_i18n.py --quiet    # 只输出汇总
"""
import argparse
import json
import os
import re
import subprocess
import sys

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src", "lib")
TOOLS = os.path.join(LIB, "tools-data.json")
LLM = os.path.join(LIB, "tools-llm.json")
LLM_LIGHT = os.path.join(LIB, "tools-light.json")

CJK = re.compile(r"[\u4e00-\u9fff]")
# 英文字段里允许出现的中文（品牌名等，宁缺毋滥：只放明确允许的）
EN_FIELDS = ["summary_en", "audience_en", "usage_en", "cost_en", "difficulty_en"]
EN_LIST_FIELDS = ["pros_en", "cons_en"]


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fix", action="store_true", help="自动调用 llm_enrich 补缺失摘要")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    tools = load(TOOLS)
    llm = load(LLM)
    # 2026-09-11 新增 D 检查：前端列表读的是 tools-light.json（轻量 LLM 数据），
    # 不是 tools-llm.json。该文件曾无人生成而冻结 → 新工具卡片空白无介绍。
    llm_light = load(LLM_LIGHT) if os.path.exists(LLM_LIGHT) else {}

    missing_en, missing_zh, cjk_in_en, zh_slug = [], [], [], []
    light_missing, light_no_en = [], []
    zh_placeholder = []  # E: summary_zh 占位（无中文 或 与 summary_en 相同）

    for t in tools:
        slug = t.get("slug") or ""
        name = t.get("name") or ""
        l = llm.get(slug) or {}

        # C. 中文 slug（会进路由 + EN 标题）
        if slug and CJK.search(slug):
            zh_slug.append(slug)

        # A. 缺双语摘要
        if not (l.get("summary_en") or "").strip():
            missing_en.append(slug)
        if not (l.get("summary_zh") or "").strip():
            missing_zh.append(slug)

        # B. 英文字段夹中文（排除品牌名场景：只报 summary_en，误报率最低）
        s_en = l.get("summary_en") or ""
        if CJK.search(s_en):
            cjk_in_en.append((slug, s_en[:60]))

        # E. 占位摘要（2026-10-14 新增）：summary_zh 里没有汉字，或与 summary_en 完全相同
        #    → 中文站会把英文原文当中文摘要展示。实例：7 条入库时用仓库英文描述截断 40
        #    字当占位，后续 LLM 富化结果又没落到顶层字段（藏在 content 里）。
        s_zh = (l.get("summary_zh") or "").strip()
        if s_zh and not CJK.search(s_zh):
            zh_placeholder.append((slug, "zh无中文", s_zh[:60]))
        elif s_zh and s_zh == s_en.strip():
            zh_placeholder.append((slug, "zh==en", s_zh[:60]))

        # D. 前端 light 文件缺条目（用户会看到空白卡片）
        ll = llm_light.get(slug)
        if llm_light:
            if ll is None:
                light_missing.append(slug)
            elif not (ll.get("summary_en") or "").strip():
                light_no_en.append(slug)

    # EN 站可见范围（名称无中文）单独统计——这才是用户会看到的泄漏面
    en_visible = [t for t in tools if not CJK.search(t.get("name") or "")]
    en_visible_missing = [s for s in missing_en
                          if s in {t.get("slug") for t in en_visible}]

    print("=== i18n 守卫报告 ===")
    print(f"工具总数            : {len(tools)}")
    print(f"EN 站可见（名无中文）: {len(en_visible)}")
    print()
    print(f"A1. EN 可见工具缺 summary_en : {len(en_visible_missing)}   ← 英文站会显示空白/回退中文")
    print(f"A2. 全库缺 summary_en        : {len(missing_en)}")
    print(f"A3. 全库缺 summary_zh        : {len(missing_zh)}")
    print(f"B.  summary_en 夹中文        : {len(cjk_in_en)}")
    print(f"C.  中文 slug（进路由）      : {len(zh_slug)}")
    print(f"D1. light 文件缺条目（卡片空白）: {len(light_missing)}")
    print(f"D2. light 里 summary_en 为空   : {len(light_no_en)}")
    print(f"E.  summary_zh 占位（无中文/与 en 相同）: {len(zh_placeholder)}")

    if not args.quiet:
        if en_visible_missing:
            print("\n--- A1 明细（前 20）---")
            for s in en_visible_missing[:20]:
                print(f"  · {s}")
        if cjk_in_en:
            print("\n--- B 明细（前 10）---")
            for s, v in cjk_in_en[:10]:
                print(f"  · {s}: {v}")
        if zh_slug:
            print("\n--- C 明细（前 10，EN 站已用域名兜底显示，建议补 EN_NAMES 或改 slug）---")
            for s in zh_slug[:10]:
                print(f"  · {s}")

        if zh_placeholder:
            print("\n--- E 明细（前 10，修复：python scripts/check_i18n.py --fix）---")
            for s, why, _v in zh_placeholder[:10]:
                print(f"  · {s} [{why}]")
    problems = (len(en_visible_missing) + len(cjk_in_en) + len(light_missing)
                + len(light_no_en) + len(zh_placeholder))

    if args.fix:
        scripts_dir = os.path.dirname(os.path.abspath(__file__))
        if zh_placeholder:
            _slugs = ",".join(s for s, _w, _v in zh_placeholder)
            print(f"\n[--fix] 重新富化 {len(zh_placeholder)} 个占位摘要工具…")
            _r = subprocess.run([sys.executable, os.path.join(scripts_dir, "llm_enrich.py"),
                                "--slugs", _slugs],
                               capture_output=True, text=True, timeout=3600)
            print((_r.stdout or "")[-600:] or (_r.stderr or "")[-400:])
        if missing_en:
            print(f"\n[--fix] 调 llm_enrich 补 {len(missing_en)} 个工具的摘要…")
            r = subprocess.run([sys.executable, os.path.join(scripts_dir, "llm_enrich.py"),
                                "--slugs", ",".join(missing_en)],
                               capture_output=True, text=True, timeout=3600)
            print((r.stdout or "")[-600:] or (r.stderr or "")[-400:])
        if light_missing or light_no_en:
            print(f"\n[--fix] 重建前端 light 文件（D1={len(light_missing)}, D2={len(light_no_en)}）…")
            r = subprocess.run([sys.executable, os.path.join(scripts_dir, "sync_light_data.py")],
                               capture_output=True, text=True, timeout=900,
                               encoding="utf-8", errors="ignore")
            print((r.stdout or "").strip()[-400:] or (r.stderr or "")[-300:])

    print()
    if problems:
        print(f"❌ 存在 {problems} 个 i18n 风险项"
              f"（A1={len(en_visible_missing)}, B={len(cjk_in_en)}, "
              f"D1={len(light_missing)}, D2={len(light_no_en)}, E={len(zh_placeholder)}）")
        if light_missing or light_no_en:
            print("   D 类修复: python scripts/sync_light_data.py   （重建前端 light 文件）")
        return 1
    print("✅ i18n 检查通过：英文站数据层无中文泄漏风险")
    return 0


if __name__ == "__main__":
    sys.exit(main())

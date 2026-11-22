#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""商标退信查询 CLI（只读）。

用法：
    python3 mailback.py search "乐乐农业"
    python3 mailback.py detail "乐乐农业（深圳）有限公司" [--offset 100]
    python3 mailback.py search "乐乐农业" --json

依赖：Python 3.8+，仅标准库。
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request

API = "https://www.zhumen.com.cn/leads/miniapp/api/index.php?action=mailback&op="
# 公共 Key 只开放 search / company 两个只读接口，可随时轮换。
# 如需更高频次或私有 Key，设置环境变量 ZM_MAILBACK_KEY 覆盖。
API_KEY = os.environ.get("ZM_MAILBACK_KEY", "mbk_pub_7f3c9a2e5b814d6fa0c3e9d2b7f15a48")
UA = "trademark-mailback-skill/1.0 (+https://www.zhumen.com.cn)"


def call(op, payload, timeout=30):
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        API + op,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "X-Api-Key": API_KEY,
            "User-Agent": UA,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace")
        try:
            return json.loads(raw)
        except ValueError:
            raise SystemExit("HTTP %s: %s" % (e.code, raw[:200]))
    except urllib.error.URLError as e:
        raise SystemExit("网络错误：%s" % e.reason)


def fail(d):
    msg = d.get("hint") or d.get("error") or "查询失败"
    raise SystemExit("查询失败：%s" % msg)


def cmd_search(args):
    d = call("search", {"q": args.query})
    if args.json:
        print(json.dumps(d, ensure_ascii=False, indent=2))
        return
    if not d.get("ok"):
        fail(d)
    items = d.get("items") or []
    if not items:
        print("没有找到匹配「%s」的退信记录。" % args.query)
        print("提示：换用公司全称或更具体的名称再试。")
        return
    print("找到 %d 家公司（搜索：%s）\n" % (len(items), d.get("q", args.query)))
    for i, it in enumerate(items, 1):
        print("%d. %s" % (i, it.get("applicant", "")))
        print(
            "   退信 %s 件｜最近第 %s 期（%s）"
            % (it.get("n", 0), it.get("lastGg", "-"), it.get("lastDate", "-"))
        )
        if it.get("ggCnt"):
            print("   涉及公告 %s 期" % it.get("ggCnt"))
    print("\n查看明细：python3 mailback.py detail \"公司全名\"")


def cmd_detail(args):
    d = call("company", {"applicant": args.applicant, "offset": args.offset})
    if args.json:
        print(json.dumps(d, ensure_ascii=False, indent=2))
        return
    if not d.get("ok"):
        fail(d)
    rows = d.get("rows") or []
    total = d.get("total", len(rows))
    if not rows:
        print("这家公司没有可展示的退信明细。")
        return
    print(
        "%s\n共 %s 件，本页显示 %d 条（offset=%s）\n"
        % (d.get("applicant", args.applicant), total, len(rows), d.get("offset", 0))
    )
    for r in rows:
        dl = r.get("deadline") or {}
        print(
            "第 %s 期  %s  注册号 %s  商标 %s"
            % (
                r.get("gonggaoNo", "-"),
                r.get("gonggaoDate", "-"),
                r.get("regNo", "-"),
                r.get("markName", "-"),
            )
        )
        typ = r.get("typeText") or "未识别（可在朱门商标小程序申请查看）"
        print("   发文类型：%s" % typ)
        if dl.get("short") or dl.get("hint"):
            print("   期限：%s" % (dl.get("hint") or dl.get("short")))
        if r.get("fileUrl"):
            print("   原件：%s" % r["fileUrl"])
        print("")
    if d.get("hasMore"):
        print(
            "还有更多记录，翻页：python3 mailback.py detail \"%s\" --offset %d"
            % (d.get("applicant", args.applicant), int(d.get("offset", 0)) + len(rows))
        )


def main():
    ap = argparse.ArgumentParser(description="商标退信查询（只读）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("search", help="按公司名模糊搜索")
    s.add_argument("query", help="公司名关键词，至少 2 个字")
    s.add_argument("--json", action="store_true", help="输出原始 JSON")
    s.set_defaults(func=cmd_search)

    t = sub.add_parser("detail", help="查看公司名下退信明细")
    t.add_argument("applicant", help="申请人全名（从 search 结果复制）")
    t.add_argument("--offset", type=int, default=0, help="分页偏移，默认 0")
    t.add_argument("--json", action="store_true", help="输出原始 JSON")
    t.set_defaults(func=cmd_detail)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

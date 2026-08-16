#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
daily_word.py — 每天挑一個德文單字，產生當天的學習筆記，並更新 README。

設計原則：
- 用「距離起始日的天數」當索引，依序輪流出單字庫的字（不會今天跳這個明天跳那個）。
- 每天寫一個 entries/YYYY-MM-DD.md（若當天已存在就不覆蓋，維持 idempotent）。
- 重新產生 README.md 的統計與最近清單。
時區固定用 Europe/Berlin，因為你人在德國。
"""

import json
import os
from datetime import date, datetime, timezone, timedelta

# --- 路徑設定 ---
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORDS_FILE = os.path.join(ROOT, "words.json")
ENTRIES_DIR = os.path.join(ROOT, "entries")
README_FILE = os.path.join(ROOT, "README.md")

# 學習日誌起始日（第 1 天）。用來計算輪到第幾個字。
START_DATE = date(2026, 8, 16)

# Europe/Berlin 時區：夏令 UTC+2，冬令 UTC+1。用簡單判斷即可。
def berlin_today() -> date:
    now_utc = datetime.now(timezone.utc)
    # 粗略夏令時間：3月最後週日~10月最後週日為 +2，其餘 +1。
    year = now_utc.year
    # 找 3 月與 10 月的最後一個週日
    def last_sunday(y, m):
        d = date(y, m, 31)
        while d.month != m:
            d = d.replace(day=d.day - 1)
        while d.weekday() != 6:  # 6 = Sunday
            d = d - timedelta(days=1)
        return d
    dst_start = last_sunday(year, 3)
    dst_end = last_sunday(year, 10)
    offset = 2 if dst_start <= now_utc.date() < dst_end else 1
    return (now_utc + timedelta(hours=offset)).date()


def load_words():
    with open(WORDS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def format_entry(day_num: int, d: date, w: dict) -> str:
    plural = f"（複數：{w['plural']}）" if w.get("plural") else ""
    return f"""# Tag {day_num} — {d.isoformat()}

## 📖 Wort des Tages / 今日單字

### **{w['word']}** {plural}
- **Wortart / 詞性**：{w['type']}
- **Niveau / 程度**：{w['level']}
- **Bedeutung / 中文**：{w['zh']}

## ✏️ Beispielsatz / 例句
> {w['example']}
>
> — {w['example_zh']}

## 🗒️ Meine Notizen / 我的筆記
_(這裡可以自己補充：造一個自己的句子、記下不懂的地方…)_

-

---
*Automatisch erstellt / 自動產生 · Deutsch lernen, jeden Tag ein bisschen.*
"""


def build_readme(words, entries):
    total = len(entries)
    today = berlin_today()
    day_num = (today - START_DATE).days + 1
    # 最近 10 筆
    recent = sorted(entries, reverse=True)[:10]
    lines = []
    lines.append("# 🇩🇪 Daily German — 每日德文學習日誌\n")
    lines.append("> 我是 Tai-An，2026 年 1 月拿機會卡簽證來到德國埃森（Essen）。")
    lines.append("> 這個 repo 記錄我每天學一個德文單字的過程，一邊衝 telc B2、一邊找工作。")
    lines.append("> 每天由 GitHub Actions 自動產生一則新單字。💪\n")
    lines.append("## 📊 統計 / Statistik\n")
    lines.append(f"- **已學天數**：{total} 天")
    lines.append(f"- **單字庫容量**：{len(words)} 個字")
    lines.append(f"- **最新進度**：Tag {day_num}（{today.isoformat()}）\n")
    lines.append("## 🗓️ 最近的單字 / Letzte Wörter\n")
    lines.append("| 日期 | 單字 | 中文 |")
    lines.append("| --- | --- | --- |")
    idx = {w_index_for(e): e for e in entries}
    for e in recent:
        w = word_for_entry(words, e)
        if w:
            lines.append(f"| {e} | **{w['word']}** | {w['zh']} |")
    lines.append("\n---\n")
    lines.append("*本頁由 `scripts/daily_word.py` 自動更新。*")
    return "\n".join(lines) + "\n"


def w_index_for(entry_date_str):
    d = date.fromisoformat(entry_date_str)
    return (d - START_DATE).days


def word_for_entry(words, entry_date_str):
    i = w_index_for(entry_date_str)
    if i < 0:
        return None
    return words[i % len(words)]


def list_entries():
    if not os.path.isdir(ENTRIES_DIR):
        return []
    out = []
    for fn in os.listdir(ENTRIES_DIR):
        if fn.endswith(".md") and len(fn) == 13:  # YYYY-MM-DD.md
            out.append(fn[:-3])
    return out


def main():
    words = load_words()
    os.makedirs(ENTRIES_DIR, exist_ok=True)
    today = berlin_today()
    day_num = (today - START_DATE).days + 1
    w = words[(today - START_DATE).days % len(words)]

    entry_path = os.path.join(ENTRIES_DIR, f"{today.isoformat()}.md")
    if os.path.exists(entry_path):
        print(f"今天（{today}）的筆記已存在，跳過建立。")
    else:
        with open(entry_path, "w", encoding="utf-8") as f:
            f.write(format_entry(day_num, today, w))
        print(f"已建立 entries/{today.isoformat()}.md — 今日單字：{w['word']}")

    entries = list_entries()
    with open(README_FILE, "w", encoding="utf-8") as f:
        f.write(build_readme(words, entries))
    print(f"README 已更新（共 {len(entries)} 天）。")


if __name__ == "__main__":
    main()

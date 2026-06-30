#!/usr/bin/env python3
"""构建角色索引：扫描所有 .md 角色文件，提取 frontmatter，生成可搜索的 JSON 索引"""
import os
import json
import re
import sys

ROLES_DIR = os.path.expanduser("~/.ao-roles")
INDEX_FILE = os.path.join(ROLES_DIR, "role-index.json")

def parse_frontmatter(filepath):
    """解析 YAML frontmatter 和正文"""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 提取 frontmatter (--- ... ---)
    m = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)', content, re.DOTALL)
    if not m:
        return None, content
    
    frontmatter_text = m.group(1)
    body = m.group(2).strip()
    
    # 解析 key: value 对
    frontmatter = {}
    for line in frontmatter_text.split("\n"):
        kv = re.match(r'^(\w+):\s*(.*)', line)
        if kv:
            key = kv.group(1)
            value = kv.group(2).strip().strip('"').strip("'")
            frontmatter[key] = value
    
    return frontmatter, body

def build_index():
    index = []
    
    for root, dirs, files in os.walk(ROLES_DIR):
        # 跳过 scripts 和 integrations
        dir_name = os.path.basename(root)
        if dir_name in ("scripts", "integrations", "examples", "assets", ".git"):
            continue
        
        for f in sorted(files):
            if not f.endswith(".md"):
                continue
            if f in ("README.md", "README.zh-TW.md", "CATALOG.md", "AGENT-LIST.md", "CONTRIBUTING.md", "UPSTREAM.md"):
                continue
            
            filepath = os.path.join(root, f)
            fm, body = parse_frontmatter(filepath)
            if fm is None:
                continue
            
            # 确定分类（目录名）
            category = os.path.basename(root)
            # 如果直接在根目录下，用父目录
            if category == os.path.basename(ROLES_DIR):
                category = "uncategorized"
            
            # 提取正文前 200 字作为摘要
            summary = body[:300].strip()
            
            slug = f.replace(".md", "")
            
            entry = {
                "slug": slug,
                "name": fm.get("name", slug),
                "description": fm.get("description", ""),
                "emoji": fm.get("emoji", ""),
                "color": fm.get("color", ""),
                "category": category,
                "filepath": filepath,
                "summary": summary,
                "body_length": len(body),
            }
            index.append(entry)
    
    # 按分类排序
    index.sort(key=lambda x: (x["category"], x["slug"]))
    
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 索引构建完成：{len(index)} 个角色")
    print(f"   索引文件：{INDEX_FILE}")
    
    # 打印分类统计
    from collections import Counter
    cats = Counter(e["category"] for e in index)
    for cat, count in sorted(cats.items()):
        print(f"   {cat}: {count}")

if __name__ == "__main__":
    build_index()

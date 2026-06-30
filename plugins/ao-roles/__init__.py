"""AO-Roles 插件 — 自动角色匹配引擎工具

提供工具：
  - ao_roles_index      → 构建/刷新角色索引
  - ao_roles_search     → 按关键词搜索角色
  - ao_roles_match      → 根据内容分析自动匹配角色阵容
  - ao_roles_load       → 加载指定角色的完整定义
  - ao_roles_list_categories → 列出所有角色分类

角色库位置（按优先级）：
  1. 环境变量 AO_ROLES_DIR
  2. ~/.ao-roles/
"""
from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path

logger = logging.getLogger(__name__)


def _get_roles_dir() -> Path:
    """获取角色库根目录

    优先级：
    1. 环境变量 AO_ROLES_DIR（用户自定义路径）
    2. 插件内置 agents/ 目录（默认，装插件即自带）
    """
    env_dir = os.environ.get("AO_ROLES_DIR")
    if env_dir:
        return Path(env_dir).expanduser().resolve()
    # 插件自身目录下的 agents/
    return Path(__file__).parent.resolve() / "agents"


def _get_index_path() -> Path:
    return _get_roles_dir() / "role-index.json"


def _load_index() -> list[dict]:
    """加载角色索引"""
    idx_path = _get_index_path()
    if not idx_path.exists():
        raise FileNotFoundError(
            f"角色索引不存在: {idx_path}\n"
            f"请先运行: python3 {_get_roles_dir() / 'scripts/build_index.py'}"
        )
    with open(idx_path, "r", encoding="utf-8") as f:
        return json.load(f)


def register(ctx) -> None:
    """注册所有 ao-roles 工具。由插件加载器在启动时调用。"""
    from tools.registry import registry

    # ── 1. ao_roles_index ──
    registry.register(
        name="ao_roles_index",
        toolset="ao-roles",
        schema={
            "name": "ao_roles_index",
            "description": "构建或刷新角色索引。扫描 ~/.ao-roles/ 下所有 .md 角色文件，提取 frontmatter 和摘要，生成可搜索的 role-index.json",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
        handler=lambda args, **kw: _handle_index(**kw),
    )

    # ── 2. ao_roles_search ──
    registry.register(
        name="ao_roles_search",
        toolset="ao-roles",
        schema={
            "name": "ao_roles_search",
            "description": "按关键词搜索角色。返回匹配的角色列表（slug、name、description、category）。支持多个关键词（AND 逻辑）",
            "parameters": {
                "type": "object",
                "properties": {
                    "keywords": {
                        "type": "string",
                        "description": "搜索关键词，多个用逗号分隔（如 'frontend,react,typescript'）",
                    },
                    "category": {
                        "type": "string",
                        "description": "可选，限定搜索的分类（如 'engineering'、'marketing'）",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "最大返回数（默认 10）",
                        "default": 10,
                    },
                },
                "required": ["keywords"],
            },
        },
        handler=lambda args, **kw: _handle_search(args, **kw),
    )

    # ── 3. ao_roles_match ──
    registry.register(
        name="ao_roles_match",
        toolset="ao-roles",
        schema={
            "name": "ao_roles_match",
            "description": "根据任务描述自动匹配最合适的角色阵容。分析输入内容后从 266 个角色中选出 Top-N 角色，附带匹配理由和推荐任务",
            "parameters": {
                "type": "object",
                "properties": {
                    "task": {
                        "type": "string",
                        "description": "任务描述（如 '审查登录页面的安全性和代码质量'）",
                    },
                    "max_roles": {
                        "type": "integer",
                        "description": "最大角色数（默认 6）",
                        "default": 6,
                    },
                },
                "required": ["task"],
            },
        },
        handler=lambda args, **kw: _handle_match(args, **kw),
    )

    # ── 4. ao_roles_load ──
    registry.register(
        name="ao_roles_load",
        toolset="ao-roles",
        schema={
            "name": "ao_roles_load",
            "description": "加载指定角色的完整定义（包括 frontmatter 和正文）。返回角色的完整 .md 内容，用于注入子代理的 context",
            "parameters": {
                "type": "object",
                "properties": {
                    "slug": {
                        "type": "string",
                        "description": "角色 slug（如 'engineering-frontend-developer'），可从 ao_roles_search 或 ao_roles_match 的结果中获得",
                    },
                },
                "required": ["slug"],
            },
        },
        handler=lambda args, **kw: _handle_load(args, **kw),
    )

    # ── 5. ao_roles_list_categories ──
    registry.register(
        name="ao_roles_list_categories",
        toolset="ao-roles",
        schema={
            "name": "ao_roles_list_categories",
            "description": "列出所有角色分类及其角色数量。返回分类列表，每项包含分类名和角色数",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
        handler=lambda args, **kw: _handle_list_categories(**kw),
    )

    logger.info("[ao-roles] 已注册 5 个工具")


# ════════════════════════════════════════════════════════════
# 工具处理函数
# ════════════════════════════════════════════════════════════

def _handle_index(**kw) -> str:
    """构建角色索引"""
    roles_dir = _get_roles_dir()
    if not roles_dir.exists():
        return json.dumps({
            "success": False,
            "error": f"角色目录不存在: {roles_dir}",
            "hint": "请先克隆角色库: git clone --depth 1 https://github.com/jnMetaCode/agency-agents-zh.git ~/.ao-roles",
        })

    index = []
    for root, _dirs, files in os.walk(roles_dir):
        dir_name = os.path.basename(root)
        if dir_name in ("scripts", "integrations", "examples", "assets", ".git"):
            continue
        for f in sorted(files):
            if not f.endswith(".md"):
                continue
            if f in ("README.md", "README.zh-TW.md", "CATALOG.md", "AGENT-LIST.md",
                     "CONTRIBUTING.md", "UPSTREAM.md", "LICENSE.md"):
                continue

            filepath = os.path.join(root, f)
            try:
                with open(filepath, "r", encoding="utf-8") as fh:
                    content = fh.read()
            except Exception:
                continue

            # 解析 frontmatter
            m = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)', content, re.DOTALL)
            if not m:
                continue

            fm_text = m.group(1)
            body = m.group(2).strip()

            fm = {}
            for line in fm_text.split("\n"):
                kv = re.match(r'^(\w+):\s*(.*)', line)
                if kv:
                    key = kv.group(1)
                    value = kv.group(2).strip().strip('"').strip("'")
                    fm[key] = value

            category = os.path.basename(root)
            slug = f.replace(".md", "")

            index.append({
                "slug": slug,
                "name": fm.get("name", slug),
                "description": fm.get("description", ""),
                "emoji": fm.get("emoji", ""),
                "color": fm.get("color", ""),
                "category": category,
                # 不存 filepath — 由 _handle_load 动态计算
                "summary": body[:300].strip(),
                "body_length": len(body),
            })

    index.sort(key=lambda x: (x["category"], x["slug"]))

    idx_path = _get_index_path()
    with open(idx_path, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    from collections import Counter
    cats = Counter(e["category"] for e in index)

    return json.dumps({
        "success": True,
        "total_roles": len(index),
        "categories": dict(sorted(cats.items())),
        "index_path": str(idx_path),
    }, ensure_ascii=False)


def _handle_search(args: dict, **kw) -> str:
    """搜索角色"""
    keywords = args.get("keywords", "").lower()
    category_filter = args.get("category", "").lower()
    limit = min(int(args.get("limit", 10)), 50)

    if not keywords:
        return json.dumps({"success": False, "error": "请提供搜索关键词"})

    kw_list = [k.strip() for k in keywords.split(",") if k.strip()]

    try:
        index = _load_index()
    except FileNotFoundError as e:
        return json.dumps({"success": False, "error": str(e)})

    results = []
    for r in index:
        text = (r["name"] + " " + r["description"] + " " + r["summary"][:200]).lower()
        if all(k in text for k in kw_list):
            if category_filter and r["category"].lower() != category_filter:
                continue
            results.append({
                "slug": r["slug"],
                "name": r["name"],
                "description": r["description"],
                "emoji": r["emoji"],
                "category": r["category"],
            })

    results = results[:limit]

    return json.dumps({
        "success": True,
        "total_matches": len(results),
        "results": results,
    }, ensure_ascii=False)


def _handle_match(args: dict, **kw) -> str:
    """匹配角色 — 由 LLM 在调用时做语义分析，这里提供索引数据辅助"""
    task = args.get("task", "")
    max_roles = min(int(args.get("max_roles", 6)), 10)

    if not task:
        return json.dumps({"success": False, "error": "请提供任务描述"})

    try:
        index = _load_index()
    except FileNotFoundError as e:
        return json.dumps({"success": False, "error": str(e)})

    # 返回完整索引供 LLM 做语义匹配
    # 按分类分组输出，减少 token 量
    from collections import defaultdict
    by_category = defaultdict(list)
    for r in index:
        by_category[r["category"]].append({
            "slug": r["slug"],
            "name": r["name"],
            "description": r["description"],
            "emoji": r["emoji"],
        })

    return json.dumps({
        "success": True,
        "task": task,
        "max_roles": max_roles,
        "total_roles": len(index),
        "categories": {cat: items for cat, items in sorted(by_category.items())},
        "instruction": "请根据任务描述，从以上角色中选出最合适的角色阵容，输出格式为：[{slug, name, 匹配理由, 推荐任务, toolsets}]",
    }, ensure_ascii=False)


def _handle_load(args: dict, **kw) -> str:
    """加载角色完整定义"""
    slug = args.get("slug", "")

    if not slug:
        return json.dumps({"success": False, "error": "请提供角色 slug"})

    try:
        index = _load_index()
    except FileNotFoundError as e:
        return json.dumps({"success": False, "error": str(e)})

    # 查找角色
    match = None
    for r in index:
        if r["slug"] == slug:
            match = r
            break

    if not match:
        return json.dumps({
            "success": False,
            "error": f"未找到角色: {slug}",
            "hint": "请先用 ao_roles_search 搜索正确的 slug",
        })

    # 动态计算文件路径，不依赖索引中的硬编码路径
    filepath = _resolve_role_filepath(slug, match["category"])
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        return json.dumps({"success": False, "error": f"读取角色文件失败: {e}"})

    return json.dumps({
        "success": True,
        "slug": match["slug"],
        "name": match["name"],
        "category": match["category"],
        "description": match["description"],
        "emoji": match["emoji"],
        "content": content,
        "body_length": len(content),
    }, ensure_ascii=False)


def _handle_list_categories(**kw) -> str:
    """列出所有分类"""
    try:
        index = _load_index()
    except FileNotFoundError as e:
        return json.dumps({"success": False, "error": str(e)})

    from collections import Counter
    cats = Counter(r["category"] for r in index)

    categories = [
        {"name": cat, "count": count, "emoji": _category_emoji(cat)}
        for cat, count in sorted(cats.items())
    ]

    return json.dumps({
        "success": True,
        "total_roles": len(index),
        "total_categories": len(categories),
        "categories": categories,
    }, ensure_ascii=False)


def _category_emoji(cat: str) -> str:
    emojis = {
        "engineering": "⚙️", "marketing": "📢", "design": "🎨", "security": "🔒",
        "testing": "🧪", "product": "📋", "finance": "💰", "sales": "🤝",
        "support": "🎧", "hr": "👥", "legal": "⚖️", "academic": "📚",
        "game-development": "🎮", "gis": "🗺️", "spatial-computing": "🥽",
        "specialized": "🔧", "strategy": "🎯", "supply-chain": "📦",
        "project-management": "📊", "paid-media": "📺",
        "unity": "🎮", "unreal-engine": "🎮", "godot": "🎮",
        "roblox-studio": "🎮", "blender": "🎨",
    }
    return emojis.get(cat, "📁")

import json
import re
import logging
from contextvars import ContextVar
from openai import AsyncOpenAI
from app.config import settings

logger = logging.getLogger(__name__)

# Request-scoped API key (set by middleware/router)
request_api_key: ContextVar[str] = ContextVar("api_key", default="")


def _get_client() -> AsyncOpenAI:
    key = request_api_key.get() or settings.deepseek_api_key
    return AsyncOpenAI(
        api_key=key,
        base_url=settings.deepseek_base_url,
        timeout=180.0,  # 3 min per call
        max_retries=1,
    )


async def call_deepseek(prompt: str, system: str = "你是一个专业的中文笔记整理助手。") -> str:
    client = _get_client()
    resp = await client.chat.completions.create(
        model=settings.deepseek_model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
        max_tokens=4096,
    )
    return resp.choices[0].message.content or ""


def _safe_json(text: str, expect_list: bool = False):
    """Safely parse AI response, handling markdown fences and malformed JSON."""
    text = re.sub(r"```json\s*|```", "", text).strip()
    # Sometimes AI wraps object in array, or returns extra text
    # Try to find JSON boundaries
    if not expect_list:
        # Look for { ... }
        m = re.search(r'\{.*\}', text, re.DOTALL)
        if m:
            try:
                val = json.loads(m.group())
                if isinstance(val, dict):
                    return val
            except json.JSONDecodeError:
                pass
    # Look for [ ... ]
    m = re.search(r'\[.*\]', text, re.DOTALL)
    if m:
        try:
            val = json.loads(m.group())
            if expect_list:
                if isinstance(val, list):
                    return val
            else:
                # Sometimes AI wraps dict in array: [{"action":...}]
                if isinstance(val, list) and len(val) > 0 and isinstance(val[0], dict):
                    return val[0]
                return val
        except json.JSONDecodeError:
            pass
    # Last resort: try to fix truncated JSON
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Try closing unclosed JSON
    for fix in [
        text + "]",
        text + "}]",
        text.rstrip(",") + "]",
    ]:
        try:
            return json.loads(fix)
        except json.JSONDecodeError:
            pass
    logger.warning("Failed to parse AI response: %s", text[:300])
    return [] if expect_list else {}


async def batch_classify(
    text: str,
    existing_files: list[dict],
    classification_rules: list[dict],
) -> list[dict]:
    """Split text into entries AND classify each - all in one AI call."""
    rules_text = "\n".join(
        f"- \"{r['pattern']}\" -> \"{r['target_file']}\""
        for r in classification_rules
    ) if classification_rules else "无"

    files_text = "\n".join(
        f"- {f['filename']}: {f.get('summary', '')}"
        for f in existing_files
    ) if existing_files else "无已有文件"

    prompt = f"""分析以下笔记，拆分成独立条目，并为每条分配目标文件。

已有文件：
{files_text}

分类规则（优先）：
{rules_text}

笔记内容：
{text}

返回JSON数组，每条包含：
[
  {{
    "content": "条目原文",
    "action": "assign 或 create_new",
    "target_file": "已有文件名（assign时必填）",
    "new_filename": "新文件名.txt（create_new时必填）",
    "importance": "high/medium/low",
    "color": "red/blue/green/yellow/orange/purple"
  }}
]

颜色：red=紧急, blue=待办, green=完成, yellow=提醒, orange=重要, purple=其他
有规则匹配必须按规则分配。无匹配文件则 create_new。
只返回JSON数组。"""
    result = await call_deepseek(prompt)
    data = _safe_json(result, expect_list=True)
    if not isinstance(data, list):
        return []
    return data


async def batch_classify_and_format(
    entries: list[dict],
    existing_files: list[dict],
    classification_rules: list[dict],
    highlight_rules: list[dict],
) -> list[dict]:
    """Classify all entries AND format them in one AI call - much faster."""
    if not entries:
        return []

    entries_text = "\n\n---\n\n".join(
        f"[条目{i}] 内容: {e.get('content', '')}\n重要性: {e.get('importance', 'medium')}\n颜色: {e.get('color', 'blue')}"
        for i, e in enumerate(entries)
    )

    rules_text = "\n".join(
        f"- 匹配 \"{r['pattern']}\" -> 归入 \"{r['target_file']}\""
        for r in classification_rules
    ) if classification_rules else "无"

    files_text = "\n".join(
        f"- {f['filename']}: {f.get('summary', '')}"
        for f in existing_files
    ) if existing_files else "无已有文件"

    prompt = f"""批量处理以下{len(entries)}条内容。对每条：1) 分配到已有文件或建议新建 2) 格式化高亮。

已有文件：
{files_text}

分类规则（优先遵循）：
{rules_text}

条目列表：
{entries_text}

返回JSON数组（顺序与输入一致）：
[
  {{
    "action": "assign 或 create_new",
    "target_file": "已有文件名（assign时）",
    "new_filename": "新文件名.txt（create_new时）",
    "keywords": ["关键词1", "关键词2", "关键词3"],
    "summary": "该条目简短摘要",
    "formatted_content": "格式化后的HTML（含span class高亮和strong加粗）",
    "skip": false
  }}
]

规则：
- 有自定义规则匹配时严格按规则分配
- 无合适文件时 action="create_new"
- 内容与已有条目高度重复时 skip=true
- 重要内容加 <span class=\"hl-颜色\"> 和 <strong>
- 颜色: hl-red(紧急), hl-blue(待办), hl-green(完成), hl-orange(提醒), hl-bold(关键词)

只返回JSON数组。"""
    result = await call_deepseek(prompt)
    data = _safe_json(result, expect_list=True)
    if not isinstance(data, list) or len(data) == 0:
        return []
    return data


async def split_summary_into_entries(text: str) -> list[dict]:
    prompt = f"""请分析以下总结笔记，将内容拆分成独立的条目（按语义划分）。

对于每个条目，返回JSON格式：
[
  {{
    "content": "条目原文内容",
    "importance": "high/medium/low",
    "color": "red/blue/green/yellow/orange/purple",
    "category_hint": "该条目所属的大致类别关键词"
  }}
]

颜色：red=紧急/问题, blue=待办/计划, green=已完成, yellow=提醒, orange=重要非紧急, purple=其他

笔记内容：
{text}

只返回JSON数组。"""
    result = await call_deepseek(prompt)
    data = _safe_json(result, expect_list=True)
    if not isinstance(data, list):
        data = [{"content": text, "importance": "medium", "color": "blue", "category_hint": ""}]
    return data


async def classify_entry_to_file(
    entry: dict,
    existing_files: list[dict],
    classification_rules: list[dict],
) -> dict:
    rules_text = "\n".join(
        f"- 规则: \"{r['pattern']}\" -> \"{r['target_file']}\""
        for r in classification_rules
    ) if classification_rules else "（无自定义规则）"

    files_text = "\n".join(
        f"- 文件: {f['filename']}, 关键词: {f.get('keywords', '')}, 摘要: {f.get('summary', '')}"
        for f in existing_files
    ) if existing_files else "（无已有文件）"

    prompt = f"""将以下内容分配到已有文件，或建议创建新文件。

已有文件：
{files_text}

自定义规则（优先）：
{rules_text}

待分类内容：
- 内容: {entry.get('content', '')}
- 重要性: {entry.get('importance', 'medium')}
- 颜色: {entry.get('color', 'blue')}
- 类别提示: {entry.get('category_hint', '')}

返回JSON对象：
{{
  "action": "assign",
  "target_file": "已有文件名",
  "new_filename": "新文件名.txt",
  "keywords": ["关键词1", "关键词2", "关键词3"],
  "summary": "简短摘要一句",
  "reason": "分配理由"
}}

有用户规则匹配时必须优先按规则分配。无合适文件时 action="create_new"。
只返回JSON对象。"""
    result = await call_deepseek(prompt)
    data = _safe_json(result, expect_list=False)
    if not isinstance(data, dict):
        # Fallback: create new file
        hint = entry.get('category_hint', '未分类')
        data = {
            "action": "create_new",
            "new_filename": f"{hint}.txt",
            "keywords": [hint],
            "summary": entry.get('content', '')[:50],
        }
    # Ensure required keys
    data.setdefault("action", "create_new")
    data.setdefault("new_filename", "新建笔记.txt")
    data.setdefault("keywords", [])
    data.setdefault("summary", "")
    data.setdefault("target_file", "")
    return data


async def generate_file_keywords_and_summary(entries: list[dict]) -> dict:
    if not entries:
        return {"keywords": ["新建"], "summary": "新创建的分类文件"}
    content_text = "\n".join(f"- {e.get('content', '')}" for e in entries[:20])
    prompt = f"""为以下内容提取关键词和摘要。

内容：
{content_text}

返回JSON：
{{
  "keywords": ["关键词1", "关键词2", "关键词3", "关键词4", "关键词5"],
  "summary": "一句话简短摘要（不超过50字）"
}}

只返回JSON对象。"""
    result = await call_deepseek(prompt)
    data = _safe_json(result, expect_list=False)
    if not isinstance(data, dict):
        data = {"keywords": [], "summary": ""}
    data.setdefault("keywords", [])
    data.setdefault("summary", "")
    return data


async def find_similar_entries(new_content: str, existing_entries: list[dict]) -> dict:
    if not existing_entries:
        return {"has_similar": False, "similar_entries": []}

    entries_text = "\n".join(
        f"[id:{e.get('id','')}] {e.get('content','')}"
        for e in existing_entries[:30]
    )

    prompt = f"""判断新内容是否与已有内容高度相似（重复度>70%）。

新内容：
{new_content}

已有内容：
{entries_text}

返回JSON：
{{
  "has_similar": true/false,
  "similar_entries": [{{"entry_id": "已有条目id", "similarity": 0.85, "existing_content": "已有内容摘要"}}]
}}

只返回JSON对象。"""
    result = await call_deepseek(prompt)
    data = _safe_json(result, expect_list=False)
    if not isinstance(data, dict):
        return {"has_similar": False, "similar_entries": []}
    data.setdefault("has_similar", False)
    data.setdefault("similar_entries", [])
    return data


async def find_cross_links(new_file_entries: list[dict], all_files: list[dict]) -> list[dict]:
    if not all_files:
        return []

    files_text = "\n".join(
        f"[id:{f.get('id','')}] 文件: {f.get('filename','')}, 关键词: {f.get('keywords','')}"
        for f in all_files
    )
    new_text = "\n".join(
        f"[id:{e.get('id','')}] {e.get('content','')}"
        for e in new_file_entries[:10]
    )

    prompt = f"""判断新内容与哪个已有文件在主题上明显相关（但不属于同一文件）。

新内容：
{new_text}

已有文件：
{files_text}

返回JSON数组：
[{{"entry_id": "新条目id", "linked_file_id": "已有文件id", "relation_reason": "关联原因"}}]

如果没有关联，返回 []。
只返回JSON数组。"""
    result = await call_deepseek(prompt)
    data = _safe_json(result, expect_list=True)
    if not isinstance(data, list):
        return []
    return data


async def auto_format_entry(entry: dict, highlight_rules: list[dict]) -> dict:
    rules_text = "\n".join(
        f"- 模式: \"{r['pattern']}\" -> 颜色: {r['color']}"
        for r in highlight_rules
    ) if highlight_rules else "默认规则"

    prompt = f"""对以下文本进行格式化处理。

原文：
{entry.get('content', '')}

高亮规则：
{rules_text}

要求：
1. 重点内容添加HTML高亮标记：
   - 紧急/问题: <span class="hl-red">...</span>
   - 待办/计划: <span class="hl-blue">...</span>
   - 已完成: <span class="hl-green">...</span>
   - 提醒: <span class="hl-orange">...</span>
   - 关键词: <span class="hl-bold">...</span>
2. 长段落按语义拆分为多行
3. 重要句子用 <strong>...</strong> 加粗

返回JSON：
{{
  "formatted_content": "格式化后的HTML文本",
  "highlighted_content": "同formatted_content"
}}

只返回JSON对象。"""
    result = await call_deepseek(prompt)
    data = _safe_json(result, expect_list=False)
    if not isinstance(data, dict):
        raw = entry.get('content', '')
        return {"formatted_content": raw, "highlighted_content": raw}
    data.setdefault("formatted_content", entry.get('content', ''))
    data.setdefault("highlighted_content", entry.get('content', ''))
    return data

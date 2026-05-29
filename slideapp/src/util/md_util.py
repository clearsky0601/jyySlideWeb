import re
import uuid
from typing import List, Union


_MATH_PATTERN = re.compile(
    r"(\$\$[\s\S]*?\$\$)"
    r"|"
    r"(\$(?!\s)(?:[^\$\\]|\\.)*(?<!\s)\$)",
)


def _protect_math(md: str):
    placeholders: dict[str, str] = {}

    def _replace(m: re.Match) -> str:
        token = m.group(0)
        key = f"\x00MATH{uuid.uuid4().hex}\x00"
        placeholders[key] = token
        return key

    safe = _MATH_PATTERN.sub(_replace, md)
    return safe, placeholders


def _restore_math(html: str, placeholders: dict[str, str]) -> str:
    for key, original in placeholders.items():
        html = html.replace(key, original)
    return html


_FENCE_RE = re.compile(r"^\s*(```+|~~~+)")
_COLUMN_OPEN_RE = re.compile(r"^\s*:::\s*column\s*$")
_DIRECTIVE_OPEN_RE = re.compile(r"^\s*:::\s*([A-Za-z][\w-]*)\s*(.*?)\s*$")
_DIRECTIVE_CLOSE_RE = re.compile(r"^\s*:::\s*$")


# === columns ===========================================================

def _build_columns_html(ratio: str, columns_md: List[str]) -> str:
    nums = [int(n) for n in re.findall(r"\d+", ratio or "")]
    n = len(columns_md)
    if not nums:
        nums = [1] * n
    elif len(nums) < n:
        nums = nums + [1] * (n - len(nums))
    nums = nums[:n]
    template = " ".join(f"{x}fr" for x in nums)
    parts = []
    for col_md in columns_md:
        inner = md_to_html(col_md)
        parts.append(f'<div class="md-column">{inner}</div>')
    style = f"grid-template-columns: {template};"
    return (
        f'<div class="md-columns" style="{style}">' + "".join(parts) + "</div>"
    )


def _handle_columns(args: str, body_md: str) -> str:
    """Body contains ``::: column ... :::`` sub-blocks; parse them out."""
    lines = body_md.split("\n")
    columns_md: List[str] = []
    current_col: List[str] = []
    in_column = False
    in_code = False
    fence_char = None

    for line in lines:
        m_fence = _FENCE_RE.match(line)
        if in_code:
            if in_column:
                current_col.append(line)
            if m_fence and m_fence.group(1)[0] == fence_char:
                in_code = False
                fence_char = None
            continue
        if m_fence:
            in_code = True
            fence_char = m_fence.group(1)[0]
            if in_column:
                current_col.append(line)
            continue
        if not in_column:
            if _COLUMN_OPEN_RE.match(line):
                in_column = True
                current_col = []
            # else: stray content between column children — ignored
        else:
            if _DIRECTIVE_CLOSE_RE.match(line):
                columns_md.append("\n".join(current_col))
                current_col = []
                in_column = False
            else:
                current_col.append(line)

    if not columns_md:
        raise ValueError("empty columns block")
    return _build_columns_html(args.strip(), columns_md)


# === admonitions =======================================================

_ADMONITION_META = {
    "note":    ("📝", "提示"),
    "tip":     ("💡", "技巧"),
    "warning": ("⚠️", "警告"),
    "danger":  ("🚫", "危险"),
    "success": ("✅", "成功"),
}


def _make_admonition_handler(kind: str):
    icon, default_title = _ADMONITION_META[kind]

    def handler(args: str, body_md: str) -> str:
        title = args.strip() or default_title
        inner = md_to_html(body_md)
        return (
            f'<aside class="admonition admonition-{kind}">'
            f'<div class="admonition-title">{icon} {title}</div>'
            f'<div class="admonition-body">{inner}</div>'
            f"</aside>"
        )

    return handler


# === speaker notes =====================================================

def _handle_notes(args: str, body_md: str) -> str:
    inner = md_to_html(body_md)
    return f'<aside class="notes">{inner}</aside>'


# === incremental list ==================================================

def _handle_incremental(args: str, body_md: str) -> str:
    """Wrap a list so each <li> reveals one-at-a-time via Reveal.js fragments."""
    from pyquery import PyQuery  # local import to keep top-level deps tidy

    inner_html = md_to_html(body_md)
    page = PyQuery(f"<div class=\"md-incremental-root\">{inner_html}</div>")
    lst = page.find("ul, ol").eq(0)
    if not lst.length:
        return inner_html
    for i, li in enumerate(lst.children("li")):
        PyQuery(li).add_class("fragment").attr("data-fragment-index", str(i + 1))
    return page.html() or inner_html


# === timeline ==========================================================

# Separator is ASCII ``:`` followed by whitespace, OR full-width ``：``.
# This lets ``14:30: event`` parse as date="14:30" / event="event" without
# eating colons inside ``http://`` URLs or other event-body content.
_TIMELINE_ITEM_RE = re.compile(r"^[-*+]\s+(.+?)(?::\s+|：\s*)(.+?)\s*$")


def _handle_timeline(args: str, body_md: str) -> str:
    items: List[tuple] = []
    for line in body_md.split("\n"):
        s = line.strip()
        if not s:
            continue
        m = _TIMELINE_ITEM_RE.match(s)
        if m:
            date, event = m.group(1), m.group(2)
        else:
            if s[:1] in ("-", "*", "+"):
                s = s[1:].strip()
            date, event = "", s
        items.append((date, event))
    if not items:
        raise ValueError("empty timeline")
    parts = []
    for date, event in items:
        event_html = md_to_html(event).strip()
        # strip a single wrapping <p>...</p> so the inline event renders inline
        if event_html.startswith("<p>") and event_html.endswith("</p>"):
            event_html = event_html[3:-4]
        parts.append(
            f'<li><span class="timeline-date">{date}</span>'
            f'<span class="timeline-event">{event_html}</span></li>'
        )
    return f'<ol class="md-timeline">{"".join(parts)}</ol>'


# === directive registry =================================================

# Filled in below as handlers are defined. Other modules can register more.
DIRECTIVE_HANDLERS: dict = {
    "columns": _handle_columns,
    "notes": _handle_notes,
    "incremental": _handle_incremental,
    "timeline": _handle_timeline,
}
for _kind in _ADMONITION_META:
    DIRECTIVE_HANDLERS[_kind] = _make_admonition_handler(_kind)


def _protect_directives(md: str):
    """Generic state machine for ``::: keyword [args] ... :::`` blocks.

    Each known keyword in ``DIRECTIVE_HANDLERS`` is dispatched to its handler;
    the resulting HTML is swapped in via a block-level placeholder div so
    Python-Markdown passes it through as raw HTML (avoiding ``<p>`` wrapping).

    Unknown keywords degrade gracefully: the original lines are restored.
    Nested blocks are tracked via a stack — a closing ``:::`` matches the most
    recent opener at the same depth. Unclosed blocks at EOF degrade.

    Handlers may raise on malformed body; the dispatcher catches and degrades.
    """
    placeholders: dict[str, str] = {}
    lines = md.split("\n")
    out: List[str] = []
    in_code = False
    fence_char = None
    stack: List[dict] = []

    def append_current(line: str) -> None:
        if stack:
            stack[-1]["raw"].append(line)
            stack[-1]["body"].append(line)
        else:
            out.append(line)

    def emit(lines_to_emit: List[str]) -> None:
        if stack:
            stack[-1]["raw"].extend(lines_to_emit)
            stack[-1]["body"].extend(lines_to_emit)
        else:
            out.extend(lines_to_emit)

    for line in lines:
        m_fence = _FENCE_RE.match(line)

        if in_code:
            append_current(line)
            if m_fence and m_fence.group(1)[0] == fence_char:
                in_code = False
                fence_char = None
            continue
        if m_fence:
            in_code = True
            fence_char = m_fence.group(1)[0]
            append_current(line)
            continue

        m_open = _DIRECTIVE_OPEN_RE.match(line)
        if m_open:
            stack.append({
                "kw": m_open.group(1),
                "args": m_open.group(2) or "",
                "body": [],
                "raw": [line],
            })
            continue

        if _DIRECTIVE_CLOSE_RE.match(line) and stack:
            frame = stack.pop()
            frame["raw"].append(line)
            handler = DIRECTIVE_HANDLERS.get(frame["kw"])
            if handler is None:
                emit(frame["raw"])
            else:
                try:
                    html = handler(frame["args"], "\n".join(frame["body"]))
                except Exception:
                    emit(frame["raw"])
                else:
                    key = f'<div data-md-directive="{uuid.uuid4().hex}"></div>'
                    placeholders[key] = html
                    emit(["", key, ""])
            continue

        append_current(line)

    # unclosed at EOF — degrade
    while stack:
        frame = stack.pop()
        emit(frame["raw"])

    return "\n".join(out), placeholders


def _restore_directives(html: str, placeholders: dict) -> str:
    # Iterate outer→inner so a nested directive's placeholder, only revealed
    # after its parent's substitution, still gets resolved. Insertion order is
    # inner-first (closing order), so reversed = outer-first.
    for key in reversed(list(placeholders)):
        html = html.replace(key, placeholders[key])
    return html


# Back-compat aliases (tests import these by their original names)
_protect_columns = _protect_directives
_restore_columns = _restore_directives


def process_images(content, func):
    """处理Markdown类型字符串中的图片链接, 返回处理过图片链接部分的Markdown字符串

    Args:
        content (_type_): Markdown类型字符串
        func (_type_): 处理图片链接的函数, 该函数接受图片链接字符串, 返回一个(有关图片链接的新串, 是否有错误)的元组
    """

    def modify(match):
        # 下面是黑盒魔法
        tar = match.group()
        pre, mid, suf = str(), str(), str()
        if tar[-1] == ")":
            pre = tar[: tar.index("(") + 1]
            mid = tar[tar.index("(") + 1 : -1]
            suf = tar[-1]
        else:
            mid = re.search(r'src="([^"]*)"', tar).group(1)
            pre, suf = tar.split(mid)

        link = mid
        # 黑盒魔法结束
        new_name, err = func(link)
        return pre + (new_name if err is False else link) + suf

    patten = r"!\[.*?\]\(((?:[^()]|\([^()]*\))*)\)|<img.*?src=[\'\"]([^\'\"]*)[\'\"].*?>"
    return re.sub(patten, modify, content)


###

from markdown import markdown
from markdown import Extension
from markdown.blockprocessors import BlockProcessor
import xml.etree.ElementTree as etree


def md_to_html(md: str) -> str:
    class BoxBlockProcessor(BlockProcessor):
        first = True

        def run(self, parent, blocks):
            if self.first:
                self.first = False
                e = etree.SubElement(parent, "div")
                self.parser.parseBlocks(e, blocks)
                for _ in range(0, len(blocks)):
                    blocks.pop(0)
                return True
            return False

    class BoxExtension(Extension):
        def extendMarkdown(self, md):
            md.parser.blockprocessors.register(BoxBlockProcessor(md.parser), "box", 175)

    extensions: List = [
        BoxExtension(),
        # "meta" intentionally NOT enabled: front matter is parsed via the
        # `+++++` separator in converter.py before markdown runs. The meta
        # extension's pattern (``Key: Value`` at document start) silently
        # swallows any leading "word: value" line — including recursive calls
        # like timeline-event "30: 下午活动".
        "fenced_code",
        "codehilite",
        "extra",
        "attr_list",
        "tables",
        "toc",
        # Tier B: Python-Markdown built-in extras
        "footnotes",
        "def_list",
        "sane_lists",
        # Tier C: pymdown-extensions
        "pymdownx.mark",
        "pymdownx.tilde",
        "pymdownx.caret",
        "pymdownx.tasklist",
        "pymdownx.emoji",
    ]
    from pymdownx import emoji as _pymdownx_emoji
    extension_configs = {
        "pymdownx.tasklist": {"custom_checkbox": False, "clickable_checkbox": False},
        "pymdownx.emoji": {
            "emoji_index": _pymdownx_emoji.gemoji,
            "emoji_generator": _pymdownx_emoji.to_alt,
        },
        # smart=False so ``==高亮==`` works adjacent to CJK characters
        "pymdownx.mark": {"smart_mark": False},
        "pymdownx.tilde": {"smart_delete": False, "subscript": True},
        "pymdownx.caret": {"smart_insert": False, "superscript": True},
    }
    safe_md, math_placeholders = _protect_math(md)
    safe_md, directive_placeholders = _protect_directives(safe_md)
    html = markdown(safe_md, extensions=extensions, extension_configs=extension_configs)
    html = _restore_directives(html, directive_placeholders)
    return _restore_math(html, math_placeholders)

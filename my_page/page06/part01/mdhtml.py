"""page06/part01 · 分析结果 HTML 报告导出（2026-09-25 V3：C 项配套）。

零第三方依赖的 markdown→HTML 转换：覆盖 LLM 输出的常用结构
（标题/无序有序列表/粗斜体/分隔线/表格/段落）。
导出为可直接浏览器打开、打印友好的独立 HTML 文件。
"""
import html as _html
import re
from datetime import datetime


def _inline(s):
    """行内元素：先转义，再粗体/斜体/行内码。"""
    s = _html.escape(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"<em>\1</em>", s)
    return s


def md_to_html(md_text):
    """markdown（标题/列表/表格/粗斜体/分隔线/段落）→ HTML 片段。"""
    lines = (md_text or "").splitlines()
    out, i, n = [], 0, len(lines)

    def _table(buf):
        rows = [[c.strip() for c in r.strip().strip("|").split("|")]
                for r in buf if not re.match(r"^\s*\|?[\s:|-]+\|?\s*$", r)]
        if not rows:
            return ""
        head, body = rows[0], rows[1:]
        h = "".join(f"<th>{_inline(c)}</th>" for c in head)
        trs = "".join("<tr>" + "".join(f"<td>{_inline(c)}</td>" for c in r)
                      + "</tr>" for r in body)
        return (f'<table><thead><tr>{h}</tr></thead><tbody>{trs}</tbody></table>')

    while i < n:
        line = lines[i]
        s = line.strip()
        if not s:
            i += 1
            continue
        if s.startswith("|"):                       # 表格块
            buf = []
            while i < n and lines[i].strip().startswith("|"):
                buf.append(lines[i]); i += 1
            out.append(_table(buf))
            continue
        m = re.match(r"^(#{1,4})\s+(.*)$", s)
        if m:
            out.append(f"<h{len(m.group(1)) + 1}>{_inline(m.group(2))}</h{len(m.group(1)) + 1}>")
            i += 1
            continue
        if re.match(r"^(-{3,}|\*{3,}|_{3,})$", s):
            out.append("<hr/>"); i += 1
            continue
        if re.match(r"^[-*+]\s+", s):               # 无序列表
            items = []
            while i < n and re.match(r"^\s*[-*+]\s+", lines[i]):
                items.append(re.sub(r"^\s*[-*+]\s+", "", lines[i])); i += 1
            out.append("<ul>" + "".join(
                f"<li>{_inline(x)}</li>" for x in items) + "</ul>")
            continue
        if re.match(r"^\d+[.、]\s+", s):            # 有序列表
            items = []
            while i < n and re.match(r"^\s*\d+[.、]\s+", lines[i]):
                items.append(re.sub(r"^\s*\d+[.、]\s+", "", lines[i])); i += 1
            out.append("<ol>" + "".join(
                f"<li>{_inline(x)}</li>" for x in items) + "</ol>")
            continue
        para = [s]
        i += 1
        while (i < n and lines[i].strip()
               and not lines[i].strip().startswith(("#", "|", "- ", "* ", ">"))
               and not re.match(r"^\s*([-*+]\s|\d+[.、]\s)", lines[i])
               and not re.match(r"^(-{3,}|\*{3,}|_{3,})$", lines[i].strip())):
            para.append(lines[i].strip()); i += 1
        out.append(f"<p>{_inline(' '.join(para))}</p>")
    return "\n".join(out)


_CSS = """
body{font-family:'PingFang SC','Microsoft YaHei',serif;max-width:860px;
margin:32px auto;padding:0 24px;color:#2b2b2b;line-height:1.8;
background:#fbfaf7}
h1{font-size:1.5em;border-bottom:3px double #8c6f4a;padding-bottom:8px;color:#5a4326}
h2{font-size:1.25em;color:#7a5c30;margin-top:1.6em}
h3{font-size:1.05em;color:#8c6f4a}
table{border-collapse:collapse;width:100%;margin:12px 0;font-size:.92em}
th{background:#f3ead8;color:#5a4326}
th,td{border:1px solid #d9cdb4;padding:6px 10px;text-align:left}
.meta{color:#8a7c66;font-size:.88em;margin:4px 0 20px}
.footer{margin-top:36px;padding-top:10px;border-top:1px solid #d9cdb4;
color:#a09585;font-size:.8em}
@media print{body{margin:0;background:#fff}}
"""


def build_report_html(title, meta_lines, result_md):
    """组装独立 HTML 报告（标题+元信息+正文+免责页脚）。"""
    meta = "".join(f"<div>{_html.escape(m)}</div>" for m in meta_lines)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>{_html.escape(title)}</title>
<style>{_CSS}</style>
</head>
<body>
<h1>{_html.escape(title)}</h1>
<div class="meta">{meta}<div>生成时间：{now}</div></div>
{md_to_html(result_md)}
<div class="footer">本报告由「中医道医学习平台 · 五运六气体质分析」生成，
内容为体质倾向提示，不构成医疗诊断，不预测吉凶。健康问题请线下就医。</div>
</body>
</html>
"""

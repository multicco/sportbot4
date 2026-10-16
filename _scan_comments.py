# -*- coding: utf-8 -*-
import os
import re

ROOT = os.path.dirname(os.path.abspath(__file__))
SKIP_DIRS = {"venv", "env", ".venv", "__pycache__", "node_modules", ".git", ".idea"}

# Признаки того, что внутри комментария реально код
CODE_HINT = re.compile(
    r"(\(|\)|=|:\s|await |async def |def |class |import |from .+ import|"
    r"return|\bself\b|\[|\]|\{|\}|f['\"]|print\(|logger\.|callback|message\.|"
    r"\.as_markup|kb\.button|dp\.|F\.data)"
)

# Строки-разделители/заголовки — это не код
HEADER = re.compile(r"^[=\-\*#\s]{3,}$")


def is_comment(line: str) -> bool:
    return line.lstrip().startswith("#")


def ctext(line: str) -> str:
    return line.lstrip()[1:].strip()


def report():
    grand_blocks = 0
    grand_lines = 0
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in sorted(filenames):
            if not fn.endswith(".py") or fn == "_scan_comments.py":
                continue
            path = os.path.join(dirpath, fn)
            try:
                with open(path, encoding="utf-8") as f:
                    lines = f.readlines()
            except Exception:
                continue
            blocks = []
            i = 0
            n = len(lines)
            while i < n:
                if is_comment(lines[i]):
                    start = i
                    j = i
                    while j < n and is_comment(lines[j]):
                        j += 1
                    seg = [ctext(lines[k]) for k in range(start, j)]
                    # сколько строк похожи на код
                    code_like = sum(
                        1 for t in seg
                        if t and not HEADER.match(t) and CODE_HINT.search(t)
                    )
                    length = j - start
                    # блок считаем мёртвым кодом: >=2 строк и >=60% строк похожи на код
                    if length >= 2 and code_like >= max(2, int(length * 0.6)):
                        blocks.append((start + 1, j, length, code_like))
                    i = j
                else:
                    i += 1
            if blocks:
                rel = os.path.relpath(path, ROOT)
                total = sum(b[2] for b in blocks)
                grand_blocks += len(blocks)
                grand_lines += total
                print(f"\n{rel}, {len(blocks)} блок(ов), {total} строк")
                for (s, e, ln, cl) in blocks:
                    print(f"    строки {s}, {e}, {ln} стр., code-like {cl})")
    print(f"\n==== ИТОГО: {grand_blocks} блоков, {grand_lines} строк ====")


if __name__ == "__main__":
    report()

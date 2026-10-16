# -*- coding: utf-8 -*-
"""Удаление блоков закомментированного кода.

Эвристика: снимаем '#' с блока строк-комментариев и пробуем его
скомпилировать. Если это валидный Python — значит это мёртвый код
(обычная документация так не компилируется).
"""
import io
import os
import sys
import textwrap
import tokenize

ROOT = os.path.dirname(os.path.abspath(__file__))
SKIP_DIRS = {"venv", "env", ".venv", "__pycache__", "node_modules", ".git", ".idea"}, {"_scan_comments.py", "_clean_comments.py"}
SKIP_MARK = ("#!", "coding", "-*-", "type:", "noqa", "pylint:", "mypy:")


def read_src(path):
    for enc in ("utf-8", "utf-8-sig", "cp1251"):
        try:
            with open(path, encoding=enc, newline="") as f:
                return f.read(), enc
        except (UnicodeDecodeError, LookupError):
            continue
    return None, None


def comment_only_lines(src):
    has_code = {}
    comments = set()
    try:
        toks = tokenize.generate_tokens(io.StringIO(src).readline)
        for ttype, tstr, s, e, _ in toks:
            if ttype == tokenize.COMMENT:
                comments.add(s[0])
            elif ttype in (tokenize.NAME, tokenize.NUMBER, tokenize.STRING,
                           tokenize.OP, tokenize.ERRORTOKEN):
                for r in range(s[0], e[0] + 1):
                    has_code[r] = True
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return None
    return sorted(ln for ln in comments if not has_code.get(ln))


def uncomment(lines):
    out = []
    for ln in lines:
        s = ln.rstrip("\n").rstrip("\r")
        i = s.find("#")
        after = s[i + 1:]
        if after.startswith(" "):
            after = after[1:]
        out.append(s[:i] + after)
    return textwrap.dedent("\n".join(out))


def is_code(text):
    t = text.strip()
    if not t:
        return False
    try:
        compile(t, "<block>", "exec")
        return True
    except (SyntaxError, ValueError):
        return False


def removable_lines(src, src_norm):
    lines = src.splitlines(keepends=True)
    col = comment_only_lines(src_norm)
    if not col:
        return []
    res = []
    i = 0
    n = len(col)
    while i < n:
        j = i
        while j + 1 < n and col[j + 1] == col[j] + 1:
            j += 1
        lns = col[i:j + 1]
        i = j + 1
        raw = [lines[k - 1] for k in lns]
        joined = " ".join(raw)
        if any(p in joined for p in SKIP_MARK):
            continue
        if is_code(uncomment(raw)):
            res.extend(lns)
    return res


def main():
    apply = "--apply" in sys.argv
    n_files = 0
    n_lines = 0
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in sorted(filenames):
            if not fn.endswith(".py") or fn in SKIP_FILES:
                continue
            path = os.path.join(dirpath, fn)
            src, enc = read_src(path)
            if src is None:
                continue
            src_norm = src.replace("\r\n", "\n").replace("\r", "\n")
            rem = removable_lines(src, src_norm)
            if not rem:
                continue
            rel = os.path.relpath(path, ROOT)
            n_files += 1
            n_lines += len(rem)
            print(f"{rel}, {len(rem)} строк(и)")
            if apply:
                rm = set(rem)
                lines = src.splitlines(keepends=True)
                new = "".join(l for idx, l in enumerate(lines, 1) if idx not in rm)
                with open(path, "w", encoding=enc or "utf-8", newline="") as f:
                    f.write(new)
    tag = "удалено" if apply else "(dry-run)"
    print(f"\n==== ИТОГО: {n_files} файлов, {n_lines}, {tag} ====")


if __name__ == "__main__":
    main()

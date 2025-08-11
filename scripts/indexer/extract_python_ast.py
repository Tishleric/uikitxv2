from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Iterator

OUTPUT = Path("memory-bank/index/python_ast.jsonl")


def iter_python_files(root: Path) -> Iterator[Path]:
    for p in root.rglob("*.py"):
        # Skip common caches and generated egg-info
        if any(part in {".git", "__pycache__", ".pytest_cache", "uikitxv2.egg-info"} for part in p.parts):
            continue
        yield p


def extract_ast_summary(path: Path) -> dict:
    src = path.read_text(encoding="utf-8", errors="ignore")
    tree = ast.parse(src, filename=str(path))
    mod_doc = ast.get_docstring(tree)
    imports = []
    functions = []
    classes = []
    for node in tree.body:
        if isinstance(node, ast.Import):
            for n in node.names:
                imports.append(n.name)
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            imports.append(mod)
        elif isinstance(node, ast.FunctionDef):
            arg_names = [a.arg for a in node.args.args]
            functions.append({"name": node.name, "args": arg_names})
        elif isinstance(node, ast.ClassDef):
            methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
            bases = [getattr(b, "id", getattr(getattr(b, "attr", None), "attr", "")) for b in node.bases]
            classes.append({"name": node.name, "bases": bases, "methods": methods})
    return {
        "path": str(path.as_posix()),
        "module_doc": mod_doc,
        "imports": sorted(set(i for i in imports if i)),
        "functions": functions,
        "classes": classes,
    }


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8") as out:
        for py in iter_python_files(Path(".").resolve()):
            try:
                rec = extract_ast_summary(py)
            except Exception as e:
                rec = {"path": str(py.as_posix()), "error": repr(e)}
            out.write(json.dumps(rec, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()


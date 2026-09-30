"""Build student + instructor notebooks from lab_src/labN.py.
Each labN.py defines TITLE and CELLS: a list of
  ("md", text)                      markdown, both versions
  ("code", code)                    code, both versions
  ("code", stub, solution)          student gets stub, instructor gets solution
Run:  python build.py            -> writes ../../labs/*.ipynb and ../solutions/*.ipynb
"""
import importlib.util, os, sys, textwrap
import nbformat as nbf

HERE = os.path.dirname(os.path.abspath(__file__))
COURSE = os.path.abspath(os.path.join(HERE, "..", ".."))

SETUP = '''# --- Setup: run this cell first -------------------------------------------
# Finds the course data whether you are in Colab or on your own laptop.
# INSTRUCTOR: set DATA_URL once to the raw GitHub folder that holds /data (see instructor README).
import os
DATA_URL = "https://raw.githubusercontent.com/YOUR-ACCOUNT/g492-coding-with-ai/main/data/"
for candidate in ["data/", "../data/", "../../data/"]:
    if os.path.exists(candidate + "orders.csv"):
        DATA = candidate
        break
else:
    DATA = DATA_URL
print("Reading data from:", DATA)'''

def load(n):
    spec = importlib.util.spec_from_file_location(f"lab{n}", os.path.join(HERE, f"lab{n}.py"))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

def build(n):
    m = load(n)
    for version in ("student", "instructor"):
        nb = nbf.v4.new_notebook()
        nb.metadata = {"kernelspec": {"name": "python3", "display_name": "Python 3"}, "colab": {"provenance": []}}
        cells = []
        head = f"# Lab {n}: {m.TITLE}\n**BUS-G 492 · Coding with AI for Business Analysts**"
        if version == "instructor":
            head += "\n\n> **INSTRUCTOR VERSION — contains solutions. Do not distribute.**"
        cells.append(nbf.v4.new_markdown_cell(head))
        cells.append(nbf.v4.new_code_cell(SETUP))
        for c in m.CELLS:
            kind, body = c[0], c[1]
            if kind == "md":
                cells.append(nbf.v4.new_markdown_cell(textwrap.dedent(body).strip()))
            else:
                src = c[2] if (len(c) == 3 and version == "instructor") else body
                cells.append(nbf.v4.new_code_cell(textwrap.dedent(src).strip()))
        nb.cells = cells
        out = os.path.join(COURSE, "labs" if version == "student" else "instructor/solutions")
        os.makedirs(out, exist_ok=True)
        suffix = "" if version == "student" else "_SOLUTIONS"
        path = os.path.join(out, f"lab{n}_{m.SLUG}{suffix}.ipynb")
        nbf.write(nb, path)
        print("wrote", os.path.relpath(path, COURSE))

if __name__ == "__main__":
    for n in (sys.argv[1:] or range(1, 7)):
        build(int(n))

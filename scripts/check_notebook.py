"""Print a summary of an executed notebook: cells run, errors, warnings, and the last outputs."""
import json
import sys

nb = json.load(open(sys.argv[1], encoding="utf-8"))
code = [c for c in nb["cells"] if c["cell_type"] == "code"]
errors = sum(o.get("output_type") == "error" for c in code for o in c["outputs"])
warns = [i for i, c in enumerate(code) for o in c["outputs"]
         if o.get("name") == "stderr" and "Warning" in "".join(o.get("text", ""))]
ran = sum(c.get("execution_count") is not None for c in code)
print(f"code cells: {len(code)} | executed: {ran} | errors: {errors} | cells with warnings: {warns}")
print("=" * 60)
for c in nb["cells"][-6:]:
    if c["cell_type"] != "code":
        continue
    for o in c["outputs"]:
        t = o.get("text") or o.get("data", {}).get("text/plain", "")
        print("".join(t).rstrip())
        print("-" * 60)

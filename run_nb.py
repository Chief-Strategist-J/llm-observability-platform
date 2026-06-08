import json
import matplotlib
matplotlib.use('Agg')
import traceback
import sys

path = 'notebooks/runbooks/research/nli-worker/2026-06-05-decoupling/research.ipynb'
with open(path) as f:
    nb = json.load(f)

global_env = {}

for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        print(f"--- Executing Cell {i} ---")
        code = "".join(cell['source'])
        try:
            exec(code, global_env)
            print(f"--- Cell {i} Completed successfully ---\n")
        except Exception as e:
            print(f"Error executing cell {i}: {e}")
            traceback.print_exc()
            sys.exit(1)
print("All cells executed successfully!")

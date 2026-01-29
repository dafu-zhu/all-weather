#!/usr/bin/env python3
"""
Renumber notebook sections after inserting lookback optimization
"""

import json
import re

# Load notebook
with open('notebooks/all_weather_v1_baseline.ipynb', 'r') as f:
    nb = json.load(f)

# Section renumbering map (old -> new)
# After inserting section 4 (Lookback Optimization), old sections 4-9 become 5-10
renumber_map = {
    '## 4. Run Backtest': '## 5. Run Backtest',
    '## 5. Plot Equity Curve': '## 6. Plot Equity Curve',
    '## 6. Performance Metrics': '## 7. Performance Metrics',
    '## 7. Weight Evolution Over Time': '## 8. Weight Evolution Over Time',
    '## 8. Risk Contribution Analysis': '## 9. Risk Contribution Analysis',
    '## 9. Export Results': '## 10. Export Results'
}

# Update markdown cells
for cell in nb['cells']:
    if cell['cell_type'] == 'markdown':
        source = ''.join(cell['source'])
        for old, new in renumber_map.items():
            if source.startswith(old):
                cell['source'] = [new + source[len(old):]]
                print(f"Renumbered: {old} → {new}")
                break

# Save notebook
with open('notebooks/all_weather_v1_baseline.ipynb', 'w') as f:
    json.dump(nb, f, indent=1)

print("\nSection renumbering complete!")

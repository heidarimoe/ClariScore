ClariScore — Building Benchmarking (Excel I/O)
ClariScore benchmarks a building’s energy performance against regional averages and returns a 1–100 score (ENERGY STAR-style) using our own dataset.

✅ Input/Output via Excel

✅ One-click Windows .bat runners

✅ Clear results (EUI, benchmark, ratio, score, label)

✅ Helpful diagnostics when a type/region doesn’t match

Quick start (Windows)
1) Set up Python (one-time)
bat
Copy
Edit
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
You need Python 3.10+ (3.12 recommended).

2) Put the benchmark file in place
Copy ClariScore_Data.xlsx into the project root (same folder as this README).

3) Create a blank input template
Double-click: make_template.bat
This generates ClariScore_Input_Template.xlsx with:

Input sheet (fill this)

Helper sheets: valid Building Types and Regions (res vs non-res)

4) Fill the template (one row = one building)
Required columns:

Building Type – must match a helper list entry exactly

Region – must match allowed regions for that type (never “Canada”)

Non-res regions: Atlantic, Great Lakes, Pacific Coast, Other

Residential regions: Atlantic, Quebec, Ontario, Manitoba / Saskatchewan, Alberta, British Columbia

Electricity_kWh, Gas_m3 (gas converts at 10.35 kWh/m³), Floor_Area_m2, Email

Optional:

Building Name (for display only)

5) Run ClariScore
Close Excel (to avoid file locks), then double-click: run_clariscore.bat
This writes ClariScore_Results.xlsx with:

User_EUI_kWh_m2

Benchmark_EUI_kWh_m2

Performance_Ratio

ClariScore (1–100) + Category (“Top Performer”, “Above Average”, “Average”, “Below Average”, “Needs Improvement”)

CTA (“Push this building to QuickModel for deeper analysis”)

Diagnostics: Match_Status, Matched_Type, Matched_Region, Notes

What’s included
pgsql
Copy
Edit
project-root/
├─ clariscore/
│  ├─ __init__.py
│  ├─ core.py                    # engine: parsing, matching, conversion, scoring
│  └─ scripts/
│     ├─ make_input_template.py  # creates blank input Excel + helper lists
│     └─ process_input.py        # computes results from filled input
├─ run.py                        # one-click run inside PyCharm (▶)
├─ make_template.bat             # double-click to generate template
├─ run_clariscore.bat            # double-click to process results
├─ requirements.txt
├─ README.md                     # this guide
└─ (place) ClariScore_Data.xlsx  # your benchmark file (not tracked by git)
Scoring (high level)
Convert gas to kWh: m³ × 10.35

Total energy = electricity + converted gas

User EUI = total kWh / floor area (m²)

Benchmark EUI is looked up by Building Type + Region

Performance Ratio = Benchmark EUI / User EUI

ClariScore is computed from a continuous curve calibrated to “feel” like ENERGY STAR; category labels follow these bands:

Ratio > 1.5 → 95 (Top Performer)

1.2–1.5 → 85 (Above Average)

0.9–1.2 → 65 (Average)

0.7–0.9 → 40 (Below Average)

< 0.7 → 20 (Needs Improvement)

Want different calibration? Edit anchors in clariscore/core.py (search for ANCHORS) to nudge scores without changing labels.

Troubleshooting
Benchmark EUI or Ratio is blank

The Building Type and/or Region didn’t match the dataset.

Fix spelling and spacing; copy/paste from helper sheets.

Check the diagnostic columns (Match_Status, Notes) for guidance.

“No module named ‘clariscore’”

Run from the project root.

Use the .bat files or python -m clariscore.scripts... (not python scripts/...).

Excel file in use / cannot write

Close Excel. Windows locks files while open.

Pip/permissions or long path errors

Use python -m pip install ...

Keep the folder path short (e.g., C:\Users\<you>\Desktop\ClariScore)


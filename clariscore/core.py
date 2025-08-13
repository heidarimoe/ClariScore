from __future__ import annotations
import pandas as pd
from typing import Tuple, List, Dict, Optional
import re
from difflib import get_close_matches

GAS_KWH_PER_M3 = 10.35  # conversion

# --- Categories stay as you defined ---
SCORE_BANDS: List[Dict[str, object]] = [
    {"min_ratio": 1.5, "max_ratio": None, "score": 95, "label": "Top Performer"},
    {"min_ratio": 1.2, "max_ratio": 1.5, "score": 85, "label": "Above Average"},
    {"min_ratio": 0.9, "max_ratio": 1.2, "score": 65, "label": "Average"},
    {"min_ratio": 0.7, "max_ratio": 0.9, "score": 40, "label": "Below Average"},
]
def ratio_to_label(ratio: float) -> str:
    for band in SCORE_BANDS:
        min_r = band["min_ratio"]; max_r = band["max_ratio"]
        if max_r is None:
            if ratio > min_r: return band["label"]  # type: ignore
        else:
            if min_r <= ratio <= max_r: return band["label"]  # type: ignore
    return "Needs Improvement"

# --- NEW: continuous score to mimic ENERGY STAR feel ---
# Anchors: (ratio -> score)
ANCHORS = [
    (0.70, 20),
    (0.90, 46),   # target ~46 around 0.90
    (1.20, 85),
    (1.50, 95),
]
def score_continuous(ratio: float) -> int:
    if ratio is None or pd.isna(ratio): return 20
    if ratio <= ANCHORS[0][0]: return ANCHORS[0][1]
    if ratio >= ANCHORS[-1][0]: return ANCHORS[-1][1]
    # piecewise-linear interpolation
    for (x1, y1), (x2, y2) in zip(ANCHORS, ANCHORS[1:]):
        if x1 <= ratio <= x2:
            t = (ratio - x1) / (x2 - x1)
            return int(round(y1 + t * (y2 - y1)))
    return 20

# --- Text normalization helpers to avoid “Low-rise a…” issues ---
_HYPHENS = r"[\u2010\u2011\u2012\u2013\u2014\u2212-]"  # various hyphens/minus
def _norm_text(s: str) -> str:
    if s is None: return ""
    s = str(s)
    s = s.replace("\xa0", " ")                         # non-breaking space
    s = re.sub(_HYPHENS, "-", s)                      # normalize hyphens to "-"
    s = re.sub(r"\s+", " ", s).strip()                # collapse spaces
    return s.lower()                                   # case-insensitive match

class ClariScoreEngine:
    def __init__(self, benchmark_xlsx_path: str, sheet_name: str = "Types (2)"):
        self.benchmark_xlsx_path = benchmark_xlsx_path
        self.sheet_name = sheet_name
        self.nonres_bench, self.res_bench = self._parse_benchmarks()

        # Build normalized keys for robust lookup
        for df in (self.nonres_bench, self.res_bench):
            df["bt_norm"] = df["building_type"].apply(_norm_text)
            df["rg_norm"] = df["region"].apply(_norm_text)

        self.nonres_types = sorted(self.nonres_bench["building_type"].unique())
        self.res_types = sorted(self.res_bench["building_type"].unique())

        self.nonres_regions = sorted([r for r in self.nonres_bench["region"].unique() if _norm_text(r) != "canada"])
        self.res_regions = sorted([r for r in self.res_bench["region"].unique() if _norm_text(r) != "canada"])

        # For fuzzy suggestions
        self._nonres_bt_norms = sorted(self.nonres_bench["bt_norm"].unique())
        self._res_bt_norms = sorted(self.res_bench["bt_norm"].unique())

    def _parse_benchmarks(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        df = pd.read_excel(self.benchmark_xlsx_path, sheet_name=self.sheet_name)

        # Find residential header (second "Canada" in col 2)
        header_row = None; canada_hits = 0
        for i in range(len(df)):
            if str(df.iloc[i,2]).strip().lower() == "canada":
                canada_hits += 1
                if canada_hits == 2:
                    header_row = i; break
        if header_row is None:
            raise ValueError("Could not locate residential header row in the benchmark sheet.")

        # Non-res block
        nonres_block = df.iloc[1:header_row, [1,2,3,4,5,6]].copy()
        nonres_block.columns = ["building_type","Canada","Atlantic","Great Lakes","Pacific Coast","Other"]
        nonres_long = nonres_block.melt(id_vars=["building_type"], var_name="region", value_name="benchmark_eui_kwh_m2")
        nonres_long = nonres_long.dropna(subset=["building_type","benchmark_eui_kwh_m2"]).reset_index(drop=True)

        # Residential block
        res_cols = ["building_type"] + [str(x) for x in df.iloc[header_row, 2:9].tolist()]
        res_block = df.iloc[header_row+1:, [1,2,3,4,5,6,7,8]].copy()
        res_block.columns = res_cols
        res_long = res_block.melt(id_vars=["building_type"], var_name="region", value_name="benchmark_eui_kwh_m2")
        res_long = res_long.dropna(subset=["building_type","benchmark_eui_kwh_m2"]).reset_index(drop=True)

        return nonres_long, res_long

    def pick_sector(self, building_type: str) -> str:
        bt = _norm_text(building_type)
        return "residential" if bt in set(self.res_bench["bt_norm"]) else "nonres"

    def valid_regions_for_type(self, building_type: str) -> List[str]:
        sector = self.pick_sector(building_type)
        return self.res_regions if sector == "residential" else self.nonres_regions

    def _lookup_with_diag(self, building_type: str, region: str) -> tuple[Optional[float], Dict[str,str]]:
        """Return (benchmark_eui, diagnostics dict). Uses normalized matching and fuzzy fallback on type."""
        bt_in = _norm_text(building_type)
        rg_in = _norm_text(region)

        # Which table?
        sector = "residential" if bt_in in set(self.res_bench["bt_norm"]) else "nonres"
        table = self.res_bench if sector == "residential" else self.nonres_bench

        # Exact normalized match
        sub = table[(table["bt_norm"] == bt_in) & (table["rg_norm"] == rg_in)]
        if not sub.empty:
            return float(sub.iloc[0]["benchmark_eui_kwh_m2"]), {
                "Match_Status": "exact",
                "Matched_Type": str(sub.iloc[0]["building_type"]),
                "Matched_Region": str(sub.iloc[0]["region"]),
                "Notes": "",
            }

        # If type didn’t match, try fuzzy suggestion (top close match in that sector)
        bt_pool = set(table["bt_norm"])
        suggestion = get_close_matches(bt_in, list(bt_pool), n=1, cutoff=0.82)
        if suggestion:
            sub2 = table[(table["bt_norm"] == suggestion[0]) & (table["rg_norm"] == rg_in)]
            if not sub2.empty:
                return float(sub2.iloc[0]["benchmark_eui_kwh_m2"]), {
                    "Match_Status": "fuzzy_type",
                    "Matched_Type": str(sub2.iloc[0]["building_type"]),
                    "Matched_Region": str(sub2.iloc[0]["region"]),
                    "Notes": f"Used closest building type to '{building_type}'.",
                }

        # If type matched but region didn’t, say so
        if bt_in in bt_pool:
            return None, {
                "Match_Status": "type_ok_region_miss",
                "Matched_Type": "",
                "Matched_Region": "",
                "Notes": f"Region '{region}' not valid for building type '{building_type}'.",
            }

        # Missed both
        return None, {
            "Match_Status": "no_match",
            "Matched_Type": "",
            "Matched_Region": "",
            "Notes": f"No benchmark found for type '{building_type}' and region '{region}'.",
        }

    def compute(self, df_in: pd.DataFrame) -> pd.DataFrame:
        required = ["Building Type","Region","Electricity_kWh","Gas_m3","Floor_Area_m2","Email"]
        df = df_in.copy()
        missing = [c for c in required if c not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        # numerics
        for col in ["Electricity_kWh","Gas_m3","Floor_Area_m2"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        # conversions
        df["Gas_kWh"] = df["Gas_m3"] * GAS_KWH_PER_M3
        df["Total_kWh"] = df["Electricity_kWh"].fillna(0) + df["Gas_kWh"].fillna(0)
        df["User_EUI_kWh_m2"] = df["Total_kWh"] / df["Floor_Area_m2"].replace({0: pd.NA})

        # benchmark lookup with diagnostics
        diags = df.apply(lambda r: self._lookup_with_diag(str(r["Building Type"]), str(r["Region"])), axis=1)
        df["Benchmark_EUI_kWh_m2"] = [x[0] for x in diags]
        diag_dicts = [x[1] for x in diags]
        df["Match_Status"] = [d["Match_Status"] for d in diag_dicts]
        df["Matched_Type"] = [d["Matched_Type"] for d in diag_dicts]
        df["Matched_Region"] = [d["Matched_Region"] for d in diag_dicts]
        df["Notes"] = [d["Notes"] for d in diag_dicts]

        # ratio + score + category
        df["Performance_Ratio"] = df["Benchmark_EUI_kWh_m2"] / df["User_EUI_kWh_m2"]
        df["ClariScore"] = df["Performance_Ratio"].apply(score_continuous)
        df["Category"] = df["Performance_Ratio"].apply(lambda x: ratio_to_label(x) if pd.notna(x) else "Needs Improvement")

        # CTA
        df["CTA"] = "Push this building to QuickModel for deeper analysis"

        preferred = [
            "Building Name","Building Type","Region",
            "Electricity_kWh","Gas_m3","Gas_kWh","Total_kWh","Floor_Area_m2",
            "User_EUI_kWh_m2","Benchmark_EUI_kWh_m2","Performance_Ratio",
            "ClariScore","Category","CTA","Email",
            # diagnostics at the end
            "Match_Status","Matched_Type","Matched_Region","Notes"
        ]
        cols = [c for c in preferred if c in df.columns] + [c for c in df.columns if c not in preferred]
        return df[cols]

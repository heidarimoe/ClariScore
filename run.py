import sys
from clariscore.scripts import process_input

if __name__ == "__main__":
    # Make sure you run this from the project root (where ClariScore_Data.xlsx lives)
    sys.argv = [
        "process_input.py",
        "--benchmarks", "ClariScore_Data.xlsx",
        "--input", "ClariScore_Input_Template.xlsx",
        "--out", "ClariScore_Results.xlsx",
    ]
    process_input.main()
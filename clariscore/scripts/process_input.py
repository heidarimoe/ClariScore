import argparse, pandas as pd, os
from clariscore import ClariScoreEngine
def main():
    p = argparse.ArgumentParser()
    p.add_argument('--benchmarks', required=True)
    p.add_argument('--input', required=True)
    p.add_argument('--out', default='ClariScore_Results.xlsx')
    args = p.parse_args()
    engine = ClariScoreEngine(args.benchmarks)
    try:
        df_in = pd.read_excel(args.input, sheet_name='Input')
    except Exception:
        df_in = pd.read_excel(args.input)
    results = engine.compute(df_in)
    with pd.ExcelWriter(args.out, engine='openpyxl') as xw:
        results.to_excel(xw, index=False, sheet_name='Results')
        pd.DataFrame({'NonRes Types': engine.nonres_types}).to_excel(xw, index=False, sheet_name='NonRes Types')
        pd.DataFrame({'Residential Types': engine.res_types}).to_excel(xw, index=False, sheet_name='Residential Types')
        pd.DataFrame({'NonRes Regions': engine.nonres_regions}).to_excel(xw, index=False, sheet_name='NonRes Regions')
        pd.DataFrame({'Residential Regions': engine.res_regions}).to_excel(xw, index=False, sheet_name='Residential Regions')
    print('Wrote:', os.path.abspath(args.out))
if __name__ == '__main__':
    main()

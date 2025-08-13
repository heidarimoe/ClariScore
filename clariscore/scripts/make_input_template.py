import argparse, pandas as pd, os
from clariscore import ClariScoreEngine
def main():
    p = argparse.ArgumentParser()
    p.add_argument('--benchmarks', required=True)
    p.add_argument('--out', default='ClariScore_Input_Template.xlsx')
    args = p.parse_args()
    engine = ClariScoreEngine(args.benchmarks)
    input_cols = ['Building Name','Building Type','Region','Electricity_kWh','Gas_m3','Floor_Area_m2','Email']
    df = pd.DataFrame(columns=input_cols)
    with pd.ExcelWriter(args.out, engine='openpyxl') as xw:
        df.to_excel(xw, index=False, sheet_name='Input')
        pd.DataFrame({'NonRes_Building_Types': engine.nonres_types}).to_excel(xw, index=False, sheet_name='NonRes Types')
        pd.DataFrame({'Residential_Building_Types': engine.res_types}).to_excel(xw, index=False, sheet_name='Residential Types')
        pd.DataFrame({'NonRes_Regions': engine.nonres_regions}).to_excel(xw, index=False, sheet_name='NonRes Regions')
        pd.DataFrame({'Residential_Regions': engine.res_regions}).to_excel(xw, index=False, sheet_name='Residential Regions')
    print('Wrote:', os.path.abspath(args.out))
if __name__ == '__main__':
    main()

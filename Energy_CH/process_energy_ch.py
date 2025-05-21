import pandas as pd
import json


def map_kanton_name(df):
    #ensure kanton names match to geojson exactly

    kan_name = {
        "ZH": "Zürich", "BE": "Bern", "LU": "Luzern", "UR": "Uri",
        "SZ": "Schwyz", "OW": "Obwalden", "NW": "Nidwalden", "GL": "Glarus",
        "ZG": "Zug", "FR": "Fribourg", "SO": "Solothurn", "BS": "Basel-Stadt",
        "BL": "Basel-Landschaft", "SH": "Schaffhausen", "AR": "Appenzell Ausserrhoden", "AI": "Appenzell Innerrhoden",
        "SG": "St. Gallen", "GR": "Graubünden", "AG": "Aargau", "TG": "Thurgau",
        "TI": "Ticino", "VD": "Vaud", "VS": "Valais", "NE": "Neuchâtel",
        "GE": "Genève", "JU": "Jura"
    }

    kan_code = {
        "ZH": 1, "BE": 2, "LU": 3, "UR": 4,
        "SZ": 5, "OW": 6, "NW": 7, "GL": 8,
        "ZG": 9, "FR": 10, "SO": 11, "BS": 12,
        "BL": 13, "SH": 14, "AR": 15, "AI": 16,
        "SG": 17, "GR": 18, "AG": 19, "TG": 20,
        "TI": 21, "VD": 22, "VS": 23, "NE": 24,
        "GE": 25, "JU": 26
    }

    df["kan_code"] = df["canton"].map(kan_code)
    df["kan_name"] = df["canton"].map(kan_name)

    #change column names to include units
    df.rename(columns={"electrical_capacity": "electrical_capacity(MW)",
                        "production": "yearly_production(MWh)"}, inplace=True)
    # convert df["commissioning_date"] to datetime
    df["commissioning_date"] = pd.to_datetime(df["commissioning_date"])
    df["commissioning_year"] = df["commissioning_date"].dt.year

    return df

def create_df_for_plots(df):

    df = map_kanton_name(df)

    total_energy = df.groupby("kan_name")["yearly_production(MWh)"].agg("sum").reset_index(name="total_production(MWh)")
    total_facilities = df.groupby(["kan_name"]).size().reset_index(name= "facilities_count")

    # Calculate number and proportion of energy facilities by sector for each canton
    facility_type = df.groupby(['kan_name', 'energy_source_level_2']).size().reset_index(name='count')
    total_per_canton = facility_type.groupby('kan_name')['count'].transform('sum')
    facility_type['relative_proportion'] = facility_type['count'] / total_per_canton

    # Calculate energy production per sector in each canton
    production_per_sector = df.groupby(['kan_name', 'energy_source_level_2'])["yearly_production(MWh)"].agg("sum").reset_index(name='total_energy_by_sector(MWh)')
    total_energy_per_canton = production_per_sector.groupby('kan_name')['total_energy_by_sector(MWh)'].transform('sum')
    production_per_sector['relative_energy_proportion'] = production_per_sector['total_energy_by_sector(MWh)'] / total_energy_per_canton

    # Merge the data frames
    merged_df = pd.merge(production_per_sector, facility_type, on=["kan_name", "energy_source_level_2"], how="left")

    return merged_df


   
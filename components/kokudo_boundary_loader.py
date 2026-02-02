from typing import Literal, List
import geopandas as gpd
import duckdb

def download_boundary_kokudo(
        con: duckdb.DuckDBPyConnection, 
        area_codes: List[str], 
        boundary_name: Literal["pref", "city"]
    ) -> gpd.GeoDataFrame:
    """
    simplifyされた境界データをダウンロードするための関数
    :param con: DuckDB接続
    :param codes: 都道府県 or 市区町村コードのリスト
    :param boundary_name: クリップに使用する境界名（pref or city）
    :param table_name: クリップ対象のテーブル名
    """

    if boundary_name == "pref":
        boundary_df = con.sql('''
            SELECT
                id,
                pref_name,
                pref_code,
                St_AsText(geom) AS geometry
            FROM  main_intermediate.int_kokudo__map_00_all_2025_pref
            WHERE pref_code IN ({})
        '''.format(', '.join(f"'{code}'" for code in area_codes))).df()
    else:  # boundary_name == "city"
        boundary_df = con.sql('''
            SELECT
                id,
                pref_name,
                pref_code,
                city_name,
                jcode,
                St_AsText(geom) AS geometry
            FROM  main_intermediate.int_kokudo__map_00_all_2025_city
            WHERE jcode IN ({})
        '''.format(', '.join(f"'{code}'" for code in area_codes))).df()
    
    # geometry列をジオメトリ型に変換
    boundary_gdf = gpd.GeoDataFrame(
        boundary_df.drop(columns=["geometry"]),
        geometry=gpd.GeoSeries.from_wkt(boundary_df["geometry"]),
        crs="EPSG:4326"
    )

    return boundary_gdf
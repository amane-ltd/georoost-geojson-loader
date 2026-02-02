from typing import Literal, List
import geopandas as gpd
import duckdb

def download_clipped_geometry(
        con: duckdb.DuckDBPyConnection, 
        area_codes: List[str], 
        boundary_name: Literal["pref", "city"],
        table_name: str
    ) -> gpd.GeoDataFrame:
    """
    クリップした地理空間をダウンロードするための関数
    :param con: DuckDB接続
    :param codes: 都道府県 or 市区町村コードのリスト
    :param boundary_name: クリップに使用する境界名（pref or city）
    :param table_name: クリップ対象のテーブル名
    """
    
    if boundary_name == "pref":
        clipped_df = con.sql('''
            WITH boundary AS (
                SELECT
                    id,
                    pref_name,
                    pref_code,
                    geom
                FROM  main_intermediate.int_kokudo__map_00_all_2025_pref
                WHERE pref_code IN ({})
            )
            SELECT
                t.* EXCLUDE(geom), 
                string_agg(DISTINCT b.pref_name, '・') AS pref_name,
                ST_AsText(ST_Union_Agg(ST_Intersection(t.geom, b.geom))) AS geometry
            FROM {} AS t, boundary AS b
            WHERE ST_Intersects(t.geom, b.geom)
            GROUP BY t.*
        '''.format(', '.join(f"'{code}'" for code in area_codes), table_name)).df()
    else:  # boundary_name == "city"
        clipped_df = con.sql('''
            WITH boundary AS (
                SELECT
                    id,
                    pref_name,
                    pref_code,
                    city_name,
                    jcode,
                    geom
                FROM  main_intermediate.int_kokudo__map_00_all_2025_city
                WHERE jcode IN ({})
            )          
            SELECT
                t.* EXCLUDE(geom), 
                -- string_agg(DISTINCT b.pref_name, '・') AS pref_name,
                -- string_agg(DISTINCT b.city_name, '・') AS city_name,
                ST_AsText(ST_Union_Agg(ST_Intersection(t.geom, b.geom))) AS geometry
            FROM {} AS t, boundary AS b
            WHERE ST_Intersects(t.geom, b.geom)
            GROUP BY t.*
        '''.format(', '.join(f"'{code}'" for code in area_codes), table_name)).df()
    
    # geometry列をジオメトリ型に変換
    clipped_gdf = gpd.GeoDataFrame(
        clipped_df.drop(columns=["geometry"]),
        geometry=gpd.GeoSeries.from_wkt(clipped_df["geometry"]),
        crs="EPSG:4326"
    )

    return clipped_gdf


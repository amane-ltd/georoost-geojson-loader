import streamlit as st
import pydeck as pdk
import geopandas as gpd
import pandas as pd

from components.connect_motherduck import get_md_con_georoost
from components.load_page import load_page_config
from components.cilpped_geometry_loader import download_clipped_geometry
from components.kokudo_boundary_loader import download_boundary_kokudo


# =======================
# === Streamlit Head ====
# =======================


# データベースのパス
con = get_md_con_georoost()

# ページ設定の読み込み
load_page_config()

# 都道府県のリストを取得、セッションステートに保存
if 'pref_dict' in st.session_state:
    pref_dict = st.session_state['pref_dict']
else:
    pref_dict = pd.read_csv('seeds/pref_code.csv', dtype={'pref_code': str, 'pref_name': str}).set_index('pref_name')['pref_code'].to_dict()
    st.session_state['pref_dict'] = pref_dict

# 市区町村のリストを取得、セッションステートに保存
if 'city_dict' in st.session_state:
    city_dict = st.session_state['city_dict']
else:
    city_dict = pd.read_csv('seeds/city_code.csv', dtype={'jcode': str, 'city_name': str}).set_index('city_name')['jcode'].to_dict()
    st.session_state['city_dict'] = city_dict

# =======================
# === Streamlit Body ====
# =======================

# GeoJSONとして保存するテーブルの選択
st.title("ベース地図のためのGeoJSON保存")
st.text("処理に時間がかかる場合があります。")

# 地理院地図の埋め込み
with st.expander("市区町村境界を確認する", expanded=False):
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="UTF-8">
    <title>GSI Tiles on Leaflet</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.6.0/dist/leaflet.css"
      integrity="sha512-xwE/Az9zrjBIphAcBb3F6JVqxf46+CDLwfLMHloNu6KEQCAWi6HcDUbeOfBIptF7tcCzusKFjFw2yuvEpDL9wQ=="
      crossorigin=""/>
    <script src="https://unpkg.com/leaflet@1.6.0/dist/leaflet.js"
      integrity="sha512-gZwIG9x3wUXg2hdXF6+rVkLF/0Vi9U8D2Ntg4Ga5I5BZpVkVxlJWbSQtXPSiUTtC0TjtGOmxa1AJPuV0CPthew=="
      crossorigin=""></script>
    
    <style>
      body {padding: 0; margin: 0}
      html, body, #map {height: 100%; width: 100%;}
    </style>
    </head>
    
    <body>
    <div id="map"></div>
    <script>
    var map = L.map('map');
    
    L.tileLayer('https://cyberjapandata.gsi.go.jp/xyz/blank/{z}/{x}/{y}.png', {
      attribution: "<a href='https://maps.gsi.go.jp/development/ichiran.html' target='_blank'>地理院タイル</a>"
    }).addTo(map);
    
    map.setView([35.3622222, 138.7313889], 5);
    </script>
    </body>
    </html>
    """
    st.components.v1.html(html_content, height=600)


# 都道府県の選択
pref_levels = st.multiselect(
    "都道府県名を選択してください", 
    pref_dict.keys(), 
    format_func=lambda x: f"{x} ({pref_dict[x]})"
)
if pref_levels:
    pref_code = [pref_dict[x] for x in pref_levels]

# 市区町村の選択
if pref_levels:
    filtered_city_dict = {k: v for k, v in city_dict.items() if v[:2] in pref_code}
else:
    filtered_city_dict = city_dict
city_levels = st.multiselect(
    "市区町村名を選択してください", 
    filtered_city_dict.keys(),
    format_func=lambda x: f"{x} ({filtered_city_dict[x]})"
)
if city_levels:
    city_code = [city_dict[x] for x in city_levels]


# データ取得ボタン
if st.button("データを取得") and (pref_levels or city_levels):
    # 鉄道駅データを取得
    query_df = con.sql('''
        SELECT
            * EXCLUDE(geom),
            St_AsText(geom) AS geometry
        FROM main_jpn.jpn_kokudo__station_info_kepler
        WHERE {}
    '''.format(
        'SUBSTRING(jcode, 1, 5) IN ({})'.format(
            ', '.join(f"'{code}'" for code in city_code)
        ) if city_levels else 'SUBSTRING(pref_code, 1, 2)  IN ({})'.format(
            ', '.join(f"'{code}'" for code in pref_code)
        )
    )).df()
    clipped_station_gdf = gpd.GeoDataFrame(
        query_df.drop(columns=['geometry']),
        geometry=gpd.GeoSeries.from_wkt(query_df['geometry']),
        crs="EPSG:4326"
    )
    clipped_station_gdf['tooltip'] = "鉄道駅"
    st.session_state['clipped_station_gdf'] = clipped_station_gdf

    # 鉄道路線データを取得
    query_df = con.sql('''
        SELECT
            * EXCLUDE(geom),
            St_AsText(geom) AS geometry
        FROM main_jpn.jpn_kokudo__railroad_section_kepler
        WHERE {}
    '''.format(
        'SUBSTRING(jcode, 1, 5) IN ({})'.format(
            ', '.join(f"'{code}'" for code in city_code)
        ) if city_levels else 'SUBSTRING(pref_code, 1, 2)  IN ({})'.format(
            ', '.join(f"'{code}'" for code in pref_code)
        )
    )).df()
    clipped_ralisection_gdf = gpd.GeoDataFrame(
        query_df.drop(columns=['geometry']),
        geometry=gpd.GeoSeries.from_wkt(query_df['geometry']),
        crs="EPSG:4326"
    )
    clipped_ralisection_gdf['tooltip'] = "鉄道路線"
    st.session_state['clipped_ralisection_gdf'] = clipped_ralisection_gdf

    # バス停データを取得
    query_df = con.sql('''
        SELECT
            * EXCLUDE(geom),
            St_AsText(geom) AS geometry
        FROM main_jpn.jpn_kokudo__bus_stop_kepler
        WHERE {}
    '''.format(
        'SUBSTRING(jcode, 1, 5) IN ({})'.format(
            ', '.join(f"'{code}'" for code in city_code)
        ) if city_levels else 'SUBSTRING(pref_code, 1, 2)  IN ({})'.format(
            ', '.join(f"'{code}'" for code in pref_code)
        )
    )).df()
    clipped_busstop_gdf = gpd.GeoDataFrame(
        query_df.drop(columns=['geometry']),
        geometry=gpd.GeoSeries.from_wkt(query_df['geometry']),
        crs="EPSG:4326"
    )
    clipped_busstop_gdf['tooltip'] = "バス停"
    st.session_state['clipped_busstop_gdf'] = clipped_busstop_gdf

    # バス路線データを取得
    query_df = con.sql('''
        SELECT
            * EXCLUDE(geom),
            St_AsText(geom) AS geometry
        FROM main_jpn.jpn_kokudo__bus_line_kepler
        WHERE {}
    '''.format(
        'SUBSTRING(jcode, 1, 5) IN ({})'.format(
            ', '.join(f"'{code}'" for code in city_code)
        ) if city_levels else 'SUBSTRING(pref_code, 1, 2)  IN ({})'.format(
            ', '.join(f"'{code}'" for code in pref_code)
        )
    )).df()
    clipped_busline_gdf = gpd.GeoDataFrame(
        query_df.drop(columns=['geometry']),
        geometry=gpd.GeoSeries.from_wkt(query_df['geometry']),
        crs="EPSG:4326"
    )
    clipped_busline_gdf['tooltip'] = "バス路線"
    st.session_state['clipped_busline_gdf'] = clipped_busline_gdf

    # メッシュ人口データを取得
    clipped_meshpop_gdf = download_clipped_geometry(
        con=con, 
        area_codes=city_code if city_levels else pref_code, 
        boundary_name="city" if city_levels else "pref",
        table_name="main_jpn.jpn_census2020_mesh5__all_kepler"
    )
    clipped_meshpop_gdf['tooltip'] = "メッシュ人口"
    clipped_meshpop_gdf = clipped_meshpop_gdf
    st.session_state['clipped_meshpop_gdf'] = clipped_meshpop_gdf

    # 町丁字人口データを取得
    query_df = con.sql('''
        SELECT
            * EXCLUDE(geom),
            St_AsText(geom) AS geometry
        FROM main_jpn.jpn_census2020_town__map_with_all_kepler
        WHERE {}
    '''.format(
        'SUBSTRING(KEY_CODE, 1, 5) IN ({})'.format(
            ', '.join(f"'{code}'" for code in city_code)
        ) if city_levels else 'SUBSTRING(KEY_CODE, 1, 2)  IN ({})'.format(
            ', '.join(f"'{code}'" for code in pref_code)
        )
    )).df()
    clipped_mappop_gdf = gpd.GeoDataFrame(
        query_df.drop(columns=['geometry']),
        geometry=gpd.GeoSeries.from_wkt(query_df['geometry']),
        crs="EPSG:4326"
    )
    clipped_mappop_gdf['tooltip'] = "町丁字人口"
    st.session_state['clipped_mappop_gdf'] = clipped_mappop_gdf

    # 行政区域データを取得
    boundary_gdf = download_boundary_kokudo(
        con=con, 
        area_codes=city_code if city_levels else pref_code, 
        boundary_name="city" if city_levels else "pref"
    )
    boundary_gdf['tooltip'] = "行政区域データ"
    st.session_state['boundary_gdf'] = boundary_gdf
    
    # 中心座標を取得
    st.session_state["center_lat"] = boundary_gdf.geometry.to_crs('EPSG:6674').centroid.to_crs('EPSG:4326').y.mean()
    st.session_state["center_lon"] = boundary_gdf.geometry.to_crs('EPSG:6674').centroid.to_crs('EPSG:4326').x.mean()

# データ表示・ダウンロードセクション
if ('clipped_station_gdf' in st.session_state) \
    and ('clipped_ralisection_gdf' in st.session_state) \
    and ('boundary_gdf' in st.session_state):

    boundary_gdf = st.session_state['boundary_gdf']
    clipped_station_gdf = st.session_state['clipped_station_gdf']
    clipped_ralisection_gdf = st.session_state['clipped_ralisection_gdf']
    clipped_busstop_gdf = st.session_state['clipped_busstop_gdf']
    clipped_busline_gdf = st.session_state['clipped_busline_gdf']
    clipped_meshpop_gdf = st.session_state['clipped_meshpop_gdf']
    clipped_mappop_gdf = st.session_state['clipped_mappop_gdf']

    # まとめてzipでダウンロード
    st.markdown("### まとめてGeoJSONファイルをダウンロード")
    zip_filename = f"ベースマップ_{'_'.join(city_levels) if city_levels else '_'.join(pref_levels)}.zip"
    with st.spinner("GeoJSONファイルを生成中..."):
        import io
        import zipfile
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED) as zip_file:
            # 鉄道駅
            station_geojson = clipped_station_gdf.to_json()
            zip_file.writestr(f"鉄道駅.geojson", station_geojson)
            # 鉄道路線
            rail_section_geojson = clipped_ralisection_gdf.to_json()
            zip_file.writestr(f"鉄道路線.geojson", rail_section_geojson)
            # バス停
            bus_stop_geojson = clipped_busstop_gdf.to_json()
            zip_file.writestr(f"バス停.geojson", bus_stop_geojson)
            # バス路線
            bus_line_geojson = clipped_busline_gdf.to_json()
            zip_file.writestr(f"バス路線.geojson", bus_line_geojson)
            # メッシュ人口
            meshpop_geojson = clipped_meshpop_gdf.to_json()
            zip_file.writestr(f"メッシュ人口.geojson", meshpop_geojson)
            # 町丁字人口
            mappop_geojson = clipped_mappop_gdf.to_json()
            zip_file.writestr(f"町丁字人口.geojson", mappop_geojson)
            # 行政区域
            boundary_geojson = boundary_gdf.to_json()
            zip_file.writestr(f"行政区域.geojson", boundary_geojson)
        zip_buffer.seek(0)
        st.download_button(
            label="GeoJSONファイルをまとめてダウンロード (zip形式)",
            data=zip_buffer,
            file_name=zip_filename,
            mime="application/zip",
            width='stretch'
        )
    # 個別にGeoJSONでダウンロード
    st.markdown("### 各データをGeoJSONファイルでダウンロード")
    # 鉄道駅データのダウンロード
    clipped_station_name = f"鉄道駅_{'_'.join(city_levels) if city_levels else '_'.join(pref_levels)}"
    st.download_button(
        label="鉄道駅をGeoJSONでダウンロード",
        data=clipped_station_gdf.to_json(),
        file_name=f"{clipped_station_name}.geojson",
        mime="application/geo+json",
        width='stretch'
    )
    # 鉄道路線データのダウンロード
    clipped_rail_section_name = f"鉄道路線_{'_'.join(city_levels) if city_levels else '_'.join(pref_levels)}"
    st.download_button(
        label="鉄道路線をGeoJSONでダウンロード",
        data=clipped_ralisection_gdf.to_json(),
        file_name=f"{clipped_rail_section_name}.geojson",
        mime="application/geo+json",
        width='stretch'
    )
    # バス停データのダウンロード
    clipped_bus_stop_name = f"バス停_{'_'.join(city_levels) if city_levels else '_'.join(pref_levels)}"
    st.download_button(
        label="バス停をGeoJSONでダウンロード",
        data=clipped_busstop_gdf.to_json(),
        file_name=f"{clipped_bus_stop_name}.geojson",
        mime="application/geo+json",
        width='stretch'
    )
    # バス路線データのダウンロード
    clipped_bus_line_name = f"バス路線_{'_'.join(city_levels) if city_levels else '_'.join(pref_levels)}"
    st.download_button(
        label="バス路線をGeoJSONでダウンロード",
        data=clipped_busline_gdf.to_json(),
        file_name=f"{clipped_bus_line_name}.geojson",
        mime="application/geo+json",
        width='stretch'
    )
    # メッシュ人口データのダウンロード
    clipped_meshpop_name = f"メッシュ人口_{'_'.join(city_levels) if city_levels else '_'.join(pref_levels)}"
    st.download_button(
        label="メッシュ人口をGeoJSONでダウンロード",
        data=clipped_meshpop_gdf.to_json(),
        file_name=f"{clipped_meshpop_name}.geojson",
        mime="application/geo+json",
        width='stretch'
    )
    # 町丁字人口データのダウンロード
    clipped_mappop_name = f"町丁字人口_{'_'.join(city_levels) if city_levels else '_'.join(pref_levels)}"
    st.download_button(
        label="町丁字人口をGeoJSONでダウンロード",
        data=clipped_mappop_gdf.to_json(),
        file_name=f"{clipped_mappop_name}.geojson",
        mime="application/geo+json",
        width='stretch'
    )
    # 行政区域データのダウンロード
    boundary_name = f"行政区域_{'_'.join(city_levels) if city_levels else '_'.join(pref_levels)}"
    st.download_button(
        label="行政区域をGeoJSONでダウンロード",
        data=boundary_gdf.to_json(),
        file_name=f"{boundary_name}.geojson",
        mime="application/geo+json",
        width='stretch'
    )
    
    
    # 地図表示のための中心座標取得
    center_lat = st.session_state['center_lat']
    center_lon = st.session_state['center_lon']
    
    
    # PyDeckで地図を表示
    st.markdown(f"### ベース地図プレビュー")
    station_layer = pdk.Layer(
        "GeoJsonLayer",
        data=clipped_station_gdf,
        pickable=True,
        stroked=True,
        filled=False,
        line_width_min_pixels=4,
        get_line_color=[25, 100, 25, 200], # 深緑色
    )
    rail_section_layer = pdk.Layer(
        "GeoJsonLayer",
        data=clipped_ralisection_gdf,
        pickable=True,
        stroked=True,
        filled=False,
        line_width_min_pixels=3,
        get_line_color=[152, 251, 152, 200], # 若草色
    )
    bus_stop_layer = pdk.Layer(
        "GeoJsonLayer",
        data=clipped_busstop_gdf,
        pickable=True,
        stroked=True,
        filled=False,
        line_width_min_pixels=4,
        get_line_color=[0, 0, 255, 200], # 青色
    )
    bus_line_layer = pdk.Layer(
        "GeoJsonLayer",
        data=clipped_busline_gdf,
        pickable=True,
        stroked=True,
        filled=False,
        line_width_min_pixels=2,
        get_line_color=[64, 224, 208, 200], # ターコイズブルー
    )
    meshpop_layer = pdk.Layer(
        "GeoJsonLayer",
        data=clipped_meshpop_gdf,
        pickable=True,
        stroked=True,
        filled=False,
        get_line_color=[255, 140, 0, 200], # 灰色
        line_width_min_pixels=1,
    )
    mappop_layer = pdk.Layer(
        "GeoJsonLayer",
        data=clipped_mappop_gdf,
        pickable=True,
        stroked=True,
        filled=False,
        get_line_color=[255, 140, 0, 200], # 灰色
        line_width_min_pixels=1,
    )
    boundary_layer = pdk.Layer(
        "GeoJsonLayer",
        data=boundary_gdf,
        pickable=True,
        stroked=True,
        filled=False,
        line_width_min_pixels=4,
        get_line_color=[0, 0, 0, 255], # 黒色
    )
    initial_view_state = pdk.ViewState(
        latitude=center_lat,
        longitude=center_lon,
        zoom=11,
        pitch=0,
    )
    deck = pdk.Deck(
        layers=[
            boundary_layer, 
            rail_section_layer, 
            station_layer, 
            bus_line_layer, 
            bus_stop_layer,
            meshpop_layer,
            mappop_layer
        ],
        tooltip={"text": "レイヤー名: {tooltip}"},
        initial_view_state=initial_view_state,
        map_style='light'
    )
    st.pydeck_chart(deck)

    

# =======================
# === Streamlit Foot ====
# =======================

# 出典情報
st.markdown("<div style='text-align: right; color: #666; font-size: 0.8em;'>【出典】国土数値情報", unsafe_allow_html=True)

# ホームに戻るボタン
st.markdown("---")  # 区切り線
if st.button("⬅ Back to Home"): st.switch_page("pages/home.py")


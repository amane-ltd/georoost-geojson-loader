import os
import duckdb
import streamlit as st  

# ===== MotherDuck 接続まわり =====
@st.cache_resource
def get_md_con_georoost():
    """
    MotherDuckへの接続を確立する。
    """
    # DuckDB データベースのパス 
    try :
        MOTHERDUCK_TOKEN = os.environ['MOTHERDUCK_TOKEN']
    except KeyError:
        MOTHERDUCK_TOKEN = st.secrets["MOTHERDUCK_TOKEN"]
    DUCKDB_PATH = f"md:georoost-dev?motherduck_token={MOTHERDUCK_TOKEN}"
    con = duckdb.connect(DUCKDB_PATH, read_only=True)
    con.sql('INSTALL spatial;')
    con.sql('LOAD spatial;')
    con.sql('INSTALL motherduck;')
    con.sql('LOAD motherduck;')
    return con
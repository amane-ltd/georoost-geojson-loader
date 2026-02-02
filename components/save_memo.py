import os
import duckdb
import streamlit as st
from datetime import datetime

st.set_page_config(page_title="Memo with MotherDuck", layout="wide")

# ===== MotherDuck 接続まわり =====

@st.cache_resource
def get_md_con_debug():
    """
    MotherDuckへの接続を確立し、メモ用テーブルがなければ作成する。
    """
    # DuckDB データベースのパス
    try :
        MOTHERDUCK_TOKEN = os.environ['MOTHERDUCK_TOKEN']
    except KeyError:
        MOTHERDUCK_TOKEN = st.secrets["MOTHERDUCK_TOKEN"]
    DUCKDB_PATH = f"md:debug?motherduck_token={MOTHERDUCK_TOKEN}"
    conn = duckdb.connect(DUCKDB_PATH, read_only=False)

    # メモ用テーブル作成（なければ）
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS main.memo_log (
            name        TEXT,
            identifier  TEXT,
            mail        TEXT,
            created_at  TIMESTAMPTZ,
            memo_text   TEXT
        )
        """
    )
    # IDの生成方法は環境に合わせて調整してください（簡略化したい場合はid無しでもOK）

    return conn


def save_memo_to_motherduck(memo_text: str):
    """
    メモをMotherDuck上のmemo_logテーブルに保存する。
    """
    if not memo_text.strip():
        # 空文字やスペースだけのときは何もしない
        return False, "メモが空です。"

    con_debug = get_md_con_debug()
    created_at = datetime.now()

    con_debug.execute(
        """
        INSERT INTO main.memo_log (name, identifier, mail, created_at, memo_text)
        VALUES (?, ?, ?, ?, ?)
        """,
        [st.user.name, st.user.sub, st.user.email, created_at, memo_text],
    )
    return True, f"ご意見ありがとうございました（{created_at}）。"

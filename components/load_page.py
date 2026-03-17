import streamlit as st
from PIL import Image

# ページ設定を読み込む関数
def load_page_config():
    # Streamlitのページ設定
    im = Image.open("./static/images/GeoRoost_favicon.ico")
    st.set_page_config(
        page_title="GeoRoost", 
        page_icon=im,
        layout="wide", 
        initial_sidebar_state="expanded",
    )

    # ロゴの設定
    st.logo(
        "./static/images/GeoRoost_Sidebar.png", 
        size="large",
        icon_image="./static/images/GeoRoost_favicon.ico"
    )

    # サイドバーに株式会社AMANEの会社紹介を追加
    with st.sidebar.expander("株式会社AMANEについて", expanded=False):
        st.markdown(
        """
        **HP**

        [https://amane.ltd/](https://amane.ltd/)
                    
        **所在地**

        〒105-0012 
        東京都港区芝大門一丁目2番14号
        
        **事業内容**
        - アーバンテック事業開発支援
        - アーバンテック自社開発
        
        [お問合せはこちら](https://amane.ltd/contact/)
        """)

    # サイドバーに権利表記を追加し、リンクを設定
    st.sidebar.markdown(
        """
        <div style="text-align: center; font-size: 12px; color: gray;">
            © 2026 <a href= "https://amane.ltd/" >株式会社AMANE</a>. All rights reserved.
        </div>
        """, 
        unsafe_allow_html=True
    )

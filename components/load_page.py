import streamlit as st
from PIL import Image

from components.save_memo import save_memo_to_motherduck

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
        st.markdown("""
        **Mission**  
        テクノロジーと現場、さまざまなステークホルダーをつなげ、価値がめぐる仕組みを創出し、豊かな都市生活を実現する
        
        **事業内容**
        - [アーバンテック事業開発支援](https://amane.ltd/service/urbantech_business-development_support/)
        - [アーバンテック自社開発](https://amane.ltd/service/urbantech_in-house-development/)
        
        [お問合せはこちら](https://amane.ltd/contact/)
        """)


    # サイドバーにフィードバックフォームを追加
    with st.sidebar.expander("ご意見・感想", expanded=False):
        with st.form("sidebar_memo_form"):
            memo = st.text_area(
                "※送信された内容は開発チームで確認し、今後の改善に役立てます。",
                height=250
            )
            save_clicked = st.form_submit_button("送信")
        if save_clicked:
            ok, msg = save_memo_to_motherduck(
                memo_text=memo
            )
            if ok:
                st.success(msg)
            else:
                st.error(msg)

    # サイドバーに権利表記を追加し、リンクを設定
    st.sidebar.markdown(
        """
        <div style="text-align: center; font-size: 12px; color: gray;">
            © 2026 <a href= "https://amane.ltd/" >株式会社AMANE</a>. All rights reserved.
        </div>
        """, 
        unsafe_allow_html=True
    )

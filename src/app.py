# app.py
import streamlit as st
import asyncio
import re
from main import search_stream

# ---- helpers ----
def make_clickable(line: str) -> str:
    """Find all http/https URLs and wrap them in <a> tags"""
    return re.sub(
        r'(https?://[^\s]+)',
        r'<a href="\1" target="_blank" style="color:#1f77b4;">\1</a>',
        line
    )

# ---- Page Config ----
st.set_page_config(
    page_title="OP",
    page_icon="🦦",
    layout="centered",
)

# ---- Header ----
st.markdown(
    """
    <h1 style='text-align: center; margin-bottom: 0;'>Open Knowledge 🦦</h1>
    <p style='text-align: center; color: gray; font-size: 1.1rem;'>
        OP is a semantic discovery engine for quality learning resources.
    </p>
    """,
    unsafe_allow_html=True,
)


# ---- Query Input ----
col1, col2 = st.columns([8, 1])

with col1:
    query = st.text_input(
        "What would you like to learn?",
        placeholder="Linear algebra",
        label_visibility="collapsed",
    )

with col2:
    send_clicked = st.button("➤", help="Search")

search_triggered = query and (send_clicked or query)

# ---- Action ----
if search_triggered:
    st.markdown("---")

    async def run_search():

        with st.container(border=True):
            st.markdown("#### WikiMedia")
            wiki_placeholder = st.empty()
        with st.container(border=True):
            st.markdown("#### HackerNews")
            hn_placeholder = st.empty()
        with st.container(border=True):
            st.markdown("#### Reddit")
            reddit_placeholder = st.empty()

        placeholders = {
            "WikiMedia": wiki_placeholder,
            "HackerNews": hn_placeholder,
            "Reddit": reddit_placeholder,
        }

        async for source, lines in search_stream(query):
            html_content = "<br>".join(
                f"<div style='margin-bottom: 1em;'>"
                + make_clickable(line.replace("\n", "<br>"))
                + "</div>"
                for line in lines
            )
            placeholders[source].markdown(html_content, unsafe_allow_html=True)

    asyncio.run(run_search())

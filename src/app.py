import streamlit as st
import asyncio
from typing import List

# internal lib
from main import search


st.title("Learn and read, Lou Reed!")
st.markdown("Semantic discovery engine for quality learning resources")

query: str = st.text_input(
    "What do you want to learn?",
    placeholder="e.g. linear algebra, machine learning, quantum physics..."
)

if st.button("🦦 Search", type="primary") or query:
    if query:
        with st.spinner("Cooking..."):
            res = asyncio.run(search(query))
            st.markdown("---")
            lines: List[str] = res.split("\n")
            for line in lines:
                st.markdown("\t" + line)
    else:
        st.warning("Please enter a topic search. Don't know where to start? Why don't you try with `linear algebra`!")

st.markdown("---")
st.markdown("*Powered by semantic search across trusted learning platforms*")
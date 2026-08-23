import streamlit as st

st.set_page_config(
    page_title="Recipe Book",
    page_icon="🍽️",
    layout="wide"
)

pages = [
    st.Page("home/home.py", title="Home"),
    st.Page("profile_manager/profile_manager.py", title="Profile Manager"),
    st.Page("recipe_manager/recipe_manager.py", title="Recipe Manager"),
]

pg = st.navigation(pages, position="top")
pg.run()
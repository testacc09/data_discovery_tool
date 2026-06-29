import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
import streamlit as st
import pandas as pd
from connectors.sqlite_conn import SQLiteConnector
from connectors.csv_conn import CSVFolderConnector
from connectors.http_conn import HTTPAPIConnector
from search.engine import SearchEngine

st.set_page_config(page_title="Инструмент поиска данных", layout="wide")

if "search_query" not in st.session_state:
    st.session_state["search_query"] = ""
if "cached_previews" not in st.session_state:
    st.session_state["cached_previews"] = {}

async def index_all(engine, connectors_pool):
    for conn in connectors_pool.values():
        await engine.index_source(conn)

@st.cache_resource
def get_indexed_search_engine():
    engine = SearchEngine()
    base_data_dir = "./data_storage"
    csv_dir = os.path.join(base_data_dir, "csv_sources")
    api_dir = os.path.join(base_data_dir, "api_responses")
    db_dir = os.path.join(base_data_dir, "databases")
    connectors_pool = {}

    if os.path.exists(csv_dir):
        connectors_pool["csv_source"] = CSVFolderConnector("csv_source", csv_dir)

    if os.path.exists(api_dir):
        for json_file in os.listdir(api_dir):
            if json_file.endswith(".json") and json_file != "embeddings_cache.json":
                file_id = f"http_{json_file.split('.')[0]}"
                abs_json_path = os.path.abspath(os.path.join(api_dir, json_file))
                connectors_pool[file_id] = HTTPAPIConnector(file_id, f"file://{abs_json_path}")

    if os.path.exists(db_dir):
        for db_file in os.listdir(db_dir):
            if db_file.endswith(".db"):
                file_id = f"sqlite_{db_file.split('.')[0]}"
                db_path = os.path.join(db_dir, db_file)
                connectors_pool[file_id] = SQLiteConnector(file_id, db_path)

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    if loop.is_running():
        future = asyncio.run_coroutine_threadsafe(index_all(engine, connectors_pool), loop)
        future.result()
    else:
        loop.run_until_complete(index_all(engine, connectors_pool))

    return engine, connectors_pool

engine, connectors_pool = get_indexed_search_engine()

st.title("🔍 Инструмент поиска данных")

search_col, btn_col = st.columns([5, 1])

with search_col:
    query_input = st.text_input(
        label="Поле поиска",
        value=st.session_state["search_query"],
        label_visibility="collapsed",
        key="main_search_input",
    )

with btn_col:
    submit_button = st.button(
        label="Найти",
        use_container_width=True,
        key="main_search_btn",
    )

query_changed = query_input != st.session_state["search_query"]

if submit_button or (query_input and query_changed):
    st.session_state["search_query"] = query_input
    st.session_state["cached_previews"] = {}
    st.rerun()

def fetch_table_data(source_id, path, pull_all=False):
    if source_id in connectors_pool:
        try:
            fetch_limit = 10000000 if pull_all else 100
            preview_data = connectors_pool[source_id].get_table_preview(
                path,
                limit=fetch_limit,
            )
            if preview_data is not None:
                if not isinstance(preview_data, pd.DataFrame):
                    df = pd.DataFrame(preview_data)
                else:
                    df = preview_data.copy()
                if not df.empty:
                    df.index = range(1, len(df) + 1)
                    df.index.name = "index"
                    return df.reset_index()
                return pd.DataFrame()
        except Exception:
            return None
    return None

def render_search_results(current_query):
    results = engine.search(current_query, limit=100)
    
    if not results:
        st.info("По запросу ничего не найдено.")
        return

    st.subheader("Результаты поиска")
    for res in results:
        st.markdown("<div style='border-bottom: 1px solid rgba(49, 51, 63, 0.2); padding-bottom: 20px; margin-bottom: 20px;'>", unsafe_allow_html=True)
        with st.container():
            col1, col2, col3 = st.columns([1, 4, 2])
            with col1:
                st.markdown(f"**[{'ТАБЛИЦА' if res['type'] == 'table' else 'КОЛОНКА'}]**")
            with col2:
                sid = res['sourceId']
                if sid.startswith("sqlite_"):
                    display_source = sid.replace("sqlite_", "") + ".db"
                elif sid.startswith("http_"):
                    display_source = sid.replace("http_", "") + ".json"
                elif sid == "csv_source":
                    display_source = os.path.basename(res['path'])
                else:
                    display_source = sid
                st.markdown(f"Путь: `{res['path']}` Источник: `{display_source}`")
                st.caption(f"Метаданные: {res['metadata']}")
            with col3:
                st.markdown(f"**Общий балл релевантности: {res['score']:.2f}**")
                st.caption(f"📜 Семантика: {res['semantic_score']:.2f} | 🔑 Ключевые слова: {res['keyword_score']:.1f}")
            if res["type"] == "table":
                with st.expander("Предпросмотр строк", expanded=False):
                    source_id = res["sourceId"]
                    path = res["path"]
                    total_rows = res["metadata"].get("row_count", 0)
                    show_all = False
                    if total_rows > 100:
                        show_all = st.checkbox(f"Загрузить все строки (Всего: {total_rows})", key=f"chk_{source_id}_{path}")
                    cache_key = f"{source_id}_{path}_{'all' if show_all else 'pvw'}"
                    if cache_key not in st.session_state["cached_previews"]:
                        st.session_state["cached_previews"][cache_key] = fetch_table_data(source_id, path, pull_all=show_all)
                    df = st.session_state["cached_previews"].get(cache_key)
                    if isinstance(df, pd.DataFrame) and not df.empty:
                        st.dataframe(df if show_all else df.head(100), hide_index=True)
                        if not show_all and total_rows > 100:
                            st.caption(f"Отображены первые 100 из {total_rows}")
                    elif df is not None:
                        st.warning("Таблица пуста.")
        st.markdown("</div>", unsafe_allow_html=True)

if st.session_state["search_query"]:
    with st.container(key=f"search_res_{st.session_state['search_query']}"):
        render_search_results(st.session_state["search_query"])

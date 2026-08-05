"""
DataLens — Streamlit Frontend
Calls the deployed DataLens FastAPI backend to upload, clean, analyze,
and visualize CSV data.
"""
 
import streamlit as st
import requests
import base64
 
st.set_page_config(page_title="DataLens", layout="wide")
 
# --- Config ---
DEFAULT_API_URL = "https://datalens-api-k9tu.onrender.com"
 
if "api_url" not in st.session_state:
    st.session_state.api_url = DEFAULT_API_URL
if "dataset_id" not in st.session_state:
    st.session_state.dataset_id = None
if "filename" not in st.session_state:
    st.session_state.filename = None
 
st.sidebar.title("DataLens")
st.session_state.api_url = st.sidebar.text_input("Backend API URL", value=st.session_state.api_url)
API_URL = st.session_state.api_url.rstrip("/")
 
st.sidebar.markdown("---")
 
# --- Upload ---
st.sidebar.subheader("1. Upload a CSV")
uploaded_file = st.sidebar.file_uploader("Choose a CSV file", type=["csv"])
 
if uploaded_file is not None and st.sidebar.button("Upload"):
    with st.spinner("Uploading..."):
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "text/csv")}
        try:
            resp = requests.post(f"{API_URL}/upload/", files=files, timeout=60)
            if resp.status_code == 200:
                data = resp.json()
                st.session_state.dataset_id = data["dataset_id"]
                st.session_state.filename = data["filename"]
                st.sidebar.success(f"Uploaded: {data['filename']} ({data['rows']} rows, {data['columns']} cols)")
            else:
                st.sidebar.error(f"Upload failed: {resp.status_code} — {resp.text}")
        except requests.exceptions.RequestException as e:
            st.sidebar.error(f"Could not reach backend: {e}")
 
st.sidebar.markdown("---")
 
if st.session_state.dataset_id:
    st.sidebar.success(f"Active dataset: {st.session_state.filename}")
    st.sidebar.caption(f"dataset_id: {st.session_state.dataset_id}")
else:
    st.sidebar.info("Upload a file to get started.")
 
# --- Main area ---
st.title("DataLens — CSV Analytics Platform")
st.caption("A FastAPI + Pandas + Matplotlib/Seaborn backend, wrapped in a Streamlit frontend.")
 
if not st.session_state.dataset_id:
    st.info("👈 Upload a CSV from the sidebar to begin.")
    st.stop()
 
dataset_id = st.session_state.dataset_id
 
 
def call_api(endpoint, params=None, method="post"):
    """Helper to call a backend endpoint using the stored dataset_id."""
    params = params or {}
    params["dataset_id"] = dataset_id
    try:
        resp = requests.post(f"{API_URL}{endpoint}", params=params, timeout=60)
        if resp.status_code == 200:
            return resp.json(), None
        return None, f"{resp.status_code}: {resp.text}"
    except requests.exceptions.RequestException as e:
        return None, str(e)
 
 
def show_chart(base64_str, caption=""):
    """Decode and display a base64 PNG returned by the backend."""
    image_bytes = base64.b64decode(base64_str)
    st.image(image_bytes, caption=caption, use_container_width=True)
 
 
tab_overview, tab_clean, tab_visual, tab_analytics, tab_export = st.tabs(
    ["Overview", "Clean Data", "Visualize", "Analytics", "Export"]
)
 
# --- Overview tab ---
with tab_overview:
    col1, col2 = st.columns(2)
 
    with col1:
        if st.button("Show Missing Values"):
            data, err = call_api("/upload/missing-values")
            if err:
                st.error(err)
            else:
                st.json(data)
 
        if st.button("Show Data Types"):
            data, err = call_api("/upload/data-types")
            if err:
                st.error(err)
            else:
                st.json(data)
 
    with col2:
        if st.button("Show Basic Statistics"):
            data, err = call_api("/upload/statistics")
            if err:
                st.error(err)
            else:
                st.dataframe(data)
 
# --- Clean Data tab ---
with tab_clean:
    st.subheader("Drop Missing Values")
    drop_col = st.text_input("Column to check (leave blank for all columns)", key="drop_col")
    if st.button("Drop Missing Rows"):
        data, err = call_api("/upload/drop-missing", {"column": drop_col or None})
        if err:
            st.error(err)
        else:
            st.json(data)
 
    st.markdown("---")
    st.subheader("Fill Missing Values")
    fill_col = st.text_input("Column", value="Age", key="fill_col")
    fill_strategy = st.selectbox("Strategy", ["mean", "median", "mode"])
    if st.button("Fill Missing Values"):
        data, err = call_api("/upload/fill-missing", {"column": fill_col, "strategy": fill_strategy})
        if err:
            st.error(err)
        else:
            st.json(data)
 
    st.markdown("---")
    st.subheader("Duplicates")
    dup_cols = st.text_input("Columns to check (comma-separated, blank = all)", key="dup_cols")
    if st.button("Check / Remove Duplicates"):
        data, err = call_api("/upload/duplicates", {"columns": dup_cols or None})
        if err:
            st.error(err)
        else:
            st.json(data)
 
    st.markdown("---")
    st.subheader("Select Columns")
    sel_cols = st.text_input("Columns (comma-separated)", value="Age,Fare,Survived", key="sel_cols")
    if st.button("Preview Selected Columns"):
        data, err = call_api("/upload/select-columns", {"columns": sel_cols})
        if err:
            st.error(err)
        else:
            st.dataframe(data.get("preview", []))
 
# --- Visualize tab ---
with tab_visual:
    chart_type = st.selectbox(
        "Chart type",
        ["Histogram", "Boxplot", "Scatter Plot", "Correlation Heatmap", "Pie Chart", "Bar Chart", "Line Chart"],
    )
 
    if chart_type == "Histogram":
        col = st.text_input("Column", value="Age", key="hist_col")
        if st.button("Generate Histogram"):
            data, err = call_api("/upload/histogram", {"column": col})
            if err:
                st.error(err)
            else:
                show_chart(data["chart_base64"], f"Histogram of {col}")
 
    elif chart_type == "Boxplot":
        col = st.text_input("Column", value="Fare", key="box_col")
        if st.button("Generate Boxplot"):
            data, err = call_api("/upload/boxplot", {"column": col})
            if err:
                st.error(err)
            else:
                show_chart(data["chart_base64"], f"Boxplot of {col}")
 
    elif chart_type == "Scatter Plot":
        c1, c2 = st.columns(2)
        x_col = c1.text_input("X column", value="Age", key="x_col")
        y_col = c2.text_input("Y column", value="Fare", key="y_col")
        if st.button("Generate Scatter Plot"):
            data, err = call_api("/upload/scatterplot", {"x_column": x_col, "y_column": y_col})
            if err:
                st.error(err)
            else:
                show_chart(data["chart_base64"], f"{x_col} vs {y_col}")
 
    elif chart_type == "Correlation Heatmap":
        if st.button("Generate Correlation Heatmap"):
            data, err = call_api("/upload/correlation-heatmap")
            if err:
                st.error(err)
            else:
                show_chart(data["chart_base64"], "Correlation Heatmap")
 
    elif chart_type == "Pie Chart":
        col = st.text_input("Column", value="Embarked", key="pie_col")
        if st.button("Generate Pie Chart"):
            data, err = call_api("/upload/piechart", {"column": col})
            if err:
                st.error(err)
            else:
                show_chart(data["chart_base64"], f"Proportion of {col}")
 
    elif chart_type == "Bar Chart":
        col = st.text_input("Column", value="Pclass", key="bar_col")
        if st.button("Generate Bar Chart"):
            data, err = call_api("/upload/barchart", {"column": col})
            if err:
                st.error(err)
            else:
                show_chart(data["chart_base64"], f"Count of {col}")
 
    elif chart_type == "Line Chart":
        col = st.text_input("Column", value="Fare", key="line_col")
        if st.button("Generate Line Chart"):
            data, err = call_api("/upload/linechart", {"column": col})
            if err:
                st.error(err)
            else:
                show_chart(data["chart_base64"], f"Sorted Trend of {col}")
 
# --- Analytics tab ---
with tab_analytics:
    st.subheader("Group By + Aggregate")
    c1, c2, c3 = st.columns(3)
    group_col = c1.text_input("Group by column", value="Pclass")
    agg_col = c2.text_input("Aggregate column", value="Fare")
    agg_func = c3.selectbox("Function", ["mean", "sum", "count", "median", "min", "max"])
    if st.button("Run Group By"):
        data, err = call_api(
            "/upload/groupby",
            {"group_by_column": group_col, "agg_column": agg_col, "agg_function": agg_func},
        )
        if err:
            st.error(err)
        else:
            st.json(data)
 
    st.markdown("---")
    st.subheader("Correlation Matrix")
    if st.button("Show Correlation Matrix"):
        data, err = call_api("/upload/correlation-matrix")
        if err:
            st.error(err)
        else:
            st.dataframe(data["correlation_matrix"])
 
    st.markdown("---")
    st.subheader("Value Counts")
    vc_col = st.text_input("Column", value="Embarked", key="vc_col")
    if st.button("Show Value Counts"):
        data, err = call_api("/upload/value-counts", {"column": vc_col})
        if err:
            st.error(err)
        else:
            st.json(data["value_counts"])
 
    st.markdown("---")
    st.subheader("Top N Records")
    c1, c2, c3 = st.columns(3)
    top_col = c1.text_input("Sort by column", value="Fare", key="top_col")
    top_n = c2.number_input("N", min_value=1, max_value=50, value=5)
    top_asc = c3.selectbox("Order", ["Descending (highest first)", "Ascending (lowest first)"])
    if st.button("Show Top Records"):
        data, err = call_api(
            "/upload/top-records",
            {"column": top_col, "n": top_n, "ascending": top_asc.startswith("Ascending")},
        )
        if err:
            st.error(err)
        else:
            st.dataframe(data["records"])
 
# --- Export tab ---
with tab_export:
    st.subheader("Download Cleaned Data")
 
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Download as CSV"):
            resp = requests.post(f"{API_URL}/upload/export-csv", params={"dataset_id": dataset_id}, timeout=60)
            if resp.status_code == 200:
                st.download_button(
                    "Click to save CSV", data=resp.content, file_name="cleaned_data.csv", mime="text/csv"
                )
            else:
                st.error(f"Export failed: {resp.status_code}")
 
    with col2:
        if st.button("Download as Excel"):
            resp = requests.post(f"{API_URL}/upload/export-excel", params={"dataset_id": dataset_id}, timeout=60)
            if resp.status_code == 200:
                st.download_button(
                    "Click to save Excel",
                    data=resp.content,
                    file_name="cleaned_data.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            else:
                st.error(f"Export failed: {resp.status_code}")
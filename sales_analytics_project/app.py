"""
app.py - Streamlit dashboard for Sales Analytics demo
Run: streamlit run app.py
"""
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine

DB_URL = st.secrets["DB_URL"] if "DB_URL" in st.secrets else "postgresql+psycopg2://user:password@localhost:5432/salesdb"
engine = create_engine(DB_URL)

st.set_page_config(page_title="Sales Analytics Demo", layout="wide")

st.title("Sales Analytics - Demo")

@st.cache_data(ttl=300)
def load_monthly():
    q = """
    SELECT DATE_TRUNC('month', order_date) AS month, SUM(total_amount) AS revenue
    FROM orders
    GROUP BY month
    ORDER BY month;
    """
    return pd.read_sql(q, engine)

@st.cache_data(ttl=300)
def load_top_products(limit=10):
    q = f"""
    SELECT p.sku, p.name, SUM(oi.line_total) AS revenue, SUM(oi.quantity) AS qty
    FROM order_items oi JOIN products p ON oi.product_id = p.product_id
    GROUP BY p.sku, p.name
    ORDER BY revenue DESC
    LIMIT {limit};
    """
    return pd.read_sql(q, engine)

try:
    monthly = load_monthly()
    if not monthly.empty:
        monthly['month'] = pd.to_datetime(monthly['month']).dt.to_period('M').dt.to_timestamp()
        st.line_chart(monthly.set_index('month')['revenue'])
    else:
        st.info("No monthly data found. Run ETL to load sample data into the database.")

    st.markdown("### Top products by revenue")
    top_products = load_top_products(10)
    st.table(top_products)
except Exception as e:
    st.error(f"Unable to load data from DB: {e}")
    st.info("Make sure you've run the SQL schema and the ETL script to populate the database.")


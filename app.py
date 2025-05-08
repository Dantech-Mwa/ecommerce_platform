import sqlite3
import pandas as pd
import plotly.express as px
import streamlit as st
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
import random

# --- Database Setup ---
def init_db():
    conn = sqlite3.connect('business_data.db')
    c = conn.cursor()
    # Sales table
    c.execute('''
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sale_date TEXT,
            product TEXT,
            quantity INTEGER,
            total_selling_price REAL,
            total_buying_price REAL,
            revenue REAL,
            customer_id INTEGER
        )
    ''')
    # Inventory table
    c.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product TEXT,
            stock INTEGER,
            last_updated TEXT
        )
    ''')
    # Customers table
    c.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            orders INTEGER,
            is_active INTEGER
        )
    ''')
    conn.commit()
    conn.close()

# --- Data Fetching ---
def fetch_sales_data():
    try:
        conn = sqlite3.connect('business_data.db')
        df = pd.read_sql_query('SELECT * FROM sales', conn)
        conn.close()
        return df
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return pd.DataFrame()

def fetch_inventory_data():
    try:
        conn = sqlite3.connect('business_data.db')
        df = pd.read_sql_query('SELECT * FROM inventory', conn)
        conn.close()
        return df
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return pd.DataFrame()

def fetch_customer_data():
    try:
        conn = sqlite3.connect('business_data.db')
        df = pd.read_sql_query('SELECT * FROM customers', conn)
        conn.close()
        return df
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return pd.DataFrame()

# --- Metrics Calculation ---
def compute_metrics(sales_df, customer_df):
    total_customers = len(customer_df)
    active_customers = len(customer_df[customer_df['is_active'] == 1])
    churn_rate = ((total_customers - active_customers) / total_customers * 100) if total_customers > 0 else 0
    metrics = {
        'total_revenue': sales_df['revenue'].sum(),
        'avg_order_value': sales_df['total_selling_price'].mean() if not sales_df.empty else 0,
        'total_quantity': sales_df['quantity'].sum(),
        'churn_rate': churn_rate,
        'total_customers': total_customers,
        'profit_margin': (sales_df['revenue'].sum() / sales_df['total_selling_price'].sum() * 100) if sales_df['total_selling_price'].sum() > 0 else 0
    }
    return metrics

# --- Visualizations ---
def create_visualizations(sales_df, inventory_df, customer_df):
    # Sales by Product (Bar Chart)
    fig1 = px.bar(sales_df, x='product', y='revenue', title='Revenue by Product', color='product')
    
    # Weekly Revenue Trend (Line Chart)
    sales_df['sale_date'] = pd.to_datetime(sales_df['sale_date'])
    sales_df['week'] = sales_df['sale_date'].dt.isocalendar().week
    weekly_revenue = sales_df.groupby('week')['revenue'].sum().reset_index()
    fig2 = px.line(weekly_revenue, x='week', y='revenue', title='Weekly Revenue Trend', markers=True)
    
    # Inventory Levels (Bar Chart)
    fig3 = px.bar(inventory_df, x='product', y='stock', title='Inventory Levels', color='product')
    
    # Customer Churn (Pie Chart)
    churn_counts = customer_df['is_active'].value_counts().reset_index()
    churn_counts['status'] = churn_counts['is_active'].map({1: 'Active', 0: 'Churned'})
    fig4 = px.pie(churn_counts, values='count', names='status', title='Customer Churn Status')
    
    return fig1, fig2, fig3, fig4

# --- Automation (Optional Sample Data) ---
def generate_sample_data():
    try:
        products = ['Phone', 'Tablet', 'TV', 'Appliance']
        sale_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        for product in products:
            quantity = random.randint(1, 20)
            selling_price = random.uniform(5000, 50000)  # Ksh per unit
            buying_price = selling_price * random.uniform(0.6, 0.8)  # 60-80% of selling price
            total_selling_price = quantity * selling_price
            total_buying_price = quantity * buying_price
            revenue = total_selling_price - total_buying_price
            customer_id = random.randint(1, 10)
            conn = sqlite3.connect('business_data.db')
            c = conn.cursor()
            c.execute('INSERT INTO sales (sale_date, product, quantity, total_selling_price, total_buying_price, revenue, customer_id) VALUES (?, ?, ?, ?, ?, ?, ?)',
                      (sale_date, product, quantity, total_selling_price, total_buying_price, revenue, customer_id))
            c.execute('INSERT OR REPLACE INTO inventory (product, stock, last_updated) VALUES (?, ?, ?)',
                      (product, random.randint(10, 100), sale_date))
            conn.commit()
            conn.close()
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")

def schedule_data_update():
    scheduler = BackgroundScheduler()
    scheduler.add_job(generate_sample_data, 'interval', hours=24)
    scheduler.start()

# --- Streamlit Interface ---
def main():
    # No st.set_page_config()
    st.title("📊 E-Commerce Analytics Dashboard")
    st.title("Analytics Dashboard")
    # Initialize database
    init_db()
    
    # Generate sample data if none exists
    if len(fetch_sales_data()) == 0:
        generate_sample_data()
    
    # Fetch data
    sales_df = fetch_sales_data()
    inventory_df = fetch_inventory_data()
    customer_df = fetch_customer_data()
    
    # Compute metrics
    metrics = compute_metrics(sales_df, customer_df)
    
    # Display metrics
    st.subheader("📈 Key Performance Indicators")
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("Total Revenue", f"Ksh {metrics['total_revenue']:,.2f}")
    col2.metric("Avg Order Value", f"Ksh {metrics['avg_order_value']:,.2f}")
    col3.metric("Total Quantity Sold", f"{metrics['total_quantity']:,}")
    col4.metric("Churn Rate", f"{metrics['churn_rate']:.2f}%")
    col5.metric("Total Customers", f"{metrics['total_customers']:,}")
    col6.metric("Profit Margin", f"{metrics['profit_margin']:.2f}%")
    
    # Display visualizations
    st.subheader("📊 Visual Analytics")
    # First row: Sales by Product, Weekly Revenue Trend, Inventory Levels
    col1, col2, col3 = st.columns(3)
    fig1, fig2, fig3, fig4 = create_visualizations(sales_df, inventory_df, customer_df)
    with col1:
        st.plotly_chart(fig1, use_container_width=True, key="analytics_sales_by_product")
    with col2:
        st.plotly_chart(fig2, use_container_width=True, key="analytics_weekly_revenue")
    with col3:
        st.plotly_chart(fig3, use_container_width=True, key="analytics_inventory_levels")
    
    # Second row: Customer Churn (centered)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.plotly_chart(fig4, use_container_width=True, key="analytics_customer_churn")

if __name__ == "__main__":
    schedule_data_update()
    main()
import sqlite3
import streamlit as st
import pandas as pd
from datetime import datetime
import random

# --- Database Functions ---
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

def add_sale(product, quantity, selling_price, buying_price, customer_id):
    try:
        sale_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        total_selling_price = quantity * selling_price
        total_buying_price = quantity * buying_price
        revenue = total_selling_price - total_buying_price
        conn = sqlite3.connect('business_data.db')
        c = conn.cursor()
        c.execute('INSERT INTO sales (sale_date, product, quantity, total_selling_price, total_buying_price, revenue, customer_id) VALUES (?, ?, ?, ?, ?, ?, ?)',
                  (sale_date, product, quantity, total_selling_price, total_buying_price, revenue, customer_id))
        c.execute('UPDATE inventory SET stock = stock - ? WHERE product = ?', (quantity, product))
        conn.commit()
        conn.close()
        return True
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return False

def add_inventory(product, stock):
    try:
        conn = sqlite3.connect('business_data.db')
        c = conn.cursor()
        c.execute('INSERT OR REPLACE INTO inventory (product, stock, last_updated) VALUES (?, ?, ?)',
                  (product, stock, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()
        conn.close()
        return True
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return False

def add_customer(name, email, orders=0, is_active=1):
    try:
        conn = sqlite3.connect('business_data.db')
        c = conn.cursor()
        c.execute('INSERT INTO customers (name, email, orders, is_active) VALUES (?, ?, ?, ?)',
                  (name, email, orders, is_active))
        conn.commit()
        customer_id = c.lastrowid
        conn.close()
        return customer_id
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return None

def fetch_customers():
    try:
        conn = sqlite3.connect('business_data.db')
        df = pd.read_sql_query('SELECT * FROM customers', conn)
        conn.close()
        return df
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return pd.DataFrame()

# --- Streamlit Interface ---
st.set_page_config(page_title="E-Commerce Business Management", layout="wide")
st.title("🛒 E-Commerce Business Management")

# Initialize database
init_db()

# Tabs for different management tasks
tab1, tab2, tab3, tab4 = st.tabs(["Add Sale", "Update Inventory", "Manage Customers", "Import Data"])

# Tab 1: Add Sale
with tab1:
    st.subheader("Record a Sale")
    product = st.selectbox("Product", ["Phone", "Tablet", "TV", "Appliance"])
    quantity = st.number_input("Quantity", min_value=1, value=1)
    selling_price = st.number_input("Selling Price per Unit (Ksh)", min_value=0.0, value=1000.0)
    buying_price = st.number_input("Buying Price per Unit (Ksh)", min_value=0.0, value=600.0)
    customer_id = st.number_input("Customer ID", min_value=1, value=1)
    if st.button("Add Sale"):
        if add_sale(product, quantity, selling_price, buying_price, customer_id):
            st.success("Sale recorded!")

# Tab 2: Update Inventory
with tab2:
    st.subheader("Update Inventory")
    product = st.selectbox("Product (Inventory)", ["Phone", "Tablet", "TV", "Appliance"])
    stock = st.number_input("Stock Level", min_value=0, value=0)
    if st.button("Update Inventory"):
        if add_inventory(product, stock):
            st.success("Inventory updated!")

# Tab 3: Manage Customers
with tab3:
    st.subheader("Add Customer")
    name = st.text_input("Customer Name")
    email = st.text_input("Customer Email")
    is_active = st.checkbox("Active Customer", value=True)
    if st.button("Add Customer"):
        customer_id = add_customer(name, email, orders=0, is_active=1 if is_active else 0)
        if customer_id:
            st.success(f"Customer added with ID: {customer_id}")
    
    st.subheader("View Customers")
    customer_df = fetch_customers()
    st.dataframe(customer_df)

# Tab 4: Import Data
with tab4:
    st.subheader("Import Sales Data from CSV")
    st.write("CSV format: product,quantity,selling_price,buying_price,customer_id")
    uploaded_file = st.file_uploader("Upload CSV", type="csv")
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        for _, row in df.iterrows():
            if add_sale(row['product'], int(row['quantity']), float(row['selling_price']), float(row['buying_price']), int(row['customer_id'])):
                st.success("Sales data imported!")
            else:
                st.error("Failed to import some sales data.")

# Simulate Business Activity
if st.button("Simulate Daily Sales"):
    products = ['Phone', 'Tablet', 'TV', 'Appliance']
    for product in products:
        quantity = random.randint(1, 10)
        selling_price = random.uniform(5000, 50000)
        buying_price = selling_price * random.uniform(0.6, 0.8)
        customer_id = random.randint(1, 10)
        if add_sale(product, quantity, selling_price, buying_price, customer_id):
            st.success("Simulated daily sales added!")
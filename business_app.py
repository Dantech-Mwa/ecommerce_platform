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
            stock INTEGER CHECK(stock >= 0),  -- Prevent negative stock
            last_updated TEXT
        )
    ''')
    # Customers table
    c.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE,
            orders INTEGER,
            is_active INTEGER
        )
    ''')
    conn.commit()
    conn.close()

def add_sale(product, quantity, selling_price, buying_price, customer_id):
    try:
        conn = sqlite3.connect('business_data.db')
        c = conn.cursor()
        # Validate customer_id exists
        c.execute('SELECT id FROM customers WHERE id = ?', (customer_id,))
        if not c.fetchone():
            st.error(f"Customer ID {customer_id} does not exist.")
            conn.close()
            return False
        # Validate product exists and has sufficient stock
        c.execute('SELECT stock FROM inventory WHERE product = ?', (product,))
        stock_result = c.fetchone()
        if not stock_result:
            st.error(f"Product {product} not found in inventory.")
            conn.close()
            return False
        current_stock = stock_result[0]
        if current_stock < quantity:
            st.error(f"Insufficient stock for {product}. Available: {current_stock}, Requested: {quantity}")
            conn.close()
            return False
        # Proceed with sale
        sale_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        total_selling_price = quantity * selling_price
        total_buying_price = quantity * buying_price
        revenue = total_selling_price - total_buying_price
        c.execute('INSERT INTO sales (sale_date, product, quantity, total_selling_price, total_buying_price, revenue, customer_id) VALUES (?, ?, ?, ?, ?, ?, ?)',
                  (sale_date, product, quantity, total_selling_price, total_buying_price, revenue, customer_id))
        # Update inventory stock
        c.execute('UPDATE inventory SET stock = stock - ?, last_updated = ? WHERE product = ?',
                  (quantity, sale_date, product))
        # Increment customer orders
        c.execute('UPDATE customers SET orders = orders + 1 WHERE id = ?', (customer_id,))
        conn.commit()
        conn.close()
        return True
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        conn.close()
        return False

def add_inventory(product, stock, last_updated=None):
    try:
        if stock < 0:
            st.error(f"Stock for {product} cannot be negative.")
            return False
        if last_updated is None:
            last_updated = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        conn = sqlite3.connect('business_data.db')
        c = conn.cursor()
        c.execute('INSERT OR REPLACE INTO inventory (product, stock, last_updated) VALUES (?, ?, ?)',
                  (product, stock, last_updated))
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
        # Check if email already exists
        c.execute('SELECT email FROM customers WHERE email = ?', (email,))
        if c.fetchone():
            st.error(f"Customer with email {email} already exists.")
            conn.close()
            return None
        # Add new customer
        c.execute('INSERT INTO customers (name, email, orders, is_active) VALUES (?, ?, ?, ?)',
                  (name, email, orders, is_active))
        conn.commit()
        customer_id = c.lastrowid
        conn.close()
        return customer_id
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return None

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
def main():
    st.title("🛒 E-Commerce Business Management")
    st.title("Business Management Platform")

    # Initialize database
    init_db()

    # Tabs for different management tasks
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Add Sale", "Update Inventory", "Manage Customers", "Import Data", "View Data"])

    # Tab 1: Add Sale
    with tab1:
        st.subheader("Record a Sale")
        product = st.selectbox("Product", ["Phone", "Tablet", "TV", "Appliance"], key="sale_product")
        quantity = st.number_input("Quantity", min_value=1, value=1, key="sale_quantity")
        selling_price = st.number_input("Selling Price per Unit (Ksh)", min_value=0.0, value=1000.0, key="sale_selling_price")
        buying_price = st.number_input("Buying Price per Unit (Ksh)", min_value=0.0, value=600.0, key="sale_buying_price")
        customer_id = st.number_input("Customer ID", min_value=1, value=1, key="sale_customer_id")
        if st.button("Add Sale", key="add_sale_button"):
            if add_sale(product, quantity, selling_price, buying_price, customer_id):
                st.success("Sale recorded!")

    # Tab 2: Update Inventory
    with tab2:
        st.subheader("Update Inventory")
        product = st.selectbox("Product (Inventory)", ["Phone", "Tablet", "TV", "Appliance"], key="inventory_product")
        stock = st.number_input("Stock Level", min_value=0, value=0, key="inventory_stock")
        if st.button("Update Inventory", key="update_inventory_button"):
            if add_inventory(product, stock):
                st.success("Inventory updated!")

    # Tab 3: Manage Customers
    with tab3:
        st.subheader("Add Customer")
        name = st.text_input("Customer Name", key="customer_name")
        email = st.text_input("Customer Email", key="customer_email")
        is_active = st.checkbox("Active Customer", value=True, key="customer_active")
        if st.button("Add Customer", key="add_customer_button"):
            customer_id = add_customer(name, email, orders=0, is_active=1 if is_active else 0)
            if customer_id:
                st.success(f"Customer added with ID: {customer_id}")
        
        st.subheader("View Customers")
        customer_df = fetch_customers()
        st.dataframe(customer_df)

    # Tab 4: Import Data
    with tab4:
        st.subheader("Import Data from CSV")
        
        # Sales CSV Import
        st.write("Sales CSV format: product,quantity,selling_price,buying_price,customer_id")
        sales_file = st.file_uploader("Upload Sales CSV", type="csv", key="sales_csv_upload")
        if sales_file:
            df = pd.read_csv(sales_file)
            for _, row in df.iterrows():
                if add_sale(row['product'], int(row['quantity']), float(row['selling_price']), float(row['buying_price']), int(row['customer_id'])):
                    st.success(f"Sale for {row['product']} imported!")
                else:
                    st.error(f"Failed to import sale for {row['product']}.")

        # Inventory CSV Import
        st.write("Inventory CSV format: product,stock,last_updated")
        inventory_file = st.file_uploader("Upload Inventory CSV", type="csv", key="inventory_csv_upload")
        if inventory_file:
            df = pd.read_csv(inventory_file)
            for _, row in df.iterrows():
                if add_inventory(row['product'], int(row['stock']), row['last_updated']):
                    st.success(f"Inventory for {row['product']} imported!")
                else:
                    st.error(f"Failed to import inventory for {row['product']}.")

        # Customers CSV Import
        st.write("Customers CSV format: name,email,orders,is_active")
        customers_file = st.file_uploader("Upload Customers CSV", type="csv", key="customers_csv_upload")
        if customers_file:
            df = pd.read_csv(customers_file)
            for _, row in df.iterrows():
                customer_id = add_customer(row['name'], row['email'], int(row['orders']), int(row['is_active']))
                if customer_id:
                    st.success(f"Customer {row['name']} imported with ID: {customer_id}")
                else:
                    st.error(f"Failed to import customer {row['name']}.")

    # Tab 5: View Data
    with tab5:
        st.subheader("View All Data")
        
        st.write("### Sales Data")
        sales_df = fetch_sales_data()
        if not sales_df.empty:
            st.dataframe(sales_df)
        else:
            st.write("No sales data available.")
        
        st.write("### Inventory Data")
        inventory_df = fetch_inventory_data()
        if not inventory_df.empty:
            st.dataframe(inventory_df)
        else:
            st.write("No inventory data available.")
        
        st.write("### Customers Data")
        customer_df = fetch_customers()
        if not customer_df.empty:
            st.dataframe(customer_df)
        else:
            st.write("No customer data available.")

    # Simulate Business Activity
    if st.button("Simulate Daily Sales", key="simulate_sales"):
        products = ['Phone', 'Tablet', 'TV', 'Appliance']
        for product in products:
            conn = sqlite3.connect('business_data.db')
            c = conn.cursor()
            c.execute('SELECT stock FROM inventory WHERE product = ?', (product,))
            stock_result = c.fetchone()
            if stock_result and stock_result[0] > 0:
                quantity = random.randint(1, min(stock_result[0], 10))  # Limit to available stock
                selling_price = random.uniform(5000, 50000)
                buying_price = selling_price * random.uniform(0.6, 0.8)
                customer_id = random.randint(1, 10)
                if add_sale(product, quantity, selling_price, buying_price, customer_id):
                    st.success(f"Simulated sale for {product} added!")
            else:
                st.warning(f"Skipping {product}: No stock available.")
            conn.close()

if __name__ == "__main__":
    main()

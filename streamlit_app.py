import streamlit as st
import pandas as pd
import os
from logic.customer_import import generate_customer_import
from logic.sales_order_import import generate_sales_order_import
from logic.split_pdfs import split_and_rename_pdfs

# Ensure output and data folders exist
os.makedirs("output", exist_ok=True)
os.makedirs("data", exist_ok=True)

mapping_file = "data/sku_price_mapping.csv"

# Initialize SKU mapping file if it doesn't exist
if not os.path.exists(mapping_file):
    pd.DataFrame(columns=["UPC", "SKU", "Price"]).to_csv(mapping_file, index=False)

# Load mapping into memory
sku_df = pd.read_csv(mapping_file)

st.title("🧾 CVS PDF → Odoo Import Files")

# --- Admin Panel ---
st.sidebar.header("🛠 SKU & Price Admin Panel")
with st.sidebar.expander("View / Update SKU Mapping", expanded=True):
    st.dataframe(sku_df, use_container_width=True)

    with st.form("add_mapping"):
        upc = st.text_input("UPC")
        sku = st.text_input("SKU")
        price = st.number_input("Price", min_value=0.0, step=0.01)
        submitted = st.form_submit_button("Add / Update")
        if submitted:
            sku_df = sku_df[sku_df["UPC"] != upc]  # Remove old if exists
            sku_df.loc[len(sku_df)] = [upc, sku, price]
            sku_df.to_csv(mapping_file, index=False)
            st.success("Mapping updated. Refresh to apply.")

# --- File Uploads ---
pdf_file = st.file_uploader("📄 Upload CVS Packing Slip PDF", type=["pdf"])

if pdf_file:
    with open("input.pdf", "wb") as f:
        f.write(pdf_file.read())

    # Generate both customer and sales data
    po_data, customer_df, sales_df = generate_sales_order_import("input.pdf", mapping_file)

    # File paths
    customer_path = "output/customers.xlsx"
    sales_path = "output/sales_orders.xlsx"

    # Save both files
    generate_customer_import(customer_df, customer_path)
    sales_df.to_excel(sales_path, index=False)

    # Split PDFs by Ship To name
    split_and_rename_pdfs("input.pdf", output_dir="output", names=po_data)

    st.success("✅ Files generated!")

    # Download buttons
    st.download_button("📥 Download Customer Import Excel", open(customer_path, "rb"), file_name="customers.xlsx")
    st.download_button("📥 Download Sales Order Excel", open(sales_path, "rb"), file_name="sales_orders.xlsx")

    # Show split packing slips
    st.subheader("📦 Split Packing Slips")
    for fname in os.listdir("output"):
        if fname.endswith(".pdf"):
            with open(os.path.join("output", fname), "rb") as f:
                st.download_button(f"Download {fname}", f, file_name=fname)


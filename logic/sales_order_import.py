import fitz  # PyMuPDF
import pandas as pd
import re

def us_state_full(abbrev):
    mapping = {
        "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas", "CA": "California",
        "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware", "FL": "Florida", "GA": "Georgia",
        "HI": "Hawaii", "ID": "Idaho", "IL": "Illinois", "IN": "Indiana", "IA": "Iowa",
        "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
        "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi", "MO": "Missouri",
        "MT": "Montana", "NE": "Nebraska", "NV": "Nevada", "NH": "New Hampshire", "NJ": "New Jersey",
        "NM": "New Mexico", "NY": "New York", "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio",
        "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",
        "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah", "VT": "Vermont",
        "VA": "Virginia", "WA": "Washington", "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming"
    }
    return mapping.get(abbrev, abbrev)

def generate_sales_order_import(pdf_path, sku_mapping_path):
    doc = fitz.open(pdf_path)
    sku_df = pd.read_csv(sku_mapping_path)
    upc_to_sku = dict(zip(sku_df['UPC'].astype(str), sku_df['SKU']))
    upc_to_price = dict(zip(sku_df['UPC'].astype(str), sku_df['Price']))

    orders = []
    for page in doc:
        text = page.get_text()

        # More robust customer order number regex
        customer_order_match = re.search(r'CUSTOMER ORDER NUMBER:\s*(\d+)', text, re.IGNORECASE)
        customer_order_number = customer_order_match.group(1) if customer_order_match else "UNKNOWN"

        name_match = re.search(r'SHIP TO:\s*(.+)', text)
        address_match = re.search(r'SHIP TO:\s*.+?\n(.*?)\n(.*?)\s+([A-Z]{2})\s+(\d{5})', text)
        phone_match = re.search(r'(\d{3}[-\s]?\d{3}[-\s]?\d{4})', text)
        upc_match = re.search(r'(817483\d{6,7})', text)
        qty_match = re.search(r'\n(\d+)\s+[\d.]+\s+[\d.]+', text)

        if not (name_match and address_match and upc_match and qty_match):
            continue

        customer = name_match.group(1).strip()
        street = address_match.group(1).strip()
        city = address_match.group(2).strip().rstrip(',')
        state_abbrev = address_match.group(3).strip()
        zip_code = address_match.group(4).strip()
        state_full = us_state_full(state_abbrev)
        phone = phone_match.group(1).strip() if phone_match else ""
        upc = upc_match.group(1)
        qty = int(qty_match.group(1))

        sku = upc_to_sku.get(upc, "UNKNOWN")
        price = upc_to_price.get(upc, 0.00)

        orders.append({
            'po_number': customer_order_number,
            'customer': customer,
            'street': street,
            'city': city,
            'state': state_full,
            'zip': zip_code,
            'phone': phone,
            'sku': sku,
            'qty': qty,
            'price': price
        })

    customers = []
    sales = []

    for o in orders:
        customers.append({
            'name': o['customer'],
            'is_company': 0,
            'company_name': 'CVS CareMark Corporate Office Headquarters',
            'country_id': 'US',
            'state_id': f"{o['state']} (US)",
            'zip': o['zip'],
            'city': o['city'],
            'street': o['street'],
            'street2': '',
            'phone': o['phone'],
            'mobile': '',
            'email': '',
            'vat': '',
            'bank_ids/bank': '',
            'bank_ids/acc_number': ''
        })
        sales.append({
            'Customer': 'CVS CareMark Corporate Office Headquarters',
            'Invoice Address': 'CVS CareMark Corporate Office Headquarters',
            'Delivery Address': f"CVS CareMark Corporate Office Headquarters, {o['customer']}",
            'PO#': o['po_number'],
            'order_line/sequence': 1,
            'order_line/product_uom_qty': o['qty'],
            'order_line/price_unit': o['price'],
            'order_line/product_template_id': o['sku'],
            'order_line/product_uom': 'Each - 1'
        })

    return orders, pd.DataFrame(customers).drop_duplicates(), pd.DataFrame(sales)


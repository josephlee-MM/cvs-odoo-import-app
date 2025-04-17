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
        lines = text.splitlines()

        # --- Extract PO number ---
        po_number = ""
        for line in lines:
            if "CUSTOMER ORDER NUMBER:" in line.upper():
                match = re.search(r'(\d{6,})', line)
                if match:
                    po_number = match.group(1)
                    break

        # --- Extract Ship To block ---
        ship_to_block = []
        start = False
        for line in lines:
            if "SHIP TO:" in line:
                start = True
                continue
            if start and ("BILL TO:" in line or line.strip() == ""):
                break
            if start:
                ship_to_block.append(line.strip())

        customer = ship_to_block[0] if len(ship_to_block) > 0 else ""
        street = ship_to_block[1] if len(ship_to_block) > 1 else ""
        city = ""
        state = ""
        zip_code = ""
        phone = ""

        for line in ship_to_block:
            match = re.search(r'(.*),\s+([A-Z]{2})\s+(\d{5})', line)
            if match:
                city = match.group(1).strip()
                state = us_state_full(match.group(2).strip())
                zip_code = match.group(3).strip()

            phone_match = re.search(r'(\(?\d{3}\)?[-\s]?\d{3}[-\s]?\d{4})', line)
            if phone_match:
                phone = phone_match.group(1)

        # --- Extract line items (UPC, QTY) ---
        item_lines = re.findall(r'(817483\d{6,7})[^\n]*?(\d+)\s+[\d.]+\s+[\d.]+', text)

        sequence = 1
        for upc, qty in item_lines:
            sku = upc_to_sku.get(upc, "UNKNOWN")
            price = upc_to_price.get(upc, 0.00)

            orders.append({
                'po_number': po_number,
                'customer': customer,
                'street': street,
                'city': city,
                'state': state,
                'zip': zip_code,
                'phone': phone,
                'sku': sku,
                'qty': int(qty),
                'price': float(price),
                'sequence': sequence
            })
            sequence += 1

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
            'order_line/sequence': o['sequence'],
            'order_line/product_uom_qty': o['qty'],
            'order_line/price_unit': o['price'],
            'order_line/product_template_id': o['sku'],
            'order_line/product_uom': 'Each - 1'
        })

    return orders, pd.DataFrame(customers).drop_duplicates(), pd.DataFrame(sales)



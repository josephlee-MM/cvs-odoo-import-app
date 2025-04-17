import pandas as pd

def generate_customer_import(customer_df, output_path):
    """
    Exports customer DataFrame to Odoo-ready customer import Excel file.
    Format is identical to Walmart version:
    - name
    - is_company
    - company_name
    - country_id
    - state_id
    - zip
    - city
    - street
    - street2
    - phone
    - mobile
    - email
    - vat
    - bank_ids/bank
    - bank_ids/acc_number
    """
    df = customer_df.copy()
    
    # Enforce column order just in case
    expected_columns = [
        'name', 'is_company', 'company_name', 'country_id', 'state_id', 'zip',
        'city', 'street', 'street2', 'phone', 'mobile', 'email', 'vat',
        'bank_ids/bank', 'bank_ids/acc_number'
    ]
    
    for col in expected_columns:
        if col not in df.columns:
            df[col] = ""

    df = df[expected_columns]
    df.to_excel(output_path, index=False)

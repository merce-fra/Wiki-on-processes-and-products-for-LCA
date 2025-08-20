# -----------------------------------------------------------------------------
# Description: [python code to import data (create product and process pages) from Excel files that are compatible with the Brightway format]
# [Directly generates GitHub Wiki markdown pages (.md) for product and process]
# Author: [Vincent Corlay - Mitsubishi Electric R&D Centre Europe]
# -----------------------------------------------------------------------------

from brightway2 import *
import os

# Define paths for database files
base_path_source = "./Wiki-on-processes-and-products-for-LCA/"  # EDIT THIS PATH IF NEEDED, parent folder for source files
base_path_target = "./Wiki-on-processes-and-products-for-LCA.wiki/"  # Parent folder for generated wiki markdown files
source_file_path = "Database_edition/source_import/Example_bw/Fairphone_4.xlsx"  
path = base_path_source + source_file_path
imp = ExcelImporter(path) #Brightway import function to import data from Excel files

product_path = os.path.join(base_path_target, "product_new")  # New product pages added in product_new_md/ (markdown)
process_path = os.path.join(base_path_target, "process_new")  ## New process pages added in process_new_md/ (markdown)
product_db_path =  os.path.join(base_path_target, "pd_db.md")  
process_db_path = os.path.join(base_path_target,"ps_db.md")   

# Create new directories if they don't exist
os.makedirs(product_path, exist_ok=True)
os.makedirs(process_path, exist_ok=True)

def is_content_different(existing_content: str, new_content: str) -> bool:
    def normalize(content):
        return ' '.join(line.strip() for line in content.splitlines() if line.strip())
    return normalize(existing_content) != normalize(new_content)

def create_markdown_file(filepath, content):
    original_path = filepath.replace('_new_md', '')
    if os.path.exists(original_path):
        with open(original_path, 'r', encoding='utf-8') as file:
            existing_content = file.read()
        if not is_content_different(existing_content, content):
            print(f"File exists with identical content - skipping: {filepath}")
            return False
        # For product files, merge process lists
        if 'product_new_md' in filepath:
            existing_processes = []
            new_processes = []
            for line in existing_content.splitlines():
                if line.strip().startswith("*"):
                    existing_processes.append(line)
            for line in content.splitlines():
                if line.strip().startswith("*"):
                    new_processes.append(line)
            all_processes = list(dict.fromkeys(existing_processes + new_processes))
            header = content.split("## List of processes")[0]
            content = header + "## List of processes\n"
            for process in all_processes:
                if not process.strip().startswith("**") and not "[product:" in process:
                    content += process + "\n"
            content += "\n## May be similar to the following products\n"
            base, ext = os.path.splitext(os.path.basename(filepath))
            if not base.endswith('_modified'):
                filepath = filepath.replace(ext, '_modified' + ext)
            with open(filepath, 'w', encoding='utf-8') as file:
                file.write(content)
            print(f"Updated product file: {filepath}")
            return True
        else:
            base, ext = os.path.splitext(filepath)
            counter = 1
            while os.path.exists(filepath):
                filepath = f"{base}_{counter}{ext}"
                counter += 1
            print(f"Creating new version: {filepath}")
    with open(filepath, 'w', encoding='utf-8') as file:
        file.write(content)
    print(f"Created file: {filepath}")
    return True

for record in imp.data:
    name = record['name']
    database = record['database']
    try:
        ref_prod = record.get('reference product')     
    except KeyError:  
        ref_prod = name
    try:
        type_ = record['type']
    except KeyError:
        type_ = "process" 
        ref_prod = name
        name = name + "_production"
    exchanges = record.get('exchanges', [])
    amount = record.get('amount')
    unit = record.get('unit')
    location = record.get('location')
    name = name

    if type_ == "process":
        prod_name = "pd_" + ref_prod.lower().replace(" ", "_").replace("__", "_").replace(",","")
        process_name = "ps_" + name.lower().replace(" ", "_").replace("__", "_").replace(",","")
        file_path = os.path.join(product_path, prod_name + ".md")
        content = f"# Product: {prod_name}\n\n## List of processes\n\n"
        content += f"* [{process_name}]({process_name}) - Quantity: {amount} {unit}\n\n"
        content += "## May be similar to the following products\n\n"
        if create_markdown_file(file_path, content):
            print(f"Added product to database: {prod_name}")

        file_path = os.path.join(process_path, process_name + ".md")
        content = f"# Process: {process_name}\n\n\n## Characteristics\n\n\n  * Database: {database}\n  * Location: {location}\n\n\n## Technosphere Flow\n\n\n### Production\n\n\n* [{prod_name}]({prod_name}) - Quantity: {amount} {unit}\n\n\n### Consumption\n\n\nProduct:\n\n"
        # Product exchanges
        for exchange in exchanges:
            if not exchange:
                break
            try:
                my_class = exchange['class']
            except KeyError:
                my_class = "product"
            if exchange['type'] == "technosphere" and my_class == "product":
                ref_prod_ex = exchange.get('reference product', exchange.get('name', ''))
                prod_link = f"pd_{ref_prod_ex.replace(' ', '_')}"
                content += f"* [{prod_link}]({prod_link}) - Quantity: {exchange['amount']} {exchange['unit']} - Database: {exchange['database']} \n"

        content += "\nProcess:\n\n"
        # Process exchanges
        for exchange in exchanges:
            try:
                my_class = exchange['class']
            except KeyError:
                my_class = "product"
            if not exchange:
                break
            if exchange['type'] == "technosphere" and my_class == "process":
                proc_link = f"ps_{exchange['name'].replace(' ', '_')}"
                content += f"* [{proc_link}]({proc_link}) - Quantity: {exchange['amount']} {exchange['unit']} - Database: {exchange['database']} \n"

        content += "\nChimaera (to be classified):\n\n"
        # Chimaera exchanges
        for exchange in exchanges:
            try:
                my_class = exchange['class']
            except KeyError:
                my_class = "product"
            if not exchange:
                break
            if exchange['type'] == "technosphere" and my_class == "chimaera":
                proc_link = f"ps_{exchange['name'].replace(' ', '_')}"
                content += f"* [{proc_link}]({proc_link}) - Quantity: {exchange['amount']} {exchange['unit']} - Database: {exchange['database']} \n"

        content += "\n\n## Biosphere Flow\n\n\n"
        for exchange in exchanges:
            if not exchange:
                break
            if exchange['type'] == "biosphere":
                bio_link = f"bp_{exchange['name'].replace(' ', '_')}"
                content += f"* [{bio_link}]({bio_link}) - Quantity: {exchange['amount']} {exchange['unit']} - Database: {exchange['database']}\n"

        content += "\n\n## Information\n\n\n  * Source file: {os.path.basename(path)}\n"
        # Optionally add more metadata here, e.g. author, document link, etc.
        if create_markdown_file(file_path, content):
            print(f"Added process to database: {process_name}")

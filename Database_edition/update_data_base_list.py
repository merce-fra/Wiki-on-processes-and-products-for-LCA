# -----------------------------------------------------------------------------
# Description: 
# [python code to update the list of products and processes in pd_db.md and ps_db.md]
# [If some pages are not referenced in the database, they will be added to the "To be classified" section.]
# [Directly generates markdown format as in pd_db.md and ps_db.md]
# Author: [Vincent Corlay - Mitsubishi Electric R&D Centre Europe]
# -----------------------------------------------------------------------------

import os

# Define paths for database files
base_path = "./Wiki-on-processes-and-products-for-LCA.wiki/" #EDIT THIS PATH IF NEEDED 

product_path = os.path.join(base_path, "product")
process_path = os.path.join(base_path, "process")
product_db_path = os.path.join(base_path, "pd_db.md")
process_db_path = os.path.join(base_path, "ps_db.md")

# Define default categories and their order (markdown style)
DEFAULT_CATEGORIES_MD = [
    '## End products or processes',
    '## Downstream',
    '## Midstream',
    '## Upstream',
    '## To be classified'
]

def initialize_db_file_md(db_path):
    """Create database file with default categories if it doesn't exist"""
    if not os.path.exists(db_path):
        with open(db_path, 'w', encoding='utf-8') as db_file:
            for category in DEFAULT_CATEGORIES_MD:
                db_file.write(f"{category}\n\n")

def read_existing_entries_md(db_path):
    existing_entries = set()
    categories = {cat: [] for cat in DEFAULT_CATEGORIES_MD}
    if os.path.exists(db_path):
        with open(db_path, 'r', encoding='utf-8') as f:
            current_category = None
            for line in f:
                line = line.rstrip()
                if line.startswith('## '):
                    current_category = line
                    if current_category not in categories:
                        categories[current_category] = []
                elif line.startswith('* [') and current_category:
                    existing_entries.add(line)
                    categories[current_category].append(line)
    return existing_entries, categories

def update_db_with_new_entries_md(folder_path, db_path):
    initialize_db_file_md(db_path)
    file_names = sorted([os.path.splitext(f)[0] for f in os.listdir(folder_path) 
                        if os.path.isfile(os.path.join(folder_path, f))])
    existing_entries, categories = read_existing_entries_md(db_path)
    new_entries = set(f"* [{name}]({name})" for name in file_names)
    all_categorized = set()
    for cat_entries in categories.values():
        all_categorized.update(cat_entries)
    truly_new_entries = new_entries - all_categorized
    if truly_new_entries:
        categories['## To be classified'].extend(sorted(truly_new_entries))
    with open(db_path, "w", encoding='utf-8') as db_file:
        for category in DEFAULT_CATEGORIES_MD:
            db_file.write(f"{category}\n\n")
            if categories[category]:
                for entry in sorted(set(categories[category])):
                    db_file.write(f"{entry}\n")
            db_file.write("\n")

# Update product and process database files in markdown format
update_db_with_new_entries_md(product_path, product_db_path)
update_db_with_new_entries_md(process_path, process_db_path)

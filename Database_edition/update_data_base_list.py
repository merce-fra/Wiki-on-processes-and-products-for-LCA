# -----------------------------------------------------------------------------
# Description: 
# [python code to update the list of products and processes in ps_db.txt and pd_db.txt]
# [If some pages are not referenced in the database, they will be added to the "To be classified" section.]
#
# Author: [Vincent Corlay - Mitsubishi Electric R&D Centre Europe]
# -----------------------------------------------------------------------------

import os

# Define paths for database files
base_path = "./Wiki-on-processes-and-products-for-LCA" #EDIT THIS PATH IF NEEDED 

product_path = os.path.join(base_path, "product")
process_path = os.path.join(base_path, "process")
product_db_path = os.path.join(product_path, "pd_db.txt")
process_db_path = os.path.join(process_path, "ps_db.txt")

# Define default categories and their order
DEFAULT_CATEGORIES = [
    'End products or processes:',
    'Downstream:',
    'Midstream:',
    'Upstream:',
    'To be classified:'
]

def initialize_db_file(db_path):
    """Create database file with default categories if it doesn't exist"""
    if not os.path.exists(db_path):
        with open(db_path, 'w') as db_file:
            for category in DEFAULT_CATEGORIES:
                db_file.write(f"{category}\n\n")

def read_existing_entries(db_path):
    existing_entries = set()
    # Initialize with default categories
    categories = {cat: [] for cat in DEFAULT_CATEGORIES}
    
    if os.path.exists(db_path):
        with open(db_path, 'r') as f:
            current_category = None
            for line in f:
                line = line.rstrip()
                if line.endswith(':'):  # Category line
                    current_category = line
                    if current_category not in categories:
                        categories[current_category] = []
                elif '*[[' in line and current_category:
                    if not line.startswith('  *[['):
                        line = '  ' + line.lstrip()
                    existing_entries.add(line)
                    categories[current_category].append(line)
    
    return existing_entries, categories

def update_db_with_new_entries(folder_path, db_path):
    # Initialize db file if it doesn't exist
    initialize_db_file(db_path)
    
    # Get all file names in the folder
    file_names = sorted([os.path.splitext(f)[0] for f in os.listdir(folder_path) 
                        if os.path.isfile(os.path.join(folder_path, f))])
    
    # Read existing entries and categories
    existing_entries, categories = read_existing_entries(db_path)
    
    # Format new entries with exactly two spaces
    new_entries = set(f"  *[[{name}]]" for name in file_names)
    
    # Find truly new entries (not in any category)
    all_categorized = set()
    for cat_entries in categories.values():
        all_categorized.update(cat_entries)
    truly_new_entries = new_entries - all_categorized
    
    # Always write all categories, even if no new entries
    if truly_new_entries:
        categories['To be classified:'].extend(sorted(truly_new_entries))
    
    # Write all categories in default order
    with open(db_path, "w") as db_file:
        for category in DEFAULT_CATEGORIES:
            db_file.write(f"{category}\n")
            if categories[category]:
                for entry in sorted(set(categories[category])):
                    db_file.write(f"{entry}\n")
            db_file.write("\n")

# Update product and process database files
update_db_with_new_entries(product_path, product_db_path)
update_db_with_new_entries(process_path, process_db_path)
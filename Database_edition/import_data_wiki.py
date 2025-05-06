# -----------------------------------------------------------------------------
# Description: [python code to import data (create product and process pages) from Excel files that are compatible with the Brightway format]
# [I.e., readable by the ExcelImporter class of brightway2]
#
# Author: [Vincent Corlay - Mitsubishi Electric R&D Centre Europe]
# -----------------------------------------------------------------------------


# %%
from brightway2 import *
import os

# %%
# Define paths for database files
base_path = "./"  # EDIT THIS PATH IF NEEDED

source_file_path = "Database_edition/source_import/Example_bw/lci_rawdata_import_corrected.xlsx"
path = base_path + source_file_path

imp = ExcelImporter(path) #Brightway import function to import data from Excel files

# %%


product_path = os.path.join(base_path, "product_new")  # New product pages added in product_new/ (to be moved manually to product/ if accepted)
process_path = os.path.join(base_path, "process_new")  ## New process pages added in process_new/ (to be moved manually to process/ if accepted)
product_db_path =  os.path.join(base_path, "product", "pd_db.txt")  # Keep original for db
process_db_path = os.path.join(base_path, "process", "ps_db.txt")   # Keep original for db

# Create new directories if they don't exist
os.makedirs(product_path, exist_ok=True)
os.makedirs(process_path, exist_ok=True)

def is_content_different(existing_content: str, new_content: str) -> bool:
    """Compare contents ignoring whitespace differences."""
    def normalize(content):
        return ' '.join(line.strip() for line in content.splitlines() if line.strip())
    return normalize(existing_content) != normalize(new_content)

# Function to create text files for products or processes
def create_text_file(filepath, content):
    # First, check if file exists in original folder. It it does, do some processing.
    # If it does not exist, create a new file in the new folder.

    # removing _new from path
    original_path = filepath.replace('_new', '')
    if os.path.exists(original_path):
        #processing if file with same name already exist in product/ or process/ folder
        #processing different for process and product files: new version for process files, merging for product files

        with open(original_path, 'r') as file:
            existing_content = file.read()
            
        if not is_content_different(existing_content, content):
            print(f"File exists with identical content - skipping: {filepath}")
            return False

        # For product files, merge content
        if 'product_new' in filepath:
            # Extract similarity section from existing content if present
            existing_similarity = ""
            if "__May be similar to the following products__" in existing_content:
                existing_similarity = existing_content.split("__May be similar to the following products__")[1].strip()

            # Extract and merge process lists
            existing_processes = []
            new_processes = []
            for line in existing_content.splitlines():
                if line.strip().startswith("*"):
                    existing_processes.append(line)
            for line in content.splitlines():
                if line.strip().startswith("*"):
                    new_processes.append(line)
                    
            all_processes = list(dict.fromkeys(existing_processes + new_processes))
            
            # Rebuild content with merged processes
            header = content.split("__List of processes__")[0]
            content = header + "__List of processes__\n"
            for process in all_processes:
                if not process.strip().startswith("**") and not "[[product:" in process: #to exclude **product ..
                    content += process + "\n"
            content += "\n__May be similar to the following products__\n"

             # Add similarity content, preserving both existing and new entries
            if existing_similarity:
                content += existing_similarity 

            base, ext = os.path.splitext(os.path.basename(filepath))
            if not base.endswith('_modified'):
                filepath = filepath.replace(ext, '_modified' + ext) # add _modified to filename if it the modification of existing product file

            with open(filepath, 'w') as file:
                file.write(content)
            print(f"Updated product file: {filepath}")
            return True
        else:
            # For process files, create new version
            base, ext = os.path.splitext(filepath)
            counter = 1
            while os.path.exists(filepath):
                filepath = f"{base}_{counter}{ext}"
                counter += 1
            print(f"Creating new version: {filepath}")

    with open(filepath, 'w') as file:
        file.write(content)
    print(f"Created file: {filepath}")
    return True

# %%
# Loop through each dictionary in imp.data (which is a list)
for record in imp.data:
    # Extract relevant fields
    name = record['name']
    database = record['database']

    try:
        ref_prod = record.get('reference product')     
    except KeyError:  
        ref_prod = name #if no reference product is given for the activity, we assume that the name of the product is the reference product

    try:
        type_ = record['type']
    except KeyError:
        #if no type is given for the activity, we define a process with name_production and reference product as name
        type_ = "process" 
        ref_prod = name #refprod is activity name
        name = name + "_production" #we assume that acitivity is process which produces the product

    
    exchanges = record.get('exchanges', [])
    amount = record.get('amount')
    unit = record.get('unit')
    location = record.get('location')

    name = name #+ "_loc_" + location #in the future, name of process should include location
    
    # Only treatement if type_ process for now. 
    if type_ == "process":

        prod_name = "pd_" + ref_prod.lower().replace(" ", "_").replace("__", "_").replace(",","")
        process_name = "ps_" + name.lower().replace(" ", "_").replace("__", "_").replace(",","")

        #First add page of product with list of process (often only one process)
        file_path = product_path + "\\" + prod_name + ".txt"
        content = f"**Product: {prod_name}**\n\n__List of processes__\n"
        content += f"  * [[process:{process_name}]] - Quantity: {amount} {unit}\n"

        content += "\n\n__May be similar to the following products__\n"
        # Check if the product file already exists, if does does merge content (=merge list of processes)
        if create_text_file(file_path, content):
            print(f"Added product to database: {prod_name}")

        # Then add process
        file_path = process_path + "\\" + process_name + ".txt"
        content = f"**Process: {process_name}**\n\n"

        content += "__Characteristics__\n\n"
        content += f"  * Database: {database}\n"
        content += f"  * Location: {location}\n"    
        
        #add technosphere flow
        content += "\n__Technosphere Flow__\n\n"
        #production
        content += "**Production**\n\n"
        content += f"  * [[product:{prod_name}]] - Quantity: {amount} {unit}\n"

        # Then, we loop several times through the exchanges to get the different types of exchanges (technosphere - product, process- and biosphere). 
        #Code could be optimized, but for now it is ok.

        #consumption
        content += "\n**Consumption**\n\n"
        content += "Product:\n\n"
        for exchange in exchanges:
            if not exchange:
                #print("Exchange is empty. Breaking out.")
                break
            try:
                my_class = exchange['class']
            except KeyError:
                my_class = "product" #if class is not given, we assume it is a product

            if exchange['type'] == "technosphere":
                if my_class == "product":
                    content += f"  * [[product:pd_{exchange['reference product'].replace(' ', '_')}]] - Quantity: {exchange['amount']} {exchange['unit']} - Database: {exchange['database']} \n"
        #Process
        content += "\nProcess:\n\n"
        for exchange in exchanges:
            try:
                my_class = exchange['class']
            except KeyError:
                my_class = "product"
            if not exchange:
                #print("Exchange is empty. Breaking out.")
                break
            if exchange['type'] == "technosphere":
                if my_class == "process":
                    content += f"  * [[process:ps_{exchange['name'].replace(' ', '_')}]] - Quantity: {exchange['amount']} {exchange['unit']} - Database: {exchange['database']} \n"
        content += "\nChimaera (to be classified):\n\n"
        for exchange in exchanges:
            try:
                my_class = exchange['class']
            except KeyError:
                my_class = "product"
            if not exchange:
                #print("Exchange is empty. Breaking out.")
                break
            if exchange['type'] == "technosphere":
                if my_class == "chimaera":
                    content += f"  * [[process:ps_{exchange['name'].replace(' ', '_')}]] - Quantity: {exchange['amount']} {exchange['unit']} - Database: {exchange['database']} \n"
                
        
        #add biosphere flow
        content += "\n\n__Biosphere Flow__\n\n"
        for exchange in exchanges:
            if not exchange:
                #print("Exchange is empty. Breaking out.")
                break
            if exchange['type'] == "biosphere":
                content += f"  * [[biosphere:bp_{exchange['name'].replace(' ', '_')}]] - Quantity: {exchange['amount']} {exchange['unit']} - Database: {exchange['database']}\n"

    content += "\n\n__Information__\n"
    content += f"  * Source file: {os.path.basename(path)}\n"
    #create file and update database
    if create_text_file(file_path, content):
        print(f"Added process to database: {process_name}")
    #update_db_file(process_db_path, process_name)
# %%

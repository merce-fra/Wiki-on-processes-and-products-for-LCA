# Project Overview

This project consists of two main parts:

1. **The Wiki**  
   A structured Wiki system to organize **processes and products**, that can be found in the public domain, to be used for Life Cycle Assessment (LCA). It provides a centralized repository for organizing and accessing information about products and processes, including their relationships and characteristics.
   You can access it directly in the [wiki of this github](https://github.com/merce-fra/Wiki-on-processes-and-products-for-LCA/wiki) or install it on dokuwiki.
   
   The pages are orginally generated in the dokuwiki format and then automatically converted to the github wiki format (markdown) with the script "convert_to_github_wiki.py".

   The sources of the pages are located in the folder process/ and product/

2. **The import function for Brightway-formatted data**  
   The tool "import_data_wiki.py" (folder code_database_edition) relies on the brightway format (with the brightway import function) to generate files from brightway-compatible data in Excel.

   If new pages are added, the ps_db and pd_db data_base folder (where all the pages are listed) should be updated by running the code "update_database_list.py".

3. **AI-based Wiki Edition**  
   This tool integrates AI to assist in the management and editing of the DokuWiki. It automates tasks such as page generation (for not brightway-compliant data), inconsistency detection, and product similarity analysis, ensuring the wiki remains consistent, accurate, and up-to-date.

# Accessing the wiki (on this github) 

Click [here](https://github.com/merce-fra/Wiki-on-processes-and-products-for-LCA/wiki) to access the wiki on this gihub.


# Installation on Dokuwiki

To install the dokuwiki version of the project, place the files in the `\dokuwiki\data\pages\` directory of your DokuWiki installation.

# Overview of the AI-Enhanced Data Management System

This tool provides AI-assisted management of Life Cycle Assessment (LCA) data within a DokuWiki system. It uses the Together AI API with the DeepSeek V3 model to process and organize product and process information.

## Main Features

1. **Product and Process Page Generation**
   - Automatically creates structured wiki pages from input data
   - Handles both products (pd_*) and processes (ps_*)
   - Preserves relationships between products and processes
   - Maintains consistent formatting with proper wiki syntax

2. **Inconsistency Detection**
   - Analyzes process files for structural inconsistencies
   - Identifies missing sections or formatting issues
   - Suggests corrections while preserving original content
   - Adds inconsistency reports to affected files

3. **Product Similarity Analysis**
   - Identifies similar products in the database
   - Adds similarity information to product pages
   - Preserves existing similarity relationships
   - Provides explanations for similarity matches

### Usage Example

1. **Adding New Data**
```bash
python generate_page.py
```
- Reads source data
- Creates structured wiki pages
- Maintains existing relationships

2. **Checking Consistency**
```bash
python inconsistency_send_request_API.py
```
- Analyzes all process files
- Reports formatting issues
- Suggests corrections

3. **Finding Similar Products**
```bash
python similarity_send_request_API.py
```
- Analyzes product relationships
- Updates similarity sections
- Preserves existing connections


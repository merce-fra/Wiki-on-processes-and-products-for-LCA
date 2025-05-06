# Project Overview

This project consists of three main parts:

1. **The Wiki**  
   A structured Wiki system to organize **processes and products**, that can be found in the public domain, to be used for Life Cycle Assessment (LCA).
   You can access it directly in the [Wiki of this GitHub](https://github.com/merce-fra/Wiki-on-processes-and-products-for-LCA/wiki) or install it on dokuwiki.
   
   The pages are orginally generated in the dokuwiki (.txt) format and then automatically converted to the GitHub Wiki format (markdown) with the script `convert_to_github_wiki.py`. The source files for the pages are located in the `process/` and `product/` folders of this repository. 
   
   Note that the GitHub Wiki is stored in a separate repository, which can be cloned from: https://github.com/merce-fra/Wiki-on-processes-and-products-for-LCA.wiki. Again, it is recommanded to modify the pages in the `process/` and `product/` folders of this repo and then automatically generate the files in the folder `Wiki-on-processes-and-products-for-LCA.wiki`.

2. **The import function for Brightway-formatted data**  
   The script `import_data_wiki.py` (in the folder `Database_edition/`) relies on the brightway format (with the brightway import function) to generate files from brightway-compatible data in Excel. New pages are automatically created in folders `process_new/` and `product_new/` . If the pages are satisfactory, they should then be manually moved to the folder `process/` and `product/` .

   If new pages are added in the folders `process/` and `product/`, the `ps_db.txt` and `pd_db.txt` files (where all the pages are listed) should be updated by running the code `update_database_list.py`.

3. **AI-based Wiki Edition**  
   This tool integrates AI to assist in the management and editing of the DokuWiki. It automates tasks such as page generation (for not brightway-compliant data), inconsistency detection, and product similarity analysis, ensuring the wiki remains consistent, accurate, and up-to-date.

# Accessing the Wiki (on this GitHub) 

Click [here](https://github.com/merce-fra/Wiki-on-processes-and-products-for-LCA/wiki) to access the Wiki on this gihub.


# Installation on Dokuwiki

To install the dokuwiki version of the project, place the files in the `\dokuwiki\data\pages\` directory of your DokuWiki installation.

# Overview of the AI-based Data Management System

This tool provides AI-assisted management of the pages. It uses the Together AI API (can be replaced by another other API in the `settings.py` file) with the DeepSeek V3 model to process and organize product and process information.

1. **Product and Process Page Generation** `generate_page.py`
   - Automatically creates structured Wiki pages from input data
   - Handles both products (pd_) and processes (ps_)

2. **Inconsistency Detection** `inconsistency_send_request_API.py`
   - Analyzes process files for structural inconsistencies
   - Identifies missing sections or formatting issues
   - Suggests corrections while preserving original content
   - Adds inconsistency reports to affected files

3. **Product Similarity Analysis** `similarity_send_request_API.py`
   - Identifies similar products in the database
   - Adds similarity information to product pages
   - Preserves existing similarity relationships
   - Provides explanations for similarity matches


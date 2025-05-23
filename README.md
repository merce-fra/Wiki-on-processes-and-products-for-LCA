# Project Overview

This project consists of three main parts:

1. **The Wiki**  
   A structured Wiki system to organize **processes and products**, that can be found in the public domain, to be used for the **inventory** part of a Life Cycle Assessment (LCA) study.
   You can access it directly in the [Wiki of this GitHub](https://github.com/merce-fra/Wiki-on-processes-and-products-for-LCA/wiki) or install it on dokuwiki.
   
   The pages are orginally generated in the dokuwiki (.txt) format and then automatically converted to the GitHub Wiki format (markdown) with the script `convert_to_github_wiki.py`. The source files for the pages are located in the `process/` and `product/` folders of this repository. The pages can be eddited by changing the text content of the .txt files. 
   
   Note that the GitHub Wiki is stored in a separate repository, which can be cloned using the link: https://github.com/merce-fra/Wiki-on-processes-and-products-for-LCA.wiki. Again, it is recommanded to modify the pages in the `process/` and `product/` folders of this repo and then automatically generate the files in the folder `Wiki-on-processes-and-products-for-LCA.wiki` using the script `convert_to_github_wiki.py`.

2. **The import function for Brightway-formatted data**  
   The script `import_data_wiki.py` (in the folder `Database_edition/`) relies on the brightway format (with the brightway import function) to generate files from brightway-compatible data in Excel. New pages are automatically created in folders `process_new/` and `product_new/` . If the pages are satisfactory, they should then be manually moved to the folders `process/` and `product/`. One can have a look at the folder `Database_edition/source_import/Example_bw/` for examples of Brightway-formatted excel files.

   If new pages are added in the folders `process/` and `product/`, the `ps_db.txt` and `pd_db.txt` files (where all the pages are listed) should be updated by running the script `update_database_list.py`.

3. **AI-based Wiki Edition**  
   This tool integrates AI to assist in the management of the Wiki. It automates tasks such as page generation (for not brightway-compliant data), inconsistency detection, and product similarity analysis, ensuring the wiki remains consistent, accurate, and up-to-date.

# Accessing the Wiki (on this GitHub) 

Click [here](https://github.com/merce-fra/Wiki-on-processes-and-products-for-LCA/wiki) to access the Wiki on this gihub.

# How to contribute

You can contribute by:
- Adding process or product pages (with or without using the python script to import the data). The pages should be added in the dokuwiki format (see the pages in the `process/` and `product/` folders of this repository).
- Improving the python scripts to automatically import data.

The standard way to proceed is the following:
1. Fork and clone this repo 
2. Create a new branch and make your changes and commit
3. Push your branch: `git push origin your-feature`
4. Open a Pull Request from your fork

Maintainers will review your proposal.
If the pages are accepted, maintainers will use the code `convert_to_github_wiki.py` to automatically update the Wiki of this GitHub.

# Installation on Dokuwiki

To install the dokuwiki version of the project, place the files in the `\dokuwiki\data\pages\` directory of your DokuWiki installation.

# Overview of the AI-based Data Management System

This tool provides AI-assisted management of the pages. It uses the Together AI API (can be replaced by another other API in the `settings.py` file) with the DeepSeek V3 model to process and organize product and process information.

1. **Product and Process Page Generation** `generate_page.py`
   - Automatically creates structured Wiki pages from input data

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


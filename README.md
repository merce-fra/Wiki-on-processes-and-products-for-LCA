# Project Overview
[Update (05/09/2025): We added a python script to automatically build a dependency tree starting from a chosen product or process node, with the output in the Mermaid .mmd format. The script is `Wiki-on-processes-and-products-for-LCA/Build_tree/build_lca_tree.py`. The output is generated in the wiki folder `Wiki-on-processes-and-products-for-LCA.wiki\out_tree\graph_name_of_the_node.mmd` (not visible on Github, you need to pull the wiki). If a product node can be produced by several processes (e.g., if several processes are listed in the 'List of processes' section of the product page), **this product node appears in red in the graph**. This indicates that one must then decide which subtree to follow among the possible options when building the system. Click [here](out_tree/graph_pd_dell_3620_computer.png) to see an example.]

[Update (20/08/2025): The dokuwiki format has been droped. The pages are now directly generated in markdown format in the folder `Wiki-on-processes-and-products-for-LCA.wiki`. The pages can now also be directly modifed from the online wiki.]

This project consists of three main parts:

1. **The Wiki**  
   A structured Wiki system to organize **processes and products**, that can be found in the public domain, to be used for the **inventory** part of a Life Cycle Assessment (LCA) study.
   You can access it directly in the [Wiki of this GitHub](https://github.com/merce-fra/Wiki-on-processes-and-products-for-LCA/wiki).
   
   Note that the GitHub Wiki is stored in a separate repository, which can be cloned using the link: https://github.com/merce-fra/Wiki-on-processes-and-products-for-LCA.wiki.

2. **The import function for Brightway-formatted data**  
   The script `import_data_wiki.py` (in the folder `Database_edition/`) relies on the brightway format (with the brightway import function) to generate files from brightway-compatible data in Excel. New pages are automatically created in folders `Wiki-on-processes-and-products-for-LCA.wiki/process_new/` and `Wiki-on-processes-and-products-for-LCA.wiki/product_new/` . If the pages are satisfactory, they should then be manually moved to the folders `Wiki-on-processes-and-products-for-LCA.wiki/process/` and `Wiki-on-processes-and-products-for-LCA.wiki/product/`. One can have a look at the folder `Database_edition/source_import/Example_bw/` for examples of Brightway-formatted excel files.

   If new pages are added in the folders `Wiki-on-processes-and-products-for-LCA.wiki/process/` and `Wiki-on-processes-and-products-for-LCA.wiki/product/`, the `ps_db.md` and `pd_db.md` files (where all the pages are listed) should be updated by running the script `update_database_list.py`. If some pages were updated online via the wiki, you should pull before performing changes.

3. **AI-based Wiki Edition**  
   This tool integrates AI to assist in the management of the Wiki. It automates tasks such as page generation (for not brightway-compliant data), inconsistency detection, and product similarity analysis, ensuring the wiki remains consistent, accurate, and up-to-date.

# Accessing the Wiki (on this GitHub)

Click [here](https://github.com/merce-fra/Wiki-on-processes-and-products-for-LCA/wiki) to access the Wiki on this gihub.

# How to contribute

You can contribute by:
- Adding process or product pages (with or without using the python script to import the data).
- Improving the python scripts to automatically import data.

The standard way to proceed is the following:
1. Clone this repo `Wiki-on-processes-and-products-for-LCA` AND the repo of the wiki pages `Wiki-on-processes-and-products-for-LCA.wiki` (a recommanded practice is to have a workspace folder where you put these two repos).
2. So far the wiki repo does not suport github merge features. We are investigating solutions. Don't hesitate to create an issue or contact the maintainters if you want to add data.


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


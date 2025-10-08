[Update (06/10/2025), **initial import tree**: The **initial scope and structure of an inventory** is an important information to keep. 
* For instance, the quantity used in a sub-process are often established with respect to the root product LCI scope. 
* Moreover, new processes may be added under an existing product. 

Therefore, we added the following elements in the structure of the wiki (see [pd_smd_thin_resistor](https://github.com/merce-fra/Wiki-on-processes-and-products-for-LCA/wiki/pd_smd_thin_resistor), [pd_livebox_6](https://github.com/merce-fra/Wiki-on-processes-and-products-for-LCA/wiki/pd_livebox_6), [Dell computer](https://github.com/merce-fra/Wiki-on-processes-and-products-for-LCA/wiki/pd_dell_3620_computer), [Process computer Loubet](https://github.com/merce-fra/Wiki-on-processes-and-products-for-LCA/wiki/ps_dell_3620_computer_loubet) for examples): 
* When importing an inventory, the LCI scope shoud be specified. 
* The root process of a root product is clearly indicated.
* This LCI scope is added under the original process of the root product of the inventory. 
* The original tree path is computed and added under the original process of the root product of the inventory (link to rn_ file).
* A link to the original root product and process nodes is added in each child process page.] 

[Update (05/09/2025): We added a python script to automatically build a **dependency tree**, with identification of alternative process nodes, starting from a chosen product or process page. See "3. Visualisation function" below.]

[Update (20/08/2025): The dokuwiki format has been droped. The pages are now directly generated in markdown format in the folder `Wiki-on-processes-and-products-for-LCA.wiki`. The pages can now also be directly modifed from the online wiki.]

# Project Overview

You can find some **slides presenting the wiki** [here](Slides_overview_wiki.pdf) (edited: 08/10/2025).

This project consists of four main parts:

1. **The Wiki**  
   A structured Wiki system to organize **processes and products**, that can be found in the public domain, to be used for the **life cycle inventory** (LCI) part of a Life Cycle Assessment (LCA) study.
   You can access it directly in the [Wiki of this GitHub](https://github.com/merce-fra/Wiki-on-processes-and-products-for-LCA/wiki). Note that the GitHub Wiki is stored in a separate repository, which can be cloned using the link: https://github.com/merce-fra/Wiki-on-processes-and-products-for-LCA.wiki.


2. **The import function for Brightway-formatted data**  
   The script `import_data_wiki.py` (in the folder `Database_edition/`) relies on the brightway format to generate wiki pages from brightway-compatible data in Excel. See the section "Details on the import script for Brightway-formatted data" below for technical details.

3. **Visualisation function**  
   The script `Wiki-on-processes-and-products-for-LCA/Build_tree/build_lca_tree.py` automatically build a **dependency tree** starting from a chosen product or process page, with **identification of alternative process nodes**. The output is in the Mermaid format. Click [here](https://github.com/merce-fra/Wiki-on-processes-and-products-for-LCA/wiki/out_tree/graph_pd_dell_3620_computer.svg) to see an example generated from the page [Dell computer](https://github.com/merce-fra/Wiki-on-processes-and-products-for-LCA/wiki/pd_dell_3620_computer).
   On the identification of alternative process nodes: If a **product node can be produced by several processes** (e.g., if several processes are listed in the 'List of processes' section of the product page), **this product node appears in red in the graph**. This indicates that one must then decide which subtree to follow among the possible options when building an inventory. The output is generated in the wiki folder `Wiki-on-processes-and-products-for-LCA.wiki\out_tree\graph_name_of_the_node.mmd` (not visible on Github, you need to pull the wiki).

4. **AI-based Wiki Edition**  
   This tool integrates AI to assist in the management of the Wiki. It automates tasks such as page generation (for not brightway-compliant data), inconsistency detection, and product similarity analysis, ensuring the wiki remains consistent, accurate, and up-to-date.

# Vision

Currently, performing the inventory step of a LCA includes the following challenges: 
1. **Several processes may exist to produce the same product**. 
2. **Scientific contributions** are often referenced by the end product, but may also **include sub-process data valuable** for other studies. 

This open wiki is designed to efficiently **list and compare multiple approaches** for performing the inventory of a product (1). It references data at **the process level** (2). By documenting these alternatives, researchers gain a valuable resource to easily compare existing options and select the most suitable approach for their needs.  
The following example illustrates this idea.

- **Electrolytic capacitors**  
  - The ecoinvent reference to produce an [electrolytic capacitors](https://github.com/merce-fra/Wiki-on-processes-and-products-for-LCA/wiki/pd_electrolytic_capacitors) was originally added when importing the inventory of the [Dell computer](https://github.com/merce-fra/Wiki-on-processes-and-products-for-LCA/wiki/pd_dell_3620_computer).  
  - A second process was imported as data from a research paper dedicated to this topic. The import script automatically detected that the process produces a product already present in the wiki.  
  - The `build_lca_tree.py` script (see "3. Visualisation function" above) produces a graph where two alternative processes are identified for the node [electrolytic capacitors](https://github.com/merce-fra/Wiki-on-processes-and-products-for-LCA/wiki/pd_electrolytic_capacitors) in the tree starting at the [Dell computer](https://github.com/merce-fra/Wiki-on-processes-and-products-for-LCA/wiki/pd_dell_3620_computer) node. See [here](https://github.com/merce-fra/Wiki-on-processes-and-products-for-LCA/wiki/out_tree/graph_pd_dell_3620_computer.svg) in red. This enables researchers studying the Dell computer to easily update their LCA with the alternative process for the electrolytic capacitors and compare the results.

- **GPU production**  
  - Two different processes are documented for the [GPU product](https://github.com/merce-fra/Wiki-on-processes-and-products-for-LCA/wiki/pd_gpu).  



# Tentative parametric approach 

[edited the 12/09/2025] The example of Appa’s parametric GPU model ([Appa GPU Build](https://appalca.github.io/in_depth/appa_build_in_depth.html)) has been added to the wiki to help identify necessary adaptations. This process is now listed under the [GPU product page](https://github.com/merce-fra/Wiki-on-processes-and-products-for-LCA/wiki/pd_gpu) of the wiki. In the [Appa GPU process branch](https://github.com/merce-fra/Wiki-on-processes-and-products-for-LCA/wiki/ps_nvidia_ai_gpu_chip_parameter_appa), the wiki page structure was updated as follow to handle the parametric model:
-	New “Parameters” section: List of the input parameter names.
-	New “parameters” field: Added to the metadata following a process name in the “Consumption” section.
-	New “Impact Flow” section: Allows for impact formulas based on parameters (e.g., see [logic_wafer](https://github.com/merce-fra/Wiki-on-processes-and-products-for-LCA/wiki/ps_logic_wafer_manufacturing)).
- Models (based on Appa’s “Parameter Matching”):
   -  If a model is used by a single process, it is added as a local model under that process.
   -	If a model is used by multiple processes, consider creating a Global Model section to avoid duplication.


# How to contribute

You can contribute by:
- Adding process or product pages (with or without using the python script to import the data).
- Improving the python scripts to automatically import data.

The standard way to proceed is the following:
1. Clone this repo `Wiki-on-processes-and-products-for-LCA` AND the repo of the wiki pages `Wiki-on-processes-and-products-for-LCA.wiki` (a recommanded practice is to have a workspace folder where you put these two repos).
2. So far the wiki repo does not support github merge features. We are investigating solutions. Don't hesitate to create an issue or contact the maintainters if you want to add data.

## Details on the import script for Brightway-formatted data

When using the script `import_data_wiki.py`, new pages are automatically created in folders `Wiki-on-processes-and-products-for-LCA.wiki/process_new/` and `Wiki-on-processes-and-products-for-LCA.wiki/product_new/`. If the pages are satisfactory, they should then be manually moved to the folders `Wiki-on-processes-and-products-for-LCA.wiki/process/` and `Wiki-on-processes-and-products-for-LCA.wiki/product/`. One can have a look at the folder `Database_edition/source_import/Example_bw/` for examples of Brightway-formatted excel files.

If new pages are added in the folders `Wiki-on-processes-and-products-for-LCA.wiki/process/` and `Wiki-on-processes-and-products-for-LCA.wiki/product/`, the `ps_db.md` and `pd_db.md` files (where all the pages are listed) should be updated by running the script `update_database_list.py`. If some pages were updated online via the wiki, you should pull before performing changes.


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


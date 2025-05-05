# -----------------------------------------------------------------------------
# Description: 
# [convert DokuWiki pages (in process/ and product/ folder) to GitHub Wiki markdown format]

# Author: [Vincent Corlay - Mitsubishi Electric R&D Centre Europe]
# -----------------------------------------------------------------------------

import os
import re

# Define base_path as a global variable
base_path = r"c:\xampp\htdocs\dokuwiki\data" #REPLACE WITH YOUR PATH

def clean_link_and_namespace(page, namespace):
    # Clean up page name and namespace
    page = page.strip().replace(' ', '_')
    namespace = namespace.strip().lower()
    
    # Map namespaces to proper categories
    namespace_mapping = {
        'product': 'Product',
        'process': 'process',
        'biosphere': 'biosphere'
    }
    
    return page, namespace_mapping.get(namespace, namespace)

def is_database_index(content):
    # Check if the content matches database index format
    first_lines = content.split('\n')[:3]
    return any(line.strip().endswith(':') and not line.startswith('**') for line in first_lines)

def convert_database_index_to_markdown(content):
    markdown_content = []
    current_section = None
    
    for line in content.split('\n'):
        # Handle section headers (ending with colon)
        if line.strip().endswith(':'):
            current_section = line.strip(':').strip()
            markdown_content.append(f"\n## {current_section}\n")
            continue
            
        # Handle simple links
        if line.strip().startswith('*[['):
            # Extract page name from simple link
            match = re.search(r'\*\[\[([^\]]+)\]\]', line)
            if match:
                page = match.group(1)
                # Determine folder based on prefix
                folder = 'product' if page.startswith('pd_') else 'process'
                markdown_line = f"* [{page}]({page})"#f"* [{page}]({folder}/{page})" #no folder support in wiki github 
                markdown_content.append(markdown_line)
                continue
                
        # Keep other lines unchanged
        if line.strip():
            markdown_content.append(line)
    
    return "\n".join(markdown_content)

def convert_dokuwiki_to_markdown(content):
    # Determine the type of file and use appropriate conversion
    if is_database_index(content):
        return convert_database_index_to_markdown(content)
        
    # Split content into lines
    lines = content.split('\n')
    markdown_content = []
    
    # Process title from first line if it exists
    if lines and lines[0].startswith('**'):
        title = lines[0].strip('*').strip()
        markdown_content.append(f"# {title}\n")
        lines = lines[1:]
    
    current_section = None
    
    for line in lines:
        # Handle section headers with underscores
        if line.startswith('__') and line.endswith('__'):
            section = line.strip('_').strip()
            markdown_content.append(f"\n## {section}\n")
            continue
            
        # Handle subsection headers with double asterisks
        if line.startswith('**') and line.endswith('**'):  # Removed extra parenthesis
            subsection = line.strip('*').strip()
            markdown_content.append(f"\n### {subsection}\n")
            continue
            
        # Handle DokuWiki links with metadata
        if '[[' in line and ']]' in line:
            if line.strip().startswith('*'):
                link_pattern = r'\[\[([^:]+):([^\]]+)\]\](.*)'
                match = re.search(link_pattern, line)
                if match:
                    namespace, page, metadata = match.groups()
                    page = page.strip()
                    namespace = namespace.strip()
                    # Clean up the link components
                    page, namespace = clean_link_and_namespace(page, namespace)
                    markdown_line = f"* [{page}]({page}){metadata}" #f"* [{page}]({namespace}/{page}){metadata}" #no folder support in wiki github 
                    markdown_content.append(markdown_line)
                    continue
            
        # Keep other lines unchanged
        markdown_content.append(line)
    
    return "\n".join(markdown_content)

def process_files(input_dir, output_dir, is_db_file=False):
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Process each file in the input directory
    for filename in os.listdir(input_dir):
        if filename.endswith('.txt'): 
            input_path = os.path.join(input_dir, filename)
            current_output_dir = output_dir
            
            
            # For db files, output to wiki_github root
            if is_db_file and ('pd_db' in filename or 'ps_db' in filename):
                current_output_dir = os.path.join(base_path, "Wiki-on-processes-and-products-for-LCA.wiki")
            
            # Change extension from .txt to .md for markdown
            output_filename = filename[:-4] + '.md'
            output_path = os.path.join(current_output_dir, output_filename)
            
            try:
                # Read content from input file
                with open(input_path, 'r', encoding='utf-8') as infile:
                    content = infile.read()
                
                # Convert content
                converted_content = convert_dokuwiki_to_markdown(content)
                
                # Write converted content to output file
                with open(output_path, 'w', encoding='utf-8') as outfile:
                    outfile.write(converted_content)
                    
                print(f'Converted {filename} to {output_filename}')
                
            except Exception as e:
                print(f'Error processing {filename}: {str(e)}')

def main():
    # Use the global base_path
    global base_path
    
    # Convert product pages
    product_input = os.path.join(base_path, "Wiki-on-processes-and-products-for-LCA", "product")
    product_output = os.path.join(base_path, "Wiki-on-processes-and-products-for-LCA.wiki", "product")
    process_files(product_input, product_output, True)
    
    # Convert process pages
    process_input = os.path.join(base_path, "Wiki-on-processes-and-products-for-LCA", "process")
    process_output = os.path.join(base_path, "Wiki-on-processes-and-products-for-LCA.wiki", "process")
    process_files(process_input, process_output, True)
    
    print("Conversion completed!")

if __name__ == "__main__":
    main()
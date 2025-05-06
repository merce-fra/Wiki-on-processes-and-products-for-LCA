# -----------------------------------------------------------------------------
# Description: 
#[check the product pages for similarities using AI]

# Author: [Vincent Corlay - Mitsubishi Electric R&D Centre Europe]
# -----------------------------------------------------------------------------

import os
import yaml
import requests
import json
from settings import TOGETHER_API_KEY, API_MODEL

#to be updated
base_path = "./" #EDIT THIS PATH IF NEEDED 

def load_yaml_file(file_path: str) -> dict:
    """Load and parse a YAML file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def call_together_ai(prompt, model_used=API_MODEL):
    """Call the Together AI API with the given prompt."""
    url = "https://api.together.xyz/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {TOGETHER_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model_used,
        "messages": prompt,
        "temperature": 0.3
        #"max_tokens": 2000
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        print(f"Error calling API: {str(e)}")
        return None

def get_product_files(base_path: str) -> list:
    """Get all product files from the products directory."""
    product_path = os.path.join(base_path, "product")
    files = []
    for file in os.listdir(product_path):
        if file.startswith("pd_") and file.endswith(".txt"):
            files.append(os.path.join(product_path, file))
    return files

def concatenate_files(files: list) -> str:
    """Concatenate content of all product files."""
    content = []
    for file in files:
        try:
            with open(file, 'r', encoding='utf-8') as f:
                content.append(f.read())
        except Exception as e:
            print(f"Error reading file {file}: {str(e)}")
    return "\n\n".join(content)

def parse_similar_products(api_response: str) -> dict:
    """Parse API response to extract source products and their similar products."""
    results = {}
    current_source = None
    
    for line in api_response.split('\n'):
        line = line.strip()
        if line.startswith('Name of the source product'):
            # Extract source product name
            current_source = line.split(':', 1)[1].strip().split()[0]
            results[current_source] = []
        elif line.startswith('Similar product') and current_source:
            # Parse similarity information
            try:
                # Split the line at the first colon
                _, similarity_info = line.split(':', 1)
                # Split at similarity score
                product_info, rest = similarity_info.split('similarity:', 1)
                # Get product name from before the comma
                similar_product = product_info.strip().split(',')[0]
                # Get similarity score
                similarity_score = rest.split(',')[0].strip()
                # Get explanation after "explanation:"
                explanation = rest.split('explanation:', 1)[1].strip()
                
                results[current_source].append({
                    'product': similar_product,
                    'similarity': similarity_score,
                    'explanation': explanation
                })
            except Exception as e:
                print(f"Error parsing similarity line: {line}\nError: {str(e)}")
                continue
    
    return results

def update_product_files(similarities: dict, base_path: str):
    """Update product files with similarity information."""
    for source_product, similar_products in similarities.items():
        if not similar_products:  # Skip if no similar products found
            continue
            
        # Construct file path
        file_path = os.path.join(base_path, "product", f"{source_product}.txt")
        if not os.path.exists(file_path):
            print(f"Warning: Source product file not found: {file_path}")
            continue
            
        try:
            # Read existing content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check if similarity section already exists
            if "__May be similar to the following products__" not in content:
                content += "\n\n__May be similar to the following products__"
            
            # Add similarity information
            similarity_section = "\n\n__May be similar to the following products__\n"
            for similar in similar_products:
                similarity_section += f"\n  * [[product:{similar['product']}]] - Similarity: {similar['similarity']}"
                similarity_section += f" - Explanation: {similar['explanation']}\n"
            
            # Replace existing similarity section or append new one
            if "__May be similar to the following products__" in content:
                parts = content.split("__May be similar to the following products__")
                content = parts[0] + similarity_section
            else:
                content += similarity_section
            
            # Write updated content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
            print(f"Updated similarity information for {source_product}")
            
        except Exception as e:
            print(f"Error updating file {file_path}: {str(e)}")

def main():
    # Load prompt template
    prompt_path = os.path.join("Database_edition","AI_treatment", "prompt", "my_prompt_similarity.yaml")
    prompt_template = load_yaml_file(prompt_path)

    # Get and concatenate product files
    product_files = get_product_files(base_path)
    concatenated_content = concatenate_files(product_files)

    # Format prompt
    messages = []
    for entry in prompt_template:
        content = entry["content"].replace("{context}", concatenated_content)
        messages.append({"role": entry["role"], "content": content})

    # Call API
    print("Sending request to Together API...")
    response = call_together_ai(messages)
    
    if response:
        # Save raw response
        output_path = os.path.join(base_path, "Database_edition","AI_treatment", "output", "product_analysis.txt")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(response)
        print(f"Raw analysis saved to {output_path}")
        
        # Parse response and update product files
        similarities = parse_similar_products(response)
        if similarities:
            update_product_files(similarities, base_path)
            print("Product files updated with similarity information")
        else:
            print("No similarity information found in API response")

if __name__ == "__main__":
    main()

# -----------------------------------------------------------------------------
# Description: 
#[To be used for non brightway-format data]
#[generate pages of product and processes using AI]
#[use prompt my_prompt_generate_pages.yaml, read the prompt to understand the template]
#[read source source_import/input_raw_data.txt]

# Author: [Vincent Corlay - Mitsubishi Electric R&D Centre Europe]
# -----------------------------------------------------------------------------


import os
import yaml
import requests
import json
from settings import TOGETHER_API_KEY, API_MODEL

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
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        print(f"Error calling API: {str(e)}")
        return None

def get_source_data(base_path: str) -> str:
    """Read the motherboard data file."""
    file_path = os.path.join(base_path, "Database_edition","source_import", "input_raw_data")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading source file: {str(e)}")
        return None

def is_content_different(existing_content: str, new_content: str) -> bool:
    """Compare contents ignoring whitespace differences."""
    def normalize(content):
        return ' '.join(line.strip() for line in content.splitlines() if line.strip())
    return normalize(existing_content) != normalize(new_content)

def normalize_name(name: str) -> str:
    """Normalize product/process names for consistency."""
    return name.lower().replace(" ", "_").replace("__", "_").replace(",", "")

def is_valid_process_line(line: str) -> bool:
    """Check if a line contains a valid process link."""
    line = line.strip()
    return line.startswith('*') and '[[process:' in line and ']]' in line

def create_or_update_file(base_path: str, subfolder: str, filename: str, content: str):
    """Create or update a file in the specified subfolder."""
    # Use new folders for output
    new_folder = subfolder + '_new'
    new_folder_path = os.path.join(base_path, new_folder)
    os.makedirs(new_folder_path, exist_ok=True)
    
    # Normalize filename
    filename = normalize_name(filename)
    if not filename.endswith('.txt'):
        filename += '.txt'
    
    # Check if file exists in original folder
    original_path = os.path.join(base_path, subfolder, filename)
    new_file_path = os.path.join(new_folder_path, filename)
    
    if os.path.exists(original_path):
        with open(original_path, 'r', encoding='utf-8') as f:
            existing_content = f.read()
            
        if not is_content_different(existing_content, content):
            print(f"File {filename} already exists with same content - skipping")
            return False

        # Special handling for product files that may already exist
        if subfolder == 'product':
            try:
                # Extract processes from original file
                existing_processes = []
                with open(original_path, 'r', encoding='utf-8') as f:
                    existing_content = f.read()
                    process_section = existing_content.split("__List of processes__")[1].split("__May be similar")[0]
                    for line in process_section.splitlines():
                        if line.strip().startswith("*") and "[[process:" in line:
                            existing_processes.append(line.strip())

                # Extract processes from new content
                new_processes = []
                process_section = content.split("__List of processes__")[1].split("__May be similar")[0]
                for line in process_section.splitlines():
                    if line.strip().startswith("*") and "[[process:" in line:
                        new_processes.append(line.strip())
                
                # If no changes in process list, skip
                if set(existing_processes) == set(new_processes):
                    print(f"Product file {filename} has identical process list - skipping")
                    return False
                
                # Combine processes without duplicates
                all_processes = list(dict.fromkeys(existing_processes + new_processes))
                
                # Create new content preserving format
                base, ext = os.path.splitext(filename)
                new_file_path = os.path.join(new_folder_path, f"{base}_modified{ext}")
                
                header = content.split("__List of processes__")[0]
                merged_content = f"{header.strip()}\n\n__List of processes__\n"
                for process in all_processes:
                    merged_content += f"{process}\n"
                merged_content += "\n__May be similar to the following products__\n"
                
                with open(new_file_path, 'w', encoding='utf-8') as f:
                    f.write(merged_content)
                print(f"Created merged product file in {new_folder}: {os.path.basename(new_file_path)}")
                return True

            except Exception as e:
                print(f"Error creating merged file {filename}: {str(e)}")
                return False
        else:
            # For process files, ensure standard sections are present
            process_sections = [
                "__Characteristics__",
                "__Technosphere Flow__",
                "__Biosphere Flow__",
                "__Information__"
            ]
            
            # Create new version with standard sections
            base, ext = os.path.splitext(filename)
            counter = 1
            while os.path.exists(os.path.join(new_folder_path, f"{base}_{counter}{ext}")):
                counter += 1
            new_file_path = os.path.join(new_folder_path, f"{base}_{counter}{ext}")
            
            new_content = content
            for section in process_sections:
                if section not in content:
                    new_content += f"\n\n{section}\n"
            
            with open(new_file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Created new version in {new_folder}: {os.path.basename(new_file_path)}")
            return True
    
    # For completely new files
    try:
        if subfolder == 'product':
            if "__List of processes__" not in content:
                content += "\n\n__List of processes__\n"
            if "__May be similar to the following products__" not in content:
                content += "\n\n__May be similar to the following products__\n"
        else:
            # Ensure process files have all required sections
            for section in ["__Characteristics__", "__Technosphere Flow__", "__Biosphere Flow__", "__Information__"]:
                if section not in content:
                    content += f"\n\n{section}\n"
        
        with open(new_file_path, 'w', encoding='utf-8') as f:
            f.write(content.strip() + '\n')
        print(f"Created new file in {new_folder}: {os.path.basename(new_file_path)}")
        return True
    except Exception as e:
        print(f"Error writing file {filename}: {str(e)}")
        return False

def parse_and_create_files(api_response: str, base_path: str):
    """Parse API response and create/update corresponding files."""
    lines = api_response.splitlines()
    current_file = None
    current_content = []
    
    for line in lines:
        line_stripped = line.strip()
        
        # Check for file name marker
        if line_stripped.startswith('name:'):
            # If we have a previous file, save it
            if current_file and current_content:
                subfolder = 'product' if current_file.startswith('pd_') else 'process'
                if create_or_update_file(base_path, subfolder, current_file, '\n'.join(current_content)):
                    print(f"Added {'product' if current_file.startswith('pd_') else 'process'} to database: {current_file}")
                current_content = []
            
            # Get new filename and normalize it
            current_file = normalize_name(line_stripped.split(':', 1)[1].strip())
            if not current_file.endswith('.txt'):
                current_file += '.txt'
            print(f"Processing file: {current_file}")
            continue
            
        # Check for end of file marker
        if line_stripped == "END FILE":
            if current_file and current_content:
                subfolder = 'product' if current_file.startswith('pd_') else 'process'
                if create_or_update_file(base_path, subfolder, current_file, '\n'.join(current_content)):
                    print(f"Added {'product' if current_file.startswith('pd_') else 'process'} to database: {current_file}")
                current_content = []
                current_file = None
            continue
            
        # Skip lines until we find a file
        if not current_file:
            continue
            
        # Add line to current content, preserving whitespace
        current_content.append(line)

def main():

    # Load prompt template
    prompt_path = os.path.join("Database_edition","AI_treatment", "prompt", "my_prompt_generate_pages.yaml")
    prompt_template = load_yaml_file(prompt_path)

    # Get source data
    source_data = get_source_data(base_path)
    if not source_data:
        return

    # Format prompt
    messages = []
    for entry in prompt_template:
        content = entry["content"].replace("{context}", source_data)
        messages.append({"role": entry["role"], "content": content})

    # Call API
    print("Sending request to Together API...")
    response = call_together_ai(messages)
    
    if response:
        # Save raw response
        output_path = os.path.join(base_path, "Database_edition","AI_treatment", "output", "generate_pages_analysis.txt")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(response)
        print(f"Raw analysis saved to {output_path}")
        
        # Parse response and create/update files
        parse_and_create_files(response, base_path)
        print("Files generated/updated successfully")

if __name__ == "__main__":
    main()

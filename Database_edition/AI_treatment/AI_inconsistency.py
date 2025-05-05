# -----------------------------------------------------------------------------
# Description: 
#[check the pages for inconsistancies using AI]

# Author: [Vincent Corlay - Mitsubishi Electric R&D Centre Europe]
# -----------------------------------------------------------------------------



import os
import yaml
import requests
import json
from settings import TOGETHER_API_KEY, API_MODEL

base_path = r"c:\xampp\htdocs\dokuwiki\data\Wiki-on-processes-and-products-for-LCA"

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

def get_process_files(base_path: str) -> list:
    """Get all process files from the processes directory."""
    process_path = os.path.join(base_path, "process")
    files = []
    if not os.path.exists(process_path):
        print(f"Warning: Process directory not found: {process_path}")
        return files

    for file in os.listdir(process_path):
        # Match files that have ps_ prefix and .txt extension in name
        if (file.lower().startswith("ps_")) and file.endswith(".txt"):
            # Return full file path 
            file_path = os.path.join(process_path, file)
            if os.path.isfile(file_path):  # Verify it's actually a file
                files.append(file_path)
                print(f"Found process file: {file}")
    if not files:
        print("Warning: No process files found")
    return files

def concatenate_files(files: list) -> str:
    """Concatenate content of all files, skipping those that already have inconsistency sections."""
    content = []
    for file in files:
        try:
            with open(file, 'r', encoding='utf-8') as f:
                file_content = f.read()
                # Only include files that don't already have inconsistency sections
                if "__Inconsistency__" not in file_content:
                    content.append(file_content)
                    print(f"Including file for analysis: {os.path.basename(file)}")
                else:
                    print(f"Skipping file (already has inconsistency section): {os.path.basename(file)}")
        except Exception as e:
            print(f"Error reading file {file}: {str(e)}")
    return "\n\n".join(content)

def parse_inconsistencies(api_response: str) -> list:
    """Parse API response to extract inconsistencies."""
    inconsistencies = []
    current_inconsistency = {}
    in_correction = False
    correction_lines = []
    
    lines = api_response.splitlines()  # Use splitlines() to preserve line endings
    for i, line in enumerate(lines):
        original_line = line  # Keep original line with spaces
        line = line.strip()
        if line.startswith('Inconsistency'):
            if current_inconsistency:
                if correction_lines:
                    # Join with newlines and preserve original formatting
                    current_inconsistency['correction'] = '\n'.join(correction_lines)
                inconsistencies.append(current_inconsistency)
            current_inconsistency = {}
            correction_lines = []
            in_correction = False
        elif line.startswith('Name of file:'):
            current_inconsistency['filename'] = line.split(':', 1)[1].strip()
        elif line.startswith('Identified inconsistency:'):
            current_inconsistency['description'] = line.split(':', 1)[1].strip()
        elif line.startswith('Formated process with correction:'):
            in_correction = True
            # Skip the current line and the opening """
            continue
        elif in_correction:
            if line == '"""':  # End of correction block
                in_correction = False
                continue
            correction_lines.append(original_line)  # Use original line with spaces
            
    if current_inconsistency:
        if correction_lines:
            current_inconsistency['correction'] = '\n'.join(correction_lines)
        inconsistencies.append(current_inconsistency)
    
    return inconsistencies

def update_process_files(inconsistencies: list, base_path: str):
    """Update process files with inconsistency information."""
    process_dir = os.path.join(base_path, "process")
    
    # Create a case-insensitive mapping of filenames to actual filenames
    file_map = {}
    if os.path.exists(process_dir):
        for file in os.listdir(process_dir):
            # Store both with and without .txt extension
            base_name = file[:-4] if file.endswith('.txt') else file
            file_map[base_name.lower()] = file
            file_map[file.lower()] = file

    for inconsistency in inconsistencies:
        filename = inconsistency.get('filename', '').strip()
        if not filename:
            continue
            
        # Try both with and without .txt extension
        filename_with_ext = filename if filename.endswith('.txt') else f"{filename}.txt"
        filename_without_ext = filename[:-4] if filename.endswith('.txt') else filename
        
        # Look for actual filename using both versions
        actual_filename = (file_map.get(filename_with_ext.lower()) or 
                         file_map.get(filename_without_ext.lower()))
        
        if not actual_filename:
            print(f"Warning: Process file not found: {filename}")
            continue
            
        file_path = os.path.join(process_dir, actual_filename)
        try:
            # Read existing content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Only add inconsistency section if it doesn't exist
            if "__Inconsistency__" not in content:
                # Get the corrected content from the inconsistency
                corrected_content = inconsistency.get('correction', '').strip()
                if not corrected_content:
                    continue
                    
                # Add inconsistency information section
                inconsistency_section = "\n\n__Inconsistency__\n"
                inconsistency_section += f"\n**Identified issue:** {inconsistency['description']}\n"
                inconsistency_section += f"\n**Suggested correction:**\n\n{corrected_content}\n"
                
                # Append the inconsistency section to the original content
                content += inconsistency_section
                
                # Write updated content
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                    
                print(f"Updated inconsistency information for {actual_filename}")
            
        except Exception as e:
            print(f"Error updating file {file_path}: {str(e)}")

def main():
    # Load prompt template with correct filename
    prompt_path = os.path.join("AI_treatment", "prompt", "my_prompt_inconsistency_processes.yaml")
    prompt_template = load_yaml_file(prompt_path)  # Store the result in prompt_template variable

    # Get and concatenate process files
    process_files = get_process_files(base_path)
    concatenated_content = concatenate_files(process_files)

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
        output_path = os.path.join(base_path, "AI_treatment", "output", "process_inconsistency_analysis.txt")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(response)
        print(f"Raw analysis saved to {output_path}")
        
        # Parse response and update process files
        inconsistencies = parse_inconsistencies(response)
        if inconsistencies:
            update_process_files(inconsistencies, base_path)
            print("Process files updated with inconsistency information")
        else:
            print("No inconsistency information found in API response")

if __name__ == "__main__":
    main()

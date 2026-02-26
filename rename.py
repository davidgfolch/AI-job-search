import os
import re

apps_dir = "apps"
env_files = [".env", ".env.example", ".env copy"]

# Base variables that are affected
base_vars = {
    "AI_ENRICH_TIMEOUT_JOB",
    "AI_ENRICH_TIMEOUT_CV_MATCH",
    "AI_MODEL_ID",
    "AI_MAX_NEW_TOKENS",
    "AI_TEMPERATURE",
    "AI_TOP_P",
    "AI_REPETITION_PENALTY",
    "AI_ENRICH_SKILL",
    "AI_SKILL_CATEGORIES",
    "AI_BATCH_SIZE",
    "AI_INPUT_MAX_LEN",
    "AI_ENRICH_GPU_CLEANUP",
    "AI_CV_MATCH",
    "AI_CV_MATCH_LIMIT",
    "AI_CV_MATCH_NEW_LIMIT",
    "AI_SKILL_ENRICH_LIMIT",
    "AI_ENRICH_TIMEOUT_SKILL",
    "AI_ENRICH_EXTRACT_TIMEOUT_SECONDS"
}

def get_new_var_name(app_name, var_name):
    # App name transformation
    if app_name.lower().startswith('ai'):
        app_suffix = app_name[2:].upper()
    else:
        app_suffix = app_name.upper()
        
    prefix = f"AI_{app_suffix}_"
    
    # Remove AI_ or AI_ENRICH_ from start
    if var_name.startswith("AI_ENRICH_"):
        suffix = var_name[len("AI_ENRICH_"):]
    elif var_name.startswith("AI_"):
        suffix = var_name[3:]
    else:
        suffix = var_name
        
    return prefix + suffix

def replace_in_file(filepath, replacements):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    new_content = content
    for old_v, new_v in replacements.items():
        # Match old variable name with word boundaries
        new_content = re.sub(r'\b' + re.escape(old_v) + r'\b', new_v, new_content)
        
    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated {filepath}")

app_replacements = {}

# Process each app
for root, dirs, files in os.walk(apps_dir):
    parts = root.split(os.sep)
    if len(parts) >= 2 and parts[0] == "apps":
        app_name = parts[1]
        
        # Only process ai apps
        if not app_name.lower().startswith("ai"):
            continue
            
        replacements = {}
        for old_v in base_vars:
            replacements[old_v] = get_new_var_name(app_name, old_v)
            
        app_replacements[app_name] = replacements
        
        for file in files:
            if file.endswith((".py", ".ts", ".tsx", ".md", ".json")):
                filepath = os.path.join(root, file)
                replace_in_file(filepath, replacements)

# Process global files (like apps/web and backend if they reference them)
# Actually, wait. The user only specified renaming in code.
# Are there any usages outside the specific ai apps? 
# Wait, web uses AI_ENRICH_SKILL in vite.config.ts. Which one does it mean? Probably it should read all of them or maybe just AI_ENRICH_SKILL for the main app.

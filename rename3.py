import os
import re

apps_dir = "apps"

def get_new_var_name(app_name, var_name):
    if app_name.lower().startswith('ai'):
        app_suffix = app_name[2:].upper()
    else:
        app_suffix = app_name.upper()
        
    prefix = f"AI_{app_suffix}_"
    
    if var_name.startswith("AI_ENRICH_"):
        suffix = var_name[len("AI_ENRICH_"):]
    elif var_name.startswith("AI_"):
        suffix = var_name[3:]
    else:
        suffix = var_name
        
    # User specifically requested AI_CVMATCHER_CV_MATCH* to become AI_CVMATCHER*
    # So if prefix is AI_CVMATCHER_ and suffix starts with CV_MATCH, remove the duplicate
    res = prefix + suffix
    if app_suffix == "CVMATCHER" and res.startswith("AI_CVMATCHER_CV_MATCH"):
        res = res.replace("AI_CVMATCHER_CV_MATCH", "AI_CVMATCHER", 1)
        
    return res

files_to_update = {}
env_vars_mapping = {}

pattern = re.compile(r'\b(AI_[A-Z0-9_]+)\b')

for root, dirs, files in os.walk(apps_dir):
    parts = root.split(os.sep)
    if len(parts) >= 2 and parts[0] == "apps":
        app_name = parts[1]
        
        if not app_name.lower().startswith("ai"):
            continue
            
        for file in files:
            if file.endswith((".py", ".ts", ".tsx", ".md", ".json", ".env")):
                # Skip massive generated files or modules if any
                if "node_modules" in root or ".pytest_cache" in root or "__pycache__" in root:
                    continue
                    
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                except UnicodeDecodeError:
                    try: 
                        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                    except Exception:
                        continue
                        
                matches = pattern.findall(content)
                if matches:
                    if filepath not in files_to_update:
                        files_to_update[filepath] = []
                    
                    for match in set(matches):
                        new_name = get_new_var_name(app_name, match)
                        files_to_update[filepath].append((match, new_name))
                        
                        if match not in env_vars_mapping:
                            env_vars_mapping[match] = set()
                        if new_name != match:
                            env_vars_mapping[match].add(new_name)

# Update App Files
for filepath, replacements in files_to_update.items():
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
    new_content = content
    replacements = list(set(replacements))
    # Replace longer matches first to prevent partial replacements
    replacements.sort(key=lambda x: len(x[0]), reverse=True)
    
    for old_v, new_v in replacements:
        if old_v != new_v:
            new_content = re.sub(r'\b' + re.escape(old_v) + r'\b', new_v, new_content)
        
    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated {filepath}")

# Update .env files
for env_filename in [".env", ".env.example", ".env copy"]:
    if not os.path.exists(env_filename):
        continue
    
    with open(env_filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    new_lines = []
    for line in lines:
        match = re.search(r'^(AI_[A-Z0-9_]+)=(.*)$', line.strip())
        if match:
            old_name = match.group(1)
            val = match.group(2)
            if old_name in env_vars_mapping and env_vars_mapping[old_name]:
                for new_name in sorted(env_vars_mapping[old_name]):
                    # Check if line already has leading/trailing whitespaces we want to keep
                    # For simplicity, recreating line with new name and retaining newline
                    new_lines.append(f"{new_name}={val}\n")
            else:
                if old_name not in env_vars_mapping:
                    new_lines.append(line)
        else:
            match_comment = re.search(r'^#\s*(AI_[A-Z0-9_]+)=(.*)$', line.strip())
            if match_comment:
                old_name = match_comment.group(1)
                val = match_comment.group(2)
                if old_name in env_vars_mapping and env_vars_mapping[old_name]:
                    for new_name in sorted(env_vars_mapping[old_name]):
                        new_lines.append(f"# {new_name}={val}\n")
                else:
                    if old_name not in env_vars_mapping:
                        new_lines.append(line)
            else:
                new_lines.append(line)
                
    with open(env_filename, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    print(f"Updated {env_filename}")

# Update special file vite.config.ts since web reads some AI variables but wasn't caught generically
import fileinput
vite_conf = "apps/web/vite.config.ts"
if os.path.exists(vite_conf):
    with open(vite_conf, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Needs AI_ENRICHNEW_SKILL or AI_ENRICH_SKILL in vite config? Let's just update common references to AI_ENRICH_SKILL if needed.
    # We will let user decide which app's config web uses. But currently it reads AI_ENRICH_SKILL
    if 'AI_ENRICH_SKILL' in content:
        new_content = content.replace('AI_ENRICH_SKILL', 'AI_ENRICHNEW_SKILL')
        with open(vite_conf, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated {vite_conf}")

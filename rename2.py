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
        
    return prefix + suffix

files_to_update = {}
env_vars_mapping = {} # old_name -> list of new_names

pattern = re.compile(r'\b(AI_[A-Z0-9_]+)\b')

for root, dirs, files in os.walk(apps_dir):
    parts = root.split(os.sep)
    if len(parts) >= 2 and parts[0] == "apps":
        app_name = parts[1]
        
        if not app_name.lower().startswith("ai"):
            continue
            
        for file in files:
            if file.endswith((".py", ".ts", ".tsx", ".md", ".json")):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                except UnicodeDecodeError:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        
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
                    # Check if the line already implicitly handles comments or what not
                    # To be safe, just add the new assignment keeping formatting
                    new_lines.append(f"{new_name}={val}\n")
            else:
                # If there are no new names mapped (e.g., variable not used in apps or already correct)
                # We can keep it or let it be. But the prompt says "rename all AI_* to AI_(apps/(*))".
                # It's possible some variables weren't seen if they are unused, or they are just kept.
                # Let's keep it if we didn't map it to anything.
                # Actually, some might be removed if we found mappings, since we replaced them with new_names.
                if old_name not in env_vars_mapping:
                    new_lines.append(line)
        else:
            # Check commented variables like # AI_...
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

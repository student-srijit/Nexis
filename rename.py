import os

def replace_in_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        new_content = content.replace('Nexis', 'Nexis')
        new_content = new_content.replace('Nexis', 'Nexis')
        new_content = new_content.replace('nexis', 'nexis')
        new_content = new_content.replace('nexis', 'nexis')

        if new_content != content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Updated {filepath}")
    except Exception as e:
        pass # ignore non-text files

def main():
    exclude_dirs = {'.git', 'node_modules', '__pycache__', 'venv', 'data', 'scratch'}
    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for file in files:
            if not file.endswith(('.py', '.js', '.jsx', '.md', '.html', '.json', '.txt', '.yml', '.css')):
                continue
            replace_in_file(os.path.join(root, file))

if __name__ == '__main__':
    main()

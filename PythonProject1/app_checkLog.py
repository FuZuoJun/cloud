import os
import re

BLOCK_DIR = "blocks/"

def get_sorted_block_files():
    def block_number(filename):
        match = re.match(r"(\d+)\.txt", filename)
        return int(match.group(1)) if match else -1

    files = [f for f in os.listdir(BLOCK_DIR) if re.match(r"\d+\.txt", f)]
    return sorted(files, key=block_number)

def show_logs():
    block_files = get_sorted_block_files()
    for filename in block_files:
        print(f"--- {filename} ---")
        with open(os.path.join(BLOCK_DIR, filename), 'r') as f:
            for line in f:
                print(line.strip())

if __name__ == "__main__":
    show_logs()

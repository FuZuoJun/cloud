import hashlib
import os
import sys
import re

BLOCK_DIR = "blocks/"
TRANSACTIONS_PER_BLOCK = 5

def sha256(data):
    return hashlib.sha256(data.encode()).hexdigest()

def get_sorted_block_files():
    def block_number(filename):
        match = re.match(r"(\d+)\.txt", filename)
        return int(match.group(1)) if match else -1

    files = [f for f in os.listdir(BLOCK_DIR) if re.match(r"\d+\.txt", f)]
    return sorted(files, key=block_number)

def create_block(prev_hash, block_number):
    filename = f"{block_number}.txt"
    filepath = os.path.join(BLOCK_DIR, filename)
    with open(filepath, 'w') as f:
        f.write(f"Sha256 of previous block: {prev_hash}\n")
        f.write("Next block: \n")  # 佔位，之後回頭補上
    return filename

def update_next_block_name(prev_filename, next_filename):
    path = os.path.join(BLOCK_DIR, prev_filename)
    with open(path, 'r') as f:
        lines = f.readlines()
    lines[1] = f"Next block: {next_filename}\n"
    with open(path, 'w') as f:
        f.writelines(lines)

def add_transaction(sender, receiver, amount):
    os.makedirs(BLOCK_DIR, exist_ok=True)
    block_files = get_sorted_block_files()

    if block_files:
        last_block = block_files[-1]
        path = os.path.join(BLOCK_DIR, last_block)
        with open(path, 'r+') as f:
            content = f.readlines()
            if len(content) - 2 < TRANSACTIONS_PER_BLOCK:  # 第1行 hash，第2行 next block
                f.write(f"{sender}, {receiver}, {amount}\n")
                return
            prev_hash = sha256(''.join(content))
    else:
        prev_hash = "GENESIS"

    # 新增區塊
    new_block_number = len(block_files) + 1
    new_block_name = create_block(prev_hash, new_block_number)

    # 回頭更新上一區塊的 next block 欄位
    if block_files:
        update_next_block_name(block_files[-1], new_block_name)

    # 寫入交易
    with open(os.path.join(BLOCK_DIR, new_block_name), 'a') as f:
        f.write(f"{sender}, {receiver}, {amount}\n")

# 用命令列輸入 sender, receiver, amount
if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python app_transaction.py <sender> <receiver> <amount>")
    else:
        add_transaction(sys.argv[1], sys.argv[2], sys.argv[3])

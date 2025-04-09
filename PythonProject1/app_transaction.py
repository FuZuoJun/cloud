import os
import hashlib

MAX_TX_PER_BLOCK = 5

def calculate_sha256(content):
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def get_last_block():
    blocks = sorted([f for f in os.listdir() if f.endswith('.txt')], key=lambda x: int(x.split('.')[0]))
    return blocks[-1] if blocks else None

def get_block_transactions(filename):
    with open(filename, 'r') as f:
        lines = f.readlines()
    return [line.strip() for line in lines[2:]]

def update_next_block_reference(block_filename, next_block_filename):
    with open(block_filename, 'r') as f:
        lines = f.readlines()
    lines[1] = f"Next block: {next_block_filename}\n"
    with open(block_filename, 'w') as f:
        f.writelines(lines)

def write_new_block(prev_block, new_filename, sender, receiver, amount):
    # 先更新上一個區塊的 "Next block" 欄位
    update_next_block_reference(prev_block, new_filename)

    # 重新讀入更新後的上一個區塊內容
    with open(prev_block, 'r') as f:
        updated_content = f.read()

    # 計算 SHA256 並寫入新區塊
    sha256 = calculate_sha256(updated_content)
    with open(new_filename, 'w') as f:
        f.write(f"Sha256 of previous block: {sha256}\n")
        f.write("Next block: \n")
        f.write(f"{sender}, {receiver}, {amount}\n")

def add_transaction(sender, receiver, amount):
    last_block = get_last_block()
    if not last_block:
        last_block = '1.txt'
        with open(last_block, 'w') as f:
            f.write("Sha256 of previous block: \n")
            f.write("Next block: \n")

    tx_list = get_block_transactions(last_block)
    if len(tx_list) < MAX_TX_PER_BLOCK:
        with open(last_block, 'a') as f:
            f.write(f"{sender}, {receiver}, {amount}\n")
    else:
        new_block = f"{int(last_block.split('.')[0]) + 1}.txt"
        write_new_block(last_block, new_block, sender, receiver, amount)

if __name__ == "__main__":
    import sys
    sender, receiver, amount = sys.argv[1], sys.argv[2], sys.argv[3]
    add_transaction(sender, receiver, amount)

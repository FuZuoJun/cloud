import hashlib
import os
import sys


def calculate_sha256(content):
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


def get_all_blocks():
    return sorted([f for f in os.listdir() if f.endswith('.txt') and f[0].isdigit()],
                  key=lambda x: int(x.split('.')[0]))


def add_transaction(sender, receiver, amount):
    blocks = get_all_blocks()
    last_block = blocks[-1]
    with open(last_block, 'r') as f:
        lines = f.readlines()

    # 去掉 meta 資訊，留下交易
    transactions = [line for line in lines[2:] if line.strip()]

    # 如果目前這個區塊已滿 5 筆交易，建立新區塊
    if len(transactions) >= 5:
        new_block_num = int(last_block.split('.')[0]) + 1
        new_block_name = f"{new_block_num}.txt"
        prev_hash = calculate_sha256(''.join(lines))
        with open(new_block_name, 'w') as f:
            f.write(f"Sha256 of previous block: {prev_hash}\n")
            f.write(f"Next block: {new_block_num + 1}.txt\n")
            f.write(f"{sender}, {receiver}, {amount}\n")
    else:
        # 加進目前區塊
        with open(last_block, 'a') as f:
            f.write(f"{sender}, {receiver}, {amount}\n")


def check_chain(reward_account):
    blocks = get_all_blocks()
    for i in range(len(blocks) - 1):
        with open(blocks[i], 'r') as f:
            content = f.read()
        calculated_hash = calculate_sha256(content)
        with open(blocks[i + 1], 'r') as f:
            next_lines = f.readlines()
        recorded_hash = next_lines[0].strip().split(': ')[1]
        if recorded_hash != calculated_hash:
            print(f"區塊鍊損壞，錯誤發生在區塊 {blocks[i + 1]}")
            return

    print(f"帳本鍊完整 ✅，angel 獎勵 {reward_account} 10 元")
    add_transaction("angel", reward_account, 10)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("使用方法: python3 app_checkChain.py <帳戶名稱>")
    else:
        check_chain(sys.argv[1])

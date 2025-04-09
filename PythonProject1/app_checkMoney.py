import os
import re

BLOCK_DIR = "blocks/"

def get_sorted_block_files():
    def block_number(filename):
        match = re.match(r"(\d+)\.txt", filename)
        return int(match.group(1)) if match else -1

    files = [f for f in os.listdir(BLOCK_DIR) if re.match(r"\d+\.txt", f)]
    return sorted(files, key=block_number)

def check_balance(account):
    balance = 0
    block_files = get_sorted_block_files()

    for filename in block_files:
        with open(os.path.join(BLOCK_DIR, filename), 'r') as f:
            lines = f.readlines()[2:]  # 忽略前兩行 header
            for line in lines:
                sender, receiver, amount = map(str.strip, line.strip().split(","))
                amount = int(amount)
                if sender == account:
                    balance -= amount
                if receiver == account:
                    balance += amount

    print(f"Balance for {account}: {balance}")
    return balance

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python app_checkMoney.py <account>")
    else:
        check_balance(sys.argv[1])

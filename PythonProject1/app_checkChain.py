import hashlib
import os
import re

BLOCK_DIR = "blocks/"

def sha256(data):
    return hashlib.sha256(data.encode()).hexdigest()

def get_sorted_block_files():
    def block_number(filename):
        match = re.match(r"(\d+)\.txt", filename)
        return int(match.group(1)) if match else -1

    files = [f for f in os.listdir(BLOCK_DIR) if re.match(r"\d+\.txt", f)]
    return sorted(files, key=block_number)

def check_chain():
    block_files = get_sorted_block_files()
    prev_hash = "GENESIS"

    for i, filename in enumerate(block_files):
        with open(os.path.join(BLOCK_DIR, filename), 'r') as f:
            lines = f.readlines()

        # 檢查前一個區塊的雜湊
        current_prev_hash = lines[0].strip().split(": ")[1]
        if current_prev_hash != prev_hash:
            print(f"Chain broken at {filename} (Invalid previous hash)")
            return False

        # 檢查 next block 名稱是否正確
        if i < len(block_files) - 1:
            expected_next = block_files[i + 1]
            recorded_next = lines[1].strip().split(": ")[1]
            if recorded_next != expected_next:
                print(f"Chain broken at {filename} (Next block mismatch: {recorded_next} vs {expected_next})")
                return False

        # 更新 prev_hash 為這一個區塊的 sha256
        prev_hash = sha256(''.join(lines))

    print("Chain is valid.")
    return True

if __name__ == "__main__":
    check_chain()

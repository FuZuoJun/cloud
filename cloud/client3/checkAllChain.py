import os
import shutil
import hashlib
import sys
from collections import defaultdict, Counter
import socket

BLOCK_FOLDER = "."
BLOCK_SIZE = 5

NODE_DIRS = {
    "client1": "../client1",
    "client2": "../client2",
    "client3": "../client3"
}

PORTS = {
    "client1": 8001,
    "client2": 8002,
    "client3": 8003
}

PEERS = {
    "client1": [("172.17.0.3", 8002), ("172.17.0.4", 8003)],
    "client2": [("172.17.0.2", 8001), ("172.17.0.4", 8003)],
    "client3": [("172.17.0.2", 8001), ("172.17.0.3", 8002)]
}

def get_node_info():
    name = os.path.basename(os.getcwd())
    if name not in NODE_DIRS:
        print("[ERROR] 請在 client1/client2/client3 資料夾內執行程式")
        sys.exit(1)
    return name, PORTS[name], PEERS[name]

def compute_sha256(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return hashlib.sha256(f.read().encode()).hexdigest()

def get_block_files(folder):
    return sorted([
        f for f in os.listdir(folder) if f.endswith(".txt") and f[:-4].isdigit()
    ], key=lambda x: int(x[:-4]))

def compute_chain_hashes(folder):
    hashes = []
    for file in get_block_files(folder):
        path = os.path.join(folder, file)
        hashes.append(compute_sha256(path))
    return tuple(hashes)

def gather_all_chain_hashes():
    chain_hashes = {}
    for node, path in NODE_DIRS.items():
        if os.path.exists(path):
            chain_hashes[node] = compute_chain_hashes(path)
        else:
            chain_hashes[node] = ()
    return chain_hashes

def majority_chain_group(chain_hashes):
    group = defaultdict(list)
    for node, chash in chain_hashes.items():
        group[chash].append(node)
    for chain, nodes in group.items():
        if len(nodes) > len(chain_hashes) / 2:
            return chain, nodes
    return None, []

def compare_chains(chain_hashes):
    print("\n帳本鏈內容比對結果：")
    nodes = list(chain_hashes.keys())
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            result = "Yes" if chain_hashes[nodes[i]] == chain_hashes[nodes[j]] else "No"
            print(f"{nodes[i]} vs {nodes[j]}: {result}")
    print("----")

def replace_local_ledger(from_dir):
    print(f"[動作] 清除本地帳本並複製較可信之帳本")
    for file in os.listdir(BLOCK_FOLDER):
        if file.endswith(".txt"):
            os.remove(os.path.join(BLOCK_FOLDER, file))
    for file in os.listdir(from_dir):
        if file.endswith(".txt"):
            shutil.copy(os.path.join(from_dir, file), os.path.join(BLOCK_FOLDER, file))
    print("[完成] 本地帳本已成功覆蓋!")

def verify_local_chain():
    print("[驗證] 檢查整條帳本鏈的SHA256")
    local_hashes = compute_chain_hashes(BLOCK_FOLDER)
    all_hashes = gather_all_chain_hashes()
    count = Counter(all_hashes.values())
    most_common = count.most_common(1)[0] if count else ((), 0)
    if count[local_hashes] >= 1:
        return True
    else:
        print("[錯誤] 本地帳本內容已被竄改，與任何節點皆不一致")
        return False

def add_transaction(sender, receiver, amount):
    tx = f"{sender}, {receiver}, {amount}"
    files = get_block_files(BLOCK_FOLDER)
    last_file = files[-1] if files else None
    if not last_file:
        with open("1.txt", "w", encoding="utf-8") as f:
            f.write("Sha256 of previous block: None\n")
            f.write("Next block: 2.txt\n")
            f.write(tx + "\n")
        return
    with open(last_file, "r+", encoding="utf-8") as f:
        lines = f.readlines()
        tx_lines = lines[2:] if len(lines) > 2 else []
        if len(tx_lines) < BLOCK_SIZE:
            f.write(tx + "\n")
        else:
            index = int(last_file.replace(".txt", ""))
            new_file = f"{index+1}.txt"
            with open(new_file, "w", encoding="utf-8") as nf:
                nf.write(f"Sha256 of previous block: {compute_sha256(last_file)}\n")
                nf.write(f"Next block: {index+2}.txt\n")
                nf.write(tx + "\n")

def broadcast_transaction(message, peers):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    for peer in peers:
        sock.sendto(message.encode("utf-8"), peer)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python checkAllChains.py <account>")
        sys.exit(1)

    account = sys.argv[1]
    name, port, peers = get_node_info()
    print(f"[{name}] 開始帳本一致性驗證...")

    chain_hashes = gather_all_chain_hashes()
    compare_chains(chain_hashes)
    local_chain = chain_hashes[name]
    majority_chain, majority_nodes = majority_chain_group(chain_hashes)

    if not majority_chain:
        print("[結果] ❌ 無法取得多數一致帳本，系統不可信任")
        sys.exit(1)

    if local_chain != majority_chain:
        print("[結果] ⚠️ 發現與多數帳本不一致，將進行覆蓋")
        for node in majority_nodes:
            if node != name:
                replace_local_ledger(NODE_DIRS[node])
                break
    else:
        print("[結果] ✅ 本地帳本已與多數一致")

    if verify_local_chain():
        print("[驗證成功] 本地鏈結正確，發放獎勵100元")
        add_transaction("angel", account, 100)
        tx = f"transaction angel {account} 100"
        broadcast_transaction(tx, peers)
    else:
        print("[錯誤] 本地帳本鏈結與任一節點不一致，疑似被竄改")

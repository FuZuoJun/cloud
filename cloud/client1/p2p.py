# p2p_all_in_one.py
# 功能：交易 + 帳本 + 共識機制 + 檢查鏈結 + 自動發獎 + 廣播同步 + 偵測篡改

import os
import sys
import socket
import threading
import hashlib
import shutil
from collections import defaultdict, Counter

BLOCK_SIZE = 5
NODE_LIST = ["client1", "client2", "client3"]

PORT_MAP = {
    8001: ("client1", "127.0.0.1"),
    8002: ("client2", "127.0.0.1"),
    8003: ("client3", "127.0.0.1")
}

class P2PNode:
    def __init__(self, name, ip, port, peers):
        self.name = name
        self.folder = "."
        self.ip = ip
        self.port = port
        self.peers = peers  # list of (peer_name, ip, port)

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            self.sock.bind((self.ip, self.port))
        except OSError:
            print(f"[ERROR] Port {self.port} is already in use. Exiting...")
            sys.exit(1)

    def start(self):
        threading.Thread(target=self._listen, daemon=True).start()
        while True:
            try:
                cmd = input(f"Enter a command [transaction/checkMoney/checkLog/checkChain/checkAllChain/exit]: ").strip()
                self.process_command(cmd)
            except Exception as e:
                print(f"[ERROR] {e}")

    def _listen(self):
        while True:
            try:
                data, addr = self.sock.recvfrom(2048)
                message = data.decode("utf-8")
                if message.startswith("transaction"):
                    self.append_to_ledger(message)
                    print(f"[{self.name}] Received and recorded: {message}")
            except Exception as e:
                print(f"[{self.name}] Listener error: {e}")

    def process_command(self, command):
        tokens = command.split()
        if not tokens:
            return
        cmd = tokens[0]

        if cmd == "transaction" and len(tokens) == 4:
            self.broadcast_transaction(command)
        elif cmd == "checkMoney" and len(tokens) == 2:
            print(f"{tokens[1]} has ${self.get_balance(tokens[1])}")
        elif cmd == "checkLog" and len(tokens) == 2:
            self.print_ledger(tokens[1])
        elif cmd == "checkChain" and len(tokens) == 2:
            if self.verify_chain():
                print("Chain OK. Rewarding...")
                self.broadcast_transaction(f"transaction angel {tokens[1]} 10")
        elif cmd == "checkAllChain" and len(tokens) == 2:
            self.check_all_chain(tokens[1])
        elif cmd == "exit":
            print("Bye!")
            sys.exit(0)
        else:
            print("Unknown or invalid command")

    def broadcast_transaction(self, tx_str):
        if self.append_to_ledger(tx_str):
            for peer_name, ip, port in self.peers:
                self.sock.sendto(tx_str.encode("utf-8"), (ip, port))
            print(f"[{self.name}] Broadcasted to peers: {[p[0] for p in self.peers]}")

    def append_to_ledger(self, tx_str):
        try:
            _, sender, receiver, amount = tx_str.strip().split()
            amount = int(amount)
            if sender != "angel" and self.get_balance(sender) < amount:
                print(f"[ERROR] {sender} has insufficient balance.")
                return False

            tx_record = f"{sender}, {receiver}, {amount}"
            files = self._get_block_files()
            last_file = files[-1] if files else None

            if not last_file:
                with open("1.txt", "w") as f:
                    f.write("Sha256 of previous block: None\n")
                    f.write("Next block: 2.txt\n")
                    f.write(tx_record + "\n")
                return True

            path = os.path.join(self.folder, last_file)
            with open(path, "r+", encoding="utf-8") as f:
                lines = f.readlines()
                tx_lines = lines[2:]
                if len(tx_lines) < BLOCK_SIZE:
                    f.write(tx_record + "\n")
                else:
                    index = int(last_file.replace(".txt", ""))
                    prev_hash = self.compute_sha256(path)
                    with open(f"{index+1}.txt", "w") as nf:
                        nf.write(f"Sha256 of previous block: {prev_hash}\n")
                        nf.write(f"Next block: {index+2}.txt\n")
                        nf.write(tx_record + "\n")
            return True
        except:
            return False

    def get_balance(self, target):
        balance = 0
        for file in self._get_block_files():
            with open(file, "r") as f:
                for line in f.readlines()[2:]:
                    parts = line.strip().split(", ")
                    if len(parts) == 3:
                        sender, receiver, amount = parts
                        if sender == target:
                            balance -= int(amount)
                        if receiver == target:
                            balance += int(amount)
        return balance

    def _get_block_files(self):
        return sorted([
            f for f in os.listdir(self.folder) if f.endswith(".txt") and f[:-4].isdigit()
        ], key=lambda x: int(x[:-4]))

    def compute_sha256(self, filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return hashlib.sha256(f.read().encode()).hexdigest()

    def print_ledger(self, account):
        for file in self._get_block_files():
            with open(file, "r") as f:
                lines = f.readlines()[2:]
                for line in lines:
                    if account in line:
                        print(f"{file}: {line.strip()}")

    def verify_chain(self):
        files = self._get_block_files()
        for i in range(1, len(files)):
            prev_hash = self.compute_sha256(files[i - 1])
            with open(files[i], "r") as f:
                line = f.readline().strip()
                if not line.endswith(prev_hash):
                    print(f"[錯誤] 區塊鏈損壞，遭竄改的可能是檔案：{files[i - 1]}")
                    return False
        last_file = files[-1]
        if self.compute_sha256(last_file) != hashlib.sha256(open(last_file, "r", encoding="utf-8").read().encode()).hexdigest():
            print(f"[錯誤] 最後一個區塊內容遭竄改：{last_file}")
            return False
        return True

    def check_all_chain(self, account):
        print("[比對中] 與其他 client 帳本進行對比：")
        local_hashes = self._get_chain_hash_sequence(self.folder)
        peer_hashes = defaultdict(list)
        node_hash_map = {}

        for node in NODE_LIST:
            folder_path = self.folder if node == self.name else os.path.join("..", node)
            if os.path.exists(folder_path):
                chain = self._get_chain_hash_sequence(folder_path)
                peer_hashes[chain].append(node)
                node_hash_map[node] = chain

        # 顯示 pairwise 比對結果
        printed = set()
        for i in NODE_LIST:
            for j in NODE_LIST:
                if i != j and (j, i) not in printed:
                    match = "✅" if node_hash_map.get(i) == node_hash_map.get(j) else "❌"
                    print(f"{i} vs {j}: {match}")
                    printed.add((i, j))

        # 進行共識檢查與處理
        majority_chain = None
        majority_nodes = []

        for chain, nodes in peer_hashes.items():
            if len(nodes) > len(NODE_LIST) // 2:
                majority_chain = chain
                majority_nodes = nodes
                break

        if majority_chain:
            if tuple(local_hashes) != majority_chain:
                print(f"[共識差異] 本地帳本不同於多數節點，正在同步...")
                self._replace_ledger_from(os.path.join("..", majority_nodes[0]))
            else:
                print("[共識一致] 本地帳本與多數節點一致 ✅")

            print(f"[驗證成功] {account} 獲得獎勵 100 元")
            self.broadcast_transaction(f"transaction angel {account} 100")
        else:
            print("[錯誤] 無法取得多數一致帳本，系統不可信任 ❌")

    def _replace_ledger_from(self, from_folder):
        for file in self._get_block_files():
            os.remove(file)
        for file in os.listdir(from_folder):
            if file.endswith(".txt"):
                shutil.copy(os.path.join(from_folder, file), file)

    def _get_chain_hash_sequence(self, folder):
        files = sorted([
            f for f in os.listdir(folder) if f.endswith(".txt") and f[:-4].isdigit()
        ], key=lambda x: int(x[:-4]))
        return tuple(self.compute_sha256(os.path.join(folder, f)) for f in files)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python p2p.py <port>")
        sys.exit(1)

    try:
        port = int(sys.argv[1])
    except:
        print("Invalid port number")
        sys.exit(1)

    if port not in PORT_MAP:
        print("Unsupported port. Use 8001, 8002, or 8003")
        sys.exit(1)

    name, ip = PORT_MAP[port]
    peers = [(PORT_MAP[p][0], PORT_MAP[p][1], p) for p in PORT_MAP if p != port]

    node = P2PNode(name, ip, port, peers)
    node.start()

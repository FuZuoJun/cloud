import os
import sys
import socket
import threading
import hashlib
import shutil
from collections import defaultdict, Counter

BLOCK_SIZE = 5
BLOCK_FOLDER = "."
PORTS = {
    8001: "client1",
    8002: "client2",
    8003: "client3"
}
PEERS = {
    8001: [("172.17.0.3", 8002), ("172.17.0.4", 8003)],
    8002: [("172.17.0.2", 8001), ("172.17.0.4", 8003)],
    8003: [("172.17.0.2", 8001), ("172.17.0.3", 8002)]
}

class P2PNode:
    def __init__(self, name, ip, port, peers):
        self.name = name
        self.folder = BLOCK_FOLDER
        self.ip = ip
        self.port = port
        self.peers = peers

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
                    print(f"[{self.name}] 收到廣播訊息: {message}")
                elif message.strip() == "get_last_hash":
                    last_file = self._get_block_files()[-1] if self._get_block_files() else None
                    if last_file:
                        hash_val = self.compute_sha256(os.path.join(self.folder, last_file))
                        self.sock.sendto(hash_val.encode("utf-8"), addr)
            except ConnectionResetError:
                print(f"[{self.name}] Warning: one of the peers forcibly closed the connection.")
            except Exception as e:
                print(f"[{self.name}] Listener error: {e}")

    def broadcast_transaction(self, tx_str):
        if self.append_to_ledger(tx_str):
            for peer in self.peers:
                try:
                    self.sock.sendto(tx_str.encode("utf-8"), peer)
                except Exception as e:
                    print(f"[{self.name}] Failed to send to {peer}: {e}")
            print(f"[{self.name}]轉帳以廣播給所有client")

    def get_balance(self, target):
        balance = 0
        for file in self._get_block_files():
            with open(os.path.join(self.folder, file), "r", encoding="utf-8") as f:
                for line in f.readlines()[2:]:
                    parts = line.strip().split(", ")
                    if len(parts) == 3:
                        sender, receiver, amount = parts
                        amount = int(amount)
                        if sender == target:
                            balance -= amount
                        if receiver == target:
                            balance += amount
        return balance

    def append_to_ledger(self, tx_str):
        try:
            _, sender, receiver, amount = tx_str.strip().split()
            amount = int(amount)
            if sender != "angel" and self.get_balance(sender) < amount:
                print(f"[ERROR] {sender}餘額不足，無法進行轉帳.")
                return False

            tx_record = f"{sender}, {receiver}, {amount}"
            files = self._get_block_files()
            last_file = files[-1] if files else None

            if not last_file:
                with open(os.path.join(self.folder, "1.txt"), "w", encoding="utf-8") as f:
                    f.write("Sha256 of previous block: None\n")
                    f.write("Next block: 2.txt\n")
                    f.write(tx_record + "\n")
                return True

            path = os.path.join(self.folder, last_file)
            with open(path, "r+", encoding="utf-8") as f:
                lines = f.readlines()
                tx_lines = lines[2:] if len(lines) > 2 else []
                if len(tx_lines) < BLOCK_SIZE:
                    f.write(tx_record + "\n")
                else:
                    index = int(last_file.replace(".txt", ""))
                    new_file = os.path.join(self.folder, f"{index+1}.txt")
                    prev_hash = self.compute_sha256(path)
                    with open(new_file, "w", encoding="utf-8") as nf:
                        nf.write(f"Sha256 of previous block: {prev_hash}\n")
                        nf.write(f"Next block: {index+2}.txt\n")
                        nf.write(tx_record + "\n")
            return True
        except Exception as e:
            print(f"[ERROR] Invalid transaction format: {e}")
            return False

    def _get_block_files(self):
        return sorted([
            f for f in os.listdir(self.folder)
            if f.endswith(".txt") and f[:-4].isdigit()
        ], key=lambda x: int(x[:-4]))

    def compute_sha256(self, filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return hashlib.sha256(f.read().encode()).hexdigest()

    def print_ledger(self, account):
        for file in self._get_block_files():
            with open(os.path.join(self.folder, file), "r", encoding="utf-8") as f:
                lines = f.readlines()[2:]
                relevant = [line.strip() for line in lines if account in line]
                if relevant:
                    print(f"--- {file} ---")
                    for line in relevant:
                        print(line)

    def verify_chain(self):
        files = self._get_block_files()
        if not files:
            return True

        for i in range(1, len(files)):
            prev_file = os.path.join(self.folder, files[i - 1])
            curr_file = os.path.join(self.folder, files[i])
            expected_hash = self.compute_sha256(prev_file)
            with open(curr_file, "r", encoding="utf-8") as f:
                first_line = f.readline().strip()
                if not first_line.endswith(expected_hash):
                    print(f"[錯誤] 區塊鏈損壞，遭竄改的可能是檔案：{files[i - 1]}")
                    return False

        last_file = os.path.join(self.folder, files[-1])
        try:
            with open(last_file, "r", encoding="utf-8") as f:
                content = f.read()
                recalculated = hashlib.sha256(content.encode()).hexdigest()
                expected = self.compute_sha256(last_file)
                if recalculated != expected:
                    print(f"[錯誤] 最後一個區塊內容遭竄改：{files[-1]}")
                    return False
        except Exception as e:
            print(f"[錯誤] 檢查最後區塊失敗：{e}")
            return False

        return True

    def check_all_chain(self, account):
        print("[檢查] 開始帳本一致性驗證...")
        all_hashes = self.gather_all_chain_hashes()
        self.compare_chains(all_hashes)
        local_chain = tuple(self.compute_chain_hashes(self.folder))
        majority_chain, majority_nodes = self.majority_chain_group(all_hashes)

        if not majority_chain:
            print("[結果] ❌ 無法取得多數一致帳本，系統不可信任")
            return

        if local_chain != majority_chain:
            print("[結果] ⚠️ 發現與多數帳本不一致，將進行覆蓋")
            for node in majority_nodes:
                if PORTS[self.port] != node:
                    self.replace_local_ledger(f"../{node}")
                    break
        else:
            print("[結果] ✅ 本地帳本已與多數一致")

        if tuple(self.compute_chain_hashes(self.folder)) in majority_chain:
            print("[驗證成功] 本地鏈結正確，發放獎勵100元")
            self.broadcast_transaction(f"transaction angel {account} 100")
        else:
            print("[錯誤] 本地帳本鏈結與任一節點不一致，疑似被竄改")

    def compute_chain_hashes(self, folder):
        return [self.compute_sha256(os.path.join(folder, file)) for file in self._get_block_files()]

    def gather_all_chain_hashes(self):
        result = {}
        for port, name in PORTS.items():
            path = f"../{name}"
            if os.path.exists(path):
                result[name] = tuple(self.compute_sha256(os.path.join(path, file)) for file in self._get_block_files_from(path))
            else:
                result[name] = ()
        return result

    def _get_block_files_from(self, folder):
        return sorted([
            f for f in os.listdir(folder)
            if f.endswith(".txt") and f[:-4].isdigit()
        ], key=lambda x: int(x[:-4]))

    def majority_chain_group(self, chain_hashes):
        group = defaultdict(list)
        for node, chash in chain_hashes.items():
            group[chash].append(node)
        for chain, nodes in group.items():
            if len(nodes) > len(chain_hashes) / 2:
                return chain, nodes
        return None, []

    def compare_chains(self, chain_hashes):
        print("\n帳本鏈內容比對結果：")
        nodes = list(chain_hashes.keys())
        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                result = "Yes" if chain_hashes[nodes[i]] == chain_hashes[nodes[j]] else "No"
                print(f"{nodes[i]} vs {nodes[j]}: {result}")
        print("----")

    def replace_local_ledger(self, from_dir):
        print("[動作] 清除本地帳本並複製較可信之帳本")
        for file in os.listdir(self.folder):
            if file.endswith(".txt"):
                os.remove(os.path.join(self.folder, file))
        for file in os.listdir(from_dir):
            if file.endswith(".txt"):
                shutil.copy(os.path.join(from_dir, file), os.path.join(self.folder, file))
        print("[完成] 本地帳本已成功覆蓋!")

    def process_command(self, command):
        tokens = command.split()
        if not tokens:
            return
        cmd = tokens[0]

        if cmd == "transaction":
            if len(tokens) != 4:
                print("Usage: transaction A B 10")
                return
            self.broadcast_transaction(command)
        elif cmd == "checkMoney":
            if len(tokens) != 2:
                print("Usage: checkMoney A")
                return
            print(f"{tokens[1]} has ${self.get_balance(tokens[1])}")
        elif cmd == "checkLog":
            if len(tokens) != 2:
                print("Usage: checkLog A")
                return
            self.print_ledger(tokens[1])
        elif cmd == "checkChain":
            if len(tokens) != 2:
                print("Usage: checkChain A")
                return
            if self.verify_chain():
                print(f"帳本鍊未有錯誤，{tokens[1]}獲得$10獎勵")
                self.broadcast_transaction(f"transaction angel {tokens[1]} 10")
        elif cmd == "checkAllChain":
            if len(tokens) != 2:
                print("Usage: checkAllChain A")
                return
            self.check_all_chain(tokens[1])
        elif cmd == "exit":
            print("Bye!")
            sys.exit(0)
        else:
            print("Unknown command")

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python p2p.py <port>")
        sys.exit(1)

    port = int(sys.argv[1])
    if port not in PORTS:
        print("[ERROR] 無效的port. 請輸入 8001, 8002 或 8003")
        sys.exit(1)

    name = PORTS[port]
    ip = "172.17.0.2"
    peers = PEERS[port]

    node = P2PNode(name, ip, port, peers)
    node.start()

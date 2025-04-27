import os
import sys
import socket
import threading
import hashlib
import shutil
from collections import defaultdict

BLOCK_SIZE = 5
BLOCK_FOLDER = "."
IPS = {
    "172.17.0.2": "client1",
    "172.17.0.3": "client2",
    "172.17.0.4": "client3"
}
PEERS = {
    "172.17.0.2": [("172.17.0.3", 8001), ("172.17.0.4", 8001)],
    "172.17.0.3": [("172.17.0.2", 8001), ("172.17.0.4", 8001)],
    "172.17.0.4": [("172.17.0.2", 8001), ("172.17.0.3", 8001)]
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
            self.sock.bind(("0.0.0.0", self.port))
        except OSError:
            print(f"[ERROR] Port {self.port} is already in use. Exiting...")
            sys.exit(1)

        # --- 新增用於checkAllChains ---
        self.chain_check_initiator = None
        self.responses = {}

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

                elif message.startswith("CHECK_CHAIN_REQUEST"):
                    _, initiator = message.strip().split()
                    final_hash = self.check_chain_and_return_hash()
                    response = f"CHECK_CHAIN_RESPONSE {initiator} {final_hash}"
                    for peer in self.peers:
                        self.sock.sendto(response.encode("utf-8"), peer)
                    self.sock.sendto(response.encode("utf-8"), ("127.0.0.1", self.port))  # 自己也要送自己一份

                elif message.startswith("CHECK_CHAIN_RESPONSE"):
                    _, initiator, hash_value = message.strip().split()
                    if self.chain_check_initiator == initiator:
                        sender_ip = addr[0]
                        self.responses[IPS[sender_ip]] = hash_value
                        self.compare_current_responses()

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
            print(f"[{self.name}] 轉帳已廣播給所有client")

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

        return True

    def check_chain_and_return_hash(self):
        if not self.verify_chain():
            print(f"[{self.name}] 本地帳本檢查失敗")
            return "ERROR"

        last_file = self._get_block_files()[-1] if self._get_block_files() else None
        if last_file:
            return self.compute_sha256(os.path.join(self.folder, last_file))
        return "EMPTY"

    def compare_current_responses(self):
        nodes = list(self.responses.keys())
        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                result = "Yes" if self.responses[nodes[i]] == self.responses[nodes[j]] else "No"
                print(f"{nodes[i]} vs {nodes[j]}: {result}")

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

        elif cmd == "checkAllChain" or cmd == "checkAllChains":
            if len(tokens) != 2:
                print("Usage: checkAllChains A")
                return
            self.chain_check_initiator = tokens[1]
            self.responses = {IPS[self.ip]: self.check_chain_and_return_hash()}
            broadcast_message = f"CHECK_CHAIN_REQUEST {tokens[1]}"
            for peer in self.peers:
                self.sock.sendto(broadcast_message.encode("utf-8"), peer)
            print(f"[{self.name}] 廣播發起checkAllChains...")

        elif cmd == "exit":
            print("Bye!")
            sys.exit(0)
        else:
            print("Unknown command")

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python p2p.py <IP>")
        sys.exit(1)

    ip = sys.argv[1]
    if ip not in IPS:
        print("[ERROR] 無效的IP. 請輸入 172.17.0.2, 172.17.0.3, 172.17.0.4")
        sys.exit(1)

    name = IPS[ip]
    port = 8001
    peers = PEERS[ip]

    node = P2PNode(name, ip, port, peers)
    node.start()

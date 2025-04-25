import os
import sys
import socket
import threading
import hashlib

BLOCK_SIZE = 5

class P2PNode:
    def __init__(self, name, ip, port, peers):
        self.name = name
        self.folder = "."
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
                cmd = input(f"Enter a command [transaction/checkMoney/checkLog/checkChain/exit]: ").strip()
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
            print(f"[{self.name}] Transaction broadcasted to peers.")

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
                print(f"[ERROR] {sender} has insufficient balance.")
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
                print("Chain OK. Rewarding...")
                self.broadcast_transaction(f"transaction angel {tokens[1]} 10")
        elif cmd == "exit":
            print("Bye!")
            sys.exit(0)
        else:
            print("Unknown command")

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

        # 驗證每一塊是否正確連接到前一塊
        for i in range(1, len(files)):
            prev_file = os.path.join(self.folder, files[i - 1])
            curr_file = os.path.join(self.folder, files[i])
            expected_hash = self.compute_sha256(prev_file)
            with open(curr_file, "r", encoding="utf-8") as f:
                first_line = f.readline().strip()
                if not first_line.endswith(expected_hash):
                    print(f"[錯誤] 區塊鏈損壞，遭竄改的可能是檔案：{files[i - 1]}")
                    return False

        # ✅ 新增：檢查最後一塊是否本身被改過（即使鏈結對）
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

if __name__ == '__main__':
    name = os.path.basename(os.getcwd())

    if name == "client1":
        ip, port = "172.17.0.2", 8001
        peers = [("172.17.0.3", 8002), ("172.17.0.4", 8003)]
    elif name == "client2":
        ip, port = "172.17.0.3", 8002
        peers = [("172.17.0.2", 8001), ("172.17.0.4", 8003)]
    elif name == "client3":
        ip, port = "172.17.0.4", 8003
        peers = [("172.17.0.2", 8001), ("172.17.0.3", 8002)]
    else:
        print("[ERROR] Please run this script inside client1, client2, or client3 folder.")
        sys.exit(1)

    node = P2PNode(name, ip, port, peers)
    node.start()

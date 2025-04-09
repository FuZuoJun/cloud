import os

def check_balance(user):
    balance = 0
    blocks = sorted([f for f in os.listdir() if f.endswith('.txt')], key=lambda x: int(x.split('.')[0]))
    for file in blocks:
        with open(file, 'r') as f:
            lines = f.readlines()[2:]
        for line in lines:
            parts = line.strip().split(', ')
            if len(parts) == 3:
                sender, receiver, amount = parts
                if sender == user:
                    balance -= int(amount)
                if receiver == user:
                    balance += int(amount)
    print(f"{user} 的餘額為: {balance}")

if __name__ == "__main__":
    import sys
    check_balance(sys.argv[1])

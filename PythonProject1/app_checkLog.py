import os

def check_log(user):
    blocks = sorted([f for f in os.listdir() if f.endswith('.txt')], key=lambda x: int(x.split('.')[0]))
    for file in blocks:
        with open(file, 'r') as f:
            lines = f.readlines()[2:]
        for line in lines:
            parts = line.strip().split(', ')
            if len(parts) == 3:
                sender, receiver, amount = parts
                if sender == user or receiver == user:
                    print(f"{file}: {sender} → {receiver} ：{amount}")

if __name__ == "__main__":
    import sys
    check_log(sys.argv[1])

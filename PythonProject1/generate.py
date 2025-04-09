import random
import string

# 隨機生成發送者、接收者名稱
def random_name():
    return ''.join(random.choices(string.ascii_uppercase, k=5))

# 隨機生成交易金額
def random_amount():
    return round(random.uniform(10, 1000), 2)

# 生成 100 筆交易紀錄
def generate_transactions(num_transactions=100):
    for _ in range(num_transactions):
        sender = random_name()
        receiver = random_name()
        amount = random_amount()
        add_transaction(sender, receiver, amount)

if __name__ == "__main__":
    generate_transactions()

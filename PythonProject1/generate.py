import random
import subprocess

clients = ['A', 'B', 'C']
num_transactions = 100

for _ in range(num_transactions):
    sender, receiver = random.sample(clients, 2)
    amount = random.randint(1, 50)
    subprocess.run(["python", "app_transaction.py", sender, receiver, str(amount)])

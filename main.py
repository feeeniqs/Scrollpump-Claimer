import requests
import random
import time
from web3 import Web3
from eth_account import Account

ABI = [
    {"inputs":[{"internalType":"address","name":"_signer","type":"address"}],"stateMutability":"nonpayable","type":"constructor"},
    {"inputs":[{"internalType":"address","name":"owner","type":"address"}],"name":"OwnableInvalidOwner","type":"error"},
    {"inputs":[{"internalType":"address","name":"account","type":"address"}],"name":"OwnableUnauthorizedAccount","type":"error"},
    {"anonymous":False,"inputs":[{"indexed":True,"internalType":"address","name":"previousOwner","type":"address"},{"indexed":True,"internalType":"address","name":"newOwner","type":"address"}],"name":"OwnershipTransferred","type":"event"},
    {"inputs":[],"name":"BONUS_AMOUNT","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"BONUS_AMOUNT_REFERRER","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"internalType":"uint256","name":"amount","type":"uint256"},{"internalType":"bytes","name":"signature","type":"bytes"},{"internalType":"address","name":"refUser","type":"address"}],"name":"claim","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[],"name":"claimReferralBonus","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"internalType":"address","name":"","type":"address"}],"name":"claimed","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"owner","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"internalType":"address","name":"","type":"address"}],"name":"referralAmount","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"internalType":"address","name":"","type":"address"}],"name":"referralBalance","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"renounceOwnership","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"internalType":"uint256","name":"newBonusAmount","type":"uint256"}],"name":"setBonusAmount","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"internalType":"uint256","name":"newBonusAmountReferrer","type":"uint256"}],"name":"setBonusAmountReferrer","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"internalType":"address","name":"newSignerAddress","type":"address"}],"name":"setSignerAddress","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[],"name":"signerAddress","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"token","outputs":[{"internalType":"contract SPumpMainToken","name":"","type":"address"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"internalType":"address","name":"newOwner","type":"address"}],"name":"transferOwnership","outputs":[],"stateMutability":"nonpayable","type":"function"}
]

contract_address = "0xCe64dA1992Cc2409E0f0CdCAAd64f8dd2dBe0093"  
rpc_url = "https://rpc.scroll.io"  
explorer_url = "https://scrollscan.com/tx/"  
w3 = Web3(Web3.HTTPProvider(rpc_url))

if not w3.is_connected():
    print("Не удалось подключиться к RPC")
    exit()

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://scrollpump.xyz",
    "Referer": "https://scrollpump.xyz/"
}

def read_private_keys(filename):
    
    try:
        with open(filename, 'r') as file:
            keys = [line.strip() for line in file if line.strip()]
        if not keys:
            print(f"Файл {filename} пуст.")
        else:
            print(f"Найдено {len(keys)} приватных ключей.")
        return keys
    except FileNotFoundError:
        print(f"Файл {filename} не найден.")
        return []

def get_signature(user_address):
    signature_url = f"https://api.scrollpump.xyz/api/Airdrop/GetSign?address={user_address}"
    try:
        response = requests.get(signature_url, headers=headers)
        if response.status_code == 200:
            json_data = response.json()
            if json_data.get("success"):
                data = json_data.get("data", {})
                signature = data.get("sign")
                amount = data.get("amount")
                if signature and amount:
                    return signature, int(amount)
        return None, None
    except Exception as e:
        print(f"Ошибка при отправке запроса для {user_address}: {e}")
        return None, None

def claim_airdrop(private_key, amount, signature):
    account = Account.from_key(private_key)
    contract = w3.eth.contract(address=contract_address, abi=ABI)
    
    try:
        nonce = w3.eth.get_transaction_count(account.address)
        # print(f"Nonce для {account.address}: {nonce}")
    except Exception as e:
        print(f"Ошибка при получении nonce для {account.address}: {e}")
        return
    
    try:
        # Увеличиваем цену газа
        gas_price = w3.eth.gas_price * 1.2 
        
        # Увеличенный лимит газа
        tx = contract.functions.claim(amount, signature, "0x0000000000000000000000000000000000000000").build_transaction({
            'from': account.address,
            'nonce': nonce,
            'gas': 1000000,
            'gasPrice': int(gas_price)
        })
        # print(f"Транзакция создана для {account.address} с лимитом газа {tx['gas']} и ценой газа {gas_price}")
    except Exception as e:
        print(f"Ошибка при создании транзакции для {account.address}: {e}")
        return

    try:
        # Подписание транзакции с приватным ключом
        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        # Вывод ссылки на транзакцию в ScrollScan
        #print(f"Транзакция отправлена: {explorer_url}{w3.to_hex(tx_hash)}")
        
        # Проверим статус транзакции
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        if receipt['status'] == 1:
            print(f"Транзакция подтверждена: {explorer_url}{w3.to_hex(tx_hash)}")
        else:
            print(f"Транзакция не прошла: {explorer_url}{w3.to_hex(tx_hash)}")
    except Exception as e:
        print(f"Ошибка при отправке транзакции для {account.address}: {e}")

# Основная функция
def main():
    print("Запуск основного скрипта...")
    private_keys = read_private_keys("keys.txt")
    
    if not private_keys:
        print("Файл с приватными ключами пуст или не найден.")
        return
    
    # Рандомное перемешивание ключей
    print("Перемешиваю ключи...")
    random.shuffle(private_keys)
    
    # Проход по каждому ключу
    for private_key in private_keys:
        account = Account.from_key(private_key)
        user_address = account.address
        print(f"\nКлейм для адреса: {user_address}")
        
        signature, amount = get_signature(user_address)
        
        if signature and amount:
            # Вывод информации о сумме токенов для клейма
            print(f"Сумма для клейма: {amount / (10 ** 18)} токенов")
            claim_airdrop(private_key, amount, signature)
            # Задержка между запросами
            delay = random.randint(60, 90)
            print(f"Ожидание {delay} секунд перед следующим запросом.")
            time.sleep(delay)
        else:
            print(f"Не удалось получить сигнатуру или сумму для {user_address}")

if __name__ == "__main__":
    main()

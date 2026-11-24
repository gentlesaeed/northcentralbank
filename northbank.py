from colorama import init, Fore, Style 

import random

init(autoreset=True)

accounts = {}

def create_account():
    print(Fore.CYAN + "\n===== CREATE NEW ACCOUNT =====")

    name = input(Fore.YELLOW + "Enter customer name: ")

    account_number = random.randint(100000,999999)

    while account_number in accounts:
        account_number = random.randint(100000,999999)

    balance = 0

    accounts[account_number] = {
        "name": name,
        "balance": balance
    }

    print(Fore.GREEN + "\nACCOUNT CREATED SUCCESSFULLY!")
    print(Fore.CYAN + "-------------------------")
    print(Fore.WHITE + f"customer Name: {name}")
    print(Fore.WHITE + f"Account Number: {account_number}")
    print(Fore.WHITE + f"Account Balance: $ {balance}") 
    print(Fore.CYAN + "-------------------------")

print(Fore.CYAN + "=========================")
print(Fore.YELLOW + " WELCOME TO NORTH CENTRAL BANK")
print(Fore.CYAN + "=========================")

print(Fore.GREEN + "1. create Account")
print(Fore. GREEN + "2. Login")
print(Fore.RED + "3. Exist")

print(Fore.CYAN + "=========================")

choice = input(Fore.YELLOW + "select an option (1-3): ")

if choice == "1":
    create_account()

elif choice =="2":
    print(Fore.GREEN + "Login system coming soon!")

elif choice == "3":
    print(Fore.RED + "Thank you for visiting our bank!")

else:
    print(Fore.RED + "Invalid optiont!")
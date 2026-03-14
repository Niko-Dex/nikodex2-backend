import getpass
import os
import re

from dotenv import load_dotenv
from passlib.context import CryptContext
from sqlalchemy import create_engine, insert, select
from sqlalchemy.orm import Session

from common.models import AccountType, User

load_dotenv()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

connection_str = "mysql+mysqlconnector://{}:{}@{}:{}/{}".format(
    os.environ["MYSQL_USER"],
    os.environ["MYSQL_PASS"],
    os.environ["MYSQL_URI"],
    os.environ["MYSQL_PORT"],
    "nikodex",
)

engine = create_engine(connection_str, echo=True)
session = Session(engine)
title = r"""
 _   _ _ _             _
| \ | (_| | _____   __| | _____  __
|  \| | | |/ / _ \ / _` |/ _ \ \/ /
| |\  | |   | (_) | (_| |  __/>  <
|_| \_|_|_|\_\___/ \__,_|\___/_/\_\
"""


def ask_pass():
    while True:
        password = getpass.getpass("Enter the new password for the account: ")
        password2 = getpass.getpass("Re-type new password: ")

        if password == password2:
            if len(password.strip()) == 0:
                print("Password cannot be empty!")
            else:
                return password
        else:
            print("New password do not match!")


def ask_username():
    while True:
        username = input("Enter username: ")
        if re.fullmatch(r"[A-Za-z0-9_]{1,255}", username):
            return username
        else:
            print("Invalid username!")


def ask_account_type() -> AccountType:
    while True:
        account_type = input("Enter account type (admin, user, dummy): ")
        output = AccountType.NORMAL
        if account_type.strip().lower() in ["admin", "user", "dummy"]:
            match account_type:
                case "admin":
                    if confirm(
                        "You are creating/changing to an ADMIN user.\nAre you sure?"
                    ):
                        output = AccountType.ADMIN
                    else:
                        continue
                case "dummy":
                    if confirm(
                        "You are creating/changing to a DUMMY user, which cannot be logged in like a normal user, and is usually created under specific conditions.\nAre you sure?"
                    ):
                        output = AccountType.DUMMY
                    else:
                        continue
            return output
        else:
            print("Invalid account type!")


def confirm(msg: str):
    while True:
        inp = input(f"{msg} (Y/N): ").strip().lower()
        if inp == "y":
            return True
        elif inp == "n":
            return False
        else:
            print("Invalid input!")


def input_choice(msg: str, choice: list[str]):
    _choice = [i.strip().lower() for i in choice]
    while True:
        inp = input(f"{msg} ({'/'.join(choice)}) (case-insensitive): ").strip().lower()
        if inp in _choice:
            return inp
        else:
            print("Invalid input!")


def get_user():
    id_or_username = input_choice(
        "Do you want to select the user by their ID or their USERNAME?",
        ["id", "username"],
    )
    user = None
    if id_or_username == "id":
        id = input("Enter user ID: ")
        user = session.execute(select(User).where(User.id == id)).scalar_one_or_none()
    elif id_or_username == "username":
        username = ask_username()
        user = session.execute(
            select(User).where(User.username == username)
        ).scalar_one_or_none()
    return user


def list_accounts():
    stmt = select(User)
    data = session.scalars(stmt).fetchall()
    print("")
    print("List of active accounts in database:")
    for user in data:
        print(" " * 2 + f'"{user.username}"')
        print(" " * 4 + f"ID: {user.id}")
        print(" " * 4 + f"Account type: {AccountType(user.account_type).name}")
    return


def add_account():
    print(
        "You are now creating an account. Please fill in the necessary informations below."
    )
    username = ask_username()
    password = ask_pass()
    account_type = ask_account_type()

    description = input("Enter a description for this user (optional): ")

    stmt = insert(User).values(
        username=username,
        hashed_pass=pwd_context.hash(password),
        description=description,
        account_type=account_type.value,
    )
    session.execute(stmt)
    session.commit()
    print("")
    print("Account created!")
    return


def edit_account():
    print("You are now editing a user.")
    user = get_user()
    if user is None:
        print("")
        print("User not found in database!")
        return

    new_username = user.username
    new_hashed_pass = user.hashed_pass
    new_description = user.description
    new_account_type = AccountType(user.account_type)

    change_username = confirm("Do you want to change their USERNAME?")
    if change_username:
        print(f"Old username: {user.username}")
        new_username = ask_username()

    change_password = confirm("Do you want to change their PASSWORD?")
    if change_password:
        print("Old password: ... we don't know lmao")
        new_password = ask_pass()
        new_hashed_pass = pwd_context.hash(new_password)

    change_description = confirm("Do you want to change their DESCRIPTION?")
    if change_description:
        print(f"Old description: {user.description}")
        new_description = input("Enter a new description for this user: ")

    change_account_type = confirm("Do you want to change their ACCOUNT TYPE?")
    if change_account_type:
        print(f"Old account type: {AccountType(user.account_type).name}")
        new_account_type = ask_account_type()

    user.username = new_username
    user.hashed_pass = new_hashed_pass
    user.description = new_description
    user.account_type = new_account_type.value
    session.commit()
    print("")
    print("Account edited!")
    return


def delete_account():
    print("You are now deleting a user.")
    user = get_user()
    if user is None:
        print("")
        print("User not found in database!")
        return
    if confirm(
        f'Are you sure you want to delete account "{user.username}" (ID: {user.id})? You CANNOT undo this action'
    ):
        session.delete(user)
        session.commit()
        print("")
        print("Account deleted!")
    else:
        print("")
        print("Canceled!")
    return


def exit_manager():
    print("See ya later, kbity :3")
    session.close()
    exit(0)


func_choice = {
    "1": {"func": list_accounts, "display_name": "List accounts"},
    "2": {"func": add_account, "display_name": "Add an account"},
    "3": {"func": edit_account, "display_name": "Edit an account"},
    "4": {"func": delete_account, "display_name": "Delete an account"},
    "5": {"func": exit_manager, "display_name": "Exit"},
}
print(title)
print("Account Manager")

while True:
    print("-" * 20)
    print("Please choose one of the functions below")
    for i in func_choice:
        print(" " * 2 + f"({i}): {func_choice[i]['display_name']}")
    choice = input("> ").strip()
    if choice not in func_choice:
        print("Invalid choice")
    else:
        func_choice[choice]["func"]()

import getpass
import os
import re

from dotenv import load_dotenv
from passlib.context import CryptContext
from sqlalchemy import create_engine, insert, select
from sqlalchemy.orm import Session

from common.models import User

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


def confirm(msg: str):
    while True:
        inp = input(f"{msg} (Y/N): ").strip().lower()
        if inp == "y":
            return True
        elif inp == "n":
            return False
        else:
            print("Invalid input!")


def list_accounts():
    stmt = select(User)
    data = session.scalars(stmt).fetchall()
    print("")
    print(
        f"List of active admin accounts in database: {', '.join([i.username for i in data])}"
    )
    return


def add_account():
    print("Please fill in the necessary informations below.")
    username = ask_username()
    password = ask_pass()
    description = input("Enter a description for this user (optional): ")

    stmt = insert(User).values(
        username=username,
        hashed_pass=pwd_context.hash(password),
        description=description,
        is_admin=True,
    )
    session.execute(stmt)
    session.commit()
    print("")
    print("Account created!")
    return


def edit_account():
    username = ask_username()
    user = session.execute(
        select(User).where(User.username == username)
    ).scalar_one_or_none()
    if user is None:
        print("")
        print("User not found in database!")
        return

    description = input("Enter a new description for this user: ")
    password = ask_pass()

    user.hashed_pass = pwd_context.hash(password)
    user.description = description
    session.commit()
    print("")
    print("Account edited!")
    return

def make_user_admin():
    username = ask_username()
    user = session.execute(
        select(User).where(User.username == username)
    ).scalar_one_or_none()
    if user is None:
        print("")
        print("User not found in database!")
        return

    bool_str = input("Admin or not (true or false):")
    bool_str = bool_str.lower()
    if bool_str == "true":
        user.is_admin = True
        session.commit()
    elif bool_str == "false":
        user.is_admin = False
        session.commit()
    else:
        print("Not a valid option!")


def delete_account():
    username = ask_username()
    user = session.execute(
        select(User).where(User.username == username)
    ).scalar_one_or_none()
    if user is None:
        print("")
        print("User not found in database!")
        return
    if confirm(
        f"Are you sure you want to delete account with name {username}? You CANNOT undo this action"
    ):
        session.delete(user)
        session.commit()
        print("Account deleted!")
    else:
        print("Canceled!")
    return


def exit_manager():
    print("Closing...")
    session.close()
    exit(0)


func_choice = {
    "1": {"func": list_accounts, "display_name": "List admin accounts"},
    "2": {"func": add_account, "display_name": "Add an admin account"},
    "3": {"func": edit_account, "display_name": "Edit an admin account"},
    "4": {"func": delete_account, "display_name": "Delete an admin account"},
    "5": {"func": make_user_admin, "display_name": "Change an account's admin status'"},
    "6": {"func": exit_manager, "display_name": "Exit"},
}

print("Account manager for Nikodex")

while True:
    print("-" * 20)
    print("Please choose one of the functions below")
    for i in func_choice:
        print(f"({i}): {func_choice[i]['display_name']}")
    choice = input("> ").strip()
    if choice not in func_choice:
        print("Invalid choice")
    else:
        func_choice[choice]["func"]()

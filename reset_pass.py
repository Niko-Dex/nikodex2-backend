import os
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, text, select
from passlib.context import CryptContext
import getpass

from models import Niko, User

load_dotenv()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

connection_str = "mysql+mysqlconnector://{}:{}@{}:{}/{}" \
    .format(os.environ['MYSQL_USER'], os.environ['MYSQL_PASS'], os.environ['MYSQL_URI'], os.environ['MYSQL_PORT'], "nikodex")

engine = create_engine(connection_str, echo=True)

session = Session(engine)
stmt = select(Niko).join(Niko.abilities)

username = input("Enter the username of the account you want to change the password (leave it blank if you leave it at `admin`): ")
username = username.strip()
if len(username) == 0:
    username = "admin"

password = ""
while True:
    password = getpass.getpass("Enter the new password for the account: ")
    password2 = getpass.getpass("Re-type new password: ")

    if password == password2:
        if len(password.strip()) == 0:
            print("Password cannot be empty!")
        else:
            break
    else:
        print("New password do not match")

try:
    entity = session.execute(select(User).where(User.username == username)).scalar_one_or_none()
    if entity is None:
        print("Cannot found user!")
        exit(1)

    entity.hashed_pass = pwd_context.hash(password)
    session.commit()
except Exception:
    print("Problem while changing the username or password.")

print("Password changed successfully!")
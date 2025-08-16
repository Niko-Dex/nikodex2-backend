import os
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, text, select

from models import Niko

load_dotenv()

connection_str = "mysql+mysqlconnector://{}:{}@{}:{}/{}" \
    .format(os.environ['MYSQL_USER'], os.environ['MYSQL_PASS'], os.environ['MYSQL_URI'], os.environ['MYSQL_PORT'], "nikodex")
    
engine = create_engine(connection_str, echo=True)

session = Session(engine)
stmt = select(Niko).join(Niko.abilities)

for niko in session.scalars(stmt):
    print(niko)
    for ability in niko.abilities:
        print(ability)
# nikodex2-backend
Backend for Nikodex V2 in Python using FastAPI

## Dependecies
To setup the backend server, you'll need:
- Python 3
- MySQL

## Setup
1. (Recommended) Setup a virtual environment for the project
```bash
python -m venv virtual-env

# only run one of the following commands depending on the OS/shell you're using
source virtual-env/bin/activate # Linux ONLY (bash, zsh, ...)
source virtual-env/bin/activate.fish # Linux ONLY (fish)
virtual-env\Scripts\Activate.ps1 # Windows ONLY (powershell)
virtual-env\Scripts\activate # Windows ONLY (cmd)
```
2. Setup the MySQL database with the provided `server_schema.sql` file.
3. Install all the required dependecies
```bash
pip install -r requirements.txt
pip install "fastapi[standard]" # fastapi command line tool
```
4. Configure the server by creating a .env file with the following content (replace the brackets with actual data):
```
# MySQL server setup.
MYSQL_USER="<mysql_username>"
MYSQL_PASS="<mysql_password>"
MYSQL_URI="<mysql_host_or_url>"
MYSQL_PORT="<mysql_port>"

# IMPORTANT: You will need to pass in the origin of the dev or prod server for front-end here.
FASTAPI_ALLOWED_ORIGIN="<allowed_url_1>,<allowed_url_2>,..."
```
5. Run the dev server
```
fastapi dev server.py
```


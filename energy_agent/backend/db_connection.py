import os
from dotenv import load_dotenv
from langchain_community.utilities import SQLDatabase

# Load environment variables
load_dotenv()

def get_db_connection():
    """
    Establish a secure SQLDatabase connection.
    """
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_host = os.getenv("DB_HOST")
    db_name = os.getenv("DB_NAME")

    connection_string = f"postgresql://{db_user}:{db_password}@{db_host}/{db_name}?sslmode=require"
    return SQLDatabase.from_uri(connection_string)

# Initialize DB connection
db = get_db_connection()

import logging
import re
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import create_sql_query_chain
from langchain_core.tools import tool
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.db_connection import db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize LLM
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)

# Get allowed tables (security check)
ALLOWED_TABLES = db.get_usable_table_names()

@tool
def query_database(question: str) -> str:
    """
    Generates and executes an SQL query for the given question.
    
    - Ensures only safe table access.
    - Returns results in natural language.
    
    Example:
    User: "How many devices are active?"
    Agent: "There are 42 active devices."
    """
    logger.info(f"User question: {question}")
    sql_chain = create_sql_query_chain(llm, db)
    generated_sql = sql_chain.invoke({"question": question}).strip()
    
    # Remove markdown code fences if present
    generated_sql = re.sub(r"^```(sql)?\s*", "", generated_sql)
    generated_sql = re.sub(r"\s*```$", "", generated_sql)
    generated_sql = generated_sql.strip()
    
    logger.info(f"Generated SQL: {generated_sql}")
    
    try:
        result = db.run(generated_sql)
        logger.info(f"Query Result: {result}")
        return str(result)
    except Exception as sql_error:
        logger.error(f"SQL error: {sql_error}")
        raise sql_error
import logging
import re
import sys
import os

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import create_sql_query_chain
from langchain_core.tools import tool

# Add the project root to sys.path so that backend can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.db_connection import db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize LLM using the Gemini model
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)

# Get allowed tables (used for security/sanity check)
ALLOWED_TABLES = db.get_usable_table_names()

@tool
def query_database(question: str) -> str:
    """
    Generates and executes an SQL query for the given question.
    
    - Uses a SQL chain to generate a query based on the question.
    - Cleans up markdown formatting from the generated SQL.
    - Validates that the query starts with SELECT.
    - Executes the query on the database.
    - Returns results in natural language or a friendly error if something goes wrong.
    
    Example:
       User: "How many devices are active?"
       Agent: "There are 42 active devices."
    """
    logger.info(f"User question: {question}")
    
    # Generate SQL query using the LLM & SQL chain:
    sql_chain = create_sql_query_chain(llm, db)
    generated_sql = sql_chain.invoke({"question": question}).strip()
    
    # Remove markdown code fences (e.g. ```sql ... ```)
    generated_sql = re.sub(r"^```(sql)?\s*", "", generated_sql, flags=re.IGNORECASE)
    generated_sql = re.sub(r"\s*```$", "", generated_sql, flags=re.IGNORECASE)
    generated_sql = generated_sql.strip()
    
    # Validate that the generated SQL starts with SELECT.
    if not generated_sql.lower().startswith("select"):
        logger.error("Generated SQL does not start with SELECT. Aborting execution.")
        return ("I'm sorry, the query could not be executed as it does not appear to be a valid SQL SELECT statement. "
                "Please try rephrasing your question with more specific details.")
    
    logger.info(f"Generated SQL: {generated_sql}")
    
    try:
        result = db.run(generated_sql)
        logger.info(f"Query Result: {result}")
        return str(result)
    except Exception as sql_error:
        logger.error(f"SQL error: {sql_error}")
        return ("I'm sorry, I couldn't execute your query due to a database error. "
                "It appears your question might be too vague or formulated in a problematic way. "
                "Please try rephrasing it with more specific details.")
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

# Get filtered table names (excluding 'users' table)
def get_filtered_table_names():
    """Return a list of table names that the agent can access, excluding 'users'."""
    all_tables = db.get_usable_table_names()
    return [table for table in all_tables if table.lower() != 'users']

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
    
    # Check if database is available
    if db is None:
        logger.error("Database connection is not available")
        return "I'm sorry, but I can't access the database at the moment. Please try again later."
    
    # Refresh the allowed tables
    allowed_tables = get_filtered_table_names()
    logger.info(f"Allowed tables: {allowed_tables}")
    
    try:
        # Get table information for context
        table_info = db.get_table_info()
        
        # Create enhanced question with table info
        enhanced_question = f"{question}. Use the following database schema:\n{table_info}"
        
        # Generate SQL using LangChain's SQL query chain
        sql_chain = create_sql_query_chain(llm, db)
        generated_sql = sql_chain.invoke({"question": enhanced_question}).strip()
        
        # Remove markdown code fences
        generated_sql = re.sub(r"^```(sql)?\s*", "", generated_sql, flags=re.IGNORECASE)
        generated_sql = re.sub(r"\s*```$", "", generated_sql, flags=re.IGNORECASE)
        generated_sql = generated_sql.strip()
        
        # Validate that the generated SQL starts with SELECT
        if not generated_sql.lower().startswith("select"):
            logger.error("Generated SQL does not start with SELECT. Aborting execution.")
            return ("I'm sorry, I couldn't generate a valid query for your question. "
                    "Please try asking in a different way with more specific details.")
        
        logger.info(f"Final SQL: {generated_sql}")
        
        # Execute the query
        result = db.run(generated_sql)
        logger.info(f"Query Result: {result}")
        
        # Make the result more readable
        if isinstance(result, list):
            if len(result) == 0:
                return "No results found for your query."
            elif len(result) == 1 and len(result[0]) == 1:
                # Single value result
                return str(result[0][0])
        
        return str(result)
        
    except Exception as e:
        logger.error(f"Error in query_database: {str(e)}")
        return f"I'm sorry, I encountered an error: {str(e)}. Please try rephrasing your question."
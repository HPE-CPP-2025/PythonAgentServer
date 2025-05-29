import logging
import re
import sys
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import create_sql_query_chain
from langchain_core.tools import tool

# Add the project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.db_connection import db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize LLM
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)

@tool
def query_database(question):
    """
    Executes a database query based on a natural language question.
    
    Args:
        question (str): The natural language question or direct SQL query
        
    Returns:
        str: The query results as a string
    """
    logger.info(f"Processing query: {question}")
    
    try:
        # Check if input is direct SQL
        if question.strip().upper().startswith("SELECT"):
            sql_query = question.strip()
            logger.info(f"Direct SQL detected: {sql_query}")
        else:
            # Get the database schema
            table_info = db.get_table_info()
            
            # Generate SQL using LangChain's SQL chain
            sql_chain = create_sql_query_chain(llm, db)
            generated_sql = sql_chain.invoke({
                "question": f"{question}\n\nDatabase schema information:\n{table_info}"
            })
            
            # Clean up SQL (remove markdown formatting)
            sql_query = re.sub(r"```sql\s*|\s*```", "", generated_sql).strip()
            logger.info(f"Generated SQL: {sql_query}")
            
        # Security check - ensure we only allow SELECT queries
        if not sql_query.strip().upper().startswith("SELECT"):
            return "For security reasons, I can only execute SELECT queries."
            
        # Execute the query
        result = db.run(sql_query)
        logger.info(f"Query result: {result}")
        
        # Handle empty results
        if not result:
            return "No data found for your query."
            
        return str(result)
        
    except Exception as e:
        logger.error(f"Error executing query: {e}")
        return f"Error: {str(e)}"
import logging
import re
import sys
import os
import time
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.db_connection import db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-lite",  
    temperature=0,
    request_timeout=60,
    max_retries=3
)

# Call counter for debugging
sql_call_count = 0

def query_database_with_schema(question, hardcoded_schema):
    """
    Generate and execute SQL using the hardcoded schema
    
    Args:
        question (str): The natural language question with context
        hardcoded_schema (str): The hardcoded schema from prompt_templates.py
        
    Returns:
        str: The query results as a string
    """
    global sql_call_count
    sql_call_count += 1
    
    logger.info(f"SQL Tool Call #{sql_call_count}: Processing with hardcoded schema")
    
    try:
        sql_query = None
        
        # Check if input is already a direct SQL query
        if question.strip().upper().startswith("SELECT"):
            sql_query = question.strip()
            logger.info("Direct SQL query detected")
        else:
            # Generate SQL using LLM with hardcoded schema
            logger.info("Generating SQL using LLM with hardcoded schema...")
            
            try:
                time.sleep(1)  # Rate limiting
                
                # Create a custom prompt with hardcoded schema
                enhanced_question = f"""
                Given this database schema:
                {hardcoded_schema}
                
                User request: {question}
                
                Generate a PostgreSQL SELECT query. Important:
                - Use PostgreSQL syntax (EXTRACT, not strftime)
                - Include proper WHERE clauses for house_id if specified
                - Only return the SQL query without explanation
                """
                
                # Use LLM directly
                response = llm.invoke(enhanced_question)
                
                # Extract SQL from response
                sql_query = response.content.strip()
                
                # Clean up SQL (remove markdown formatting)
                sql_query = re.sub(r"```sql\s*|\s*```", "", sql_query).strip()
                sql_query = re.sub(r"```\s*|\s*```", "", sql_query).strip()
                
                logger.info(f"Generated SQL: {sql_query}")
                
            except Exception as llm_error:
                logger.error(f"LLM generation failed: {llm_error}")
                if "429" in str(llm_error) or "quota" in str(llm_error).lower():
                    return "Error: API rate limit exceeded. Please try again in a few minutes."
                elif "ResourceExhausted" in str(llm_error):
                    return "Error: API quota exceeded. Please wait a moment and try again."
                return f"Error generating SQL: {str(llm_error)}"
        
        if not sql_query or not sql_query.strip().upper().startswith("SELECT"):
            return "For security reasons, I can only execute SELECT queries."
        
        # Clean up SQL
        sql_query = sql_query.strip()
        if sql_query.endswith(';'):
            sql_query = sql_query[:-1]
            
        logger.info(f"Executing SQL: {sql_query}")
        
        # Execute the query
        result = db.run(sql_query)
        logger.info("Query executed successfully")
        
        # Handle empty results
        if not result:
            return "No data found for your query."
        
        # Format result nicely
        if isinstance(result, str):
            return result
        elif isinstance(result, list):
            if len(result) == 1 and isinstance(result[0], tuple) and len(result[0]) == 1:
                # Single value result
                return f"Result: {result[0][0]}"
            else:
                # Multiple results
                return str(result)
        
        return str(result)
        
    except Exception as e:
        logger.error(f"Error executing query: {e}")
        
        # Handle specific PostgreSQL errors
        if "strftime" in str(e):
            return "Error: PostgreSQL doesn't support strftime(). Use EXTRACT() function instead."
        elif "does not exist" in str(e):
            return f"Database error: {str(e)}. Please check table/column names."
        elif "syntax error" in str(e).lower():
            return f"SQL syntax error: {str(e)}"
        
        return f"Error: {str(e)}"

@tool
def query_database(question):
    """Legacy function for backward compatibility"""
    return query_database_with_schema(question, "")
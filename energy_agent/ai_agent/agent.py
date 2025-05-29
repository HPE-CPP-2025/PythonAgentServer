import logging
import re
import sys
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import initialize_agent
from langchain.tools import Tool

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from tools.sql_tool import query_database

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize LLM
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)

def get_schema_info():
    """Get comprehensive database schema information."""
    try:
        schema_query = "List all tables in the database with their column names and data types. Provide a clear structure overview."
        schema_result = query_database(schema_query)
        return schema_result
    except Exception as e:
        logger.error(f"Error getting schema info: {e}")
        return "Schema information unavailable. Please check database connection."

def validate_query_security(query_text, house_id=None):
    """Additional security validation for queries."""
    try:
        query_lower = query_text.lower()
        
        # Block dangerous SQL operations
        dangerous_keywords = ['drop', 'delete', 'insert', 'update', 'alter', 'truncate', 'create']
        for keyword in dangerous_keywords:
            if keyword in query_lower:
                return False, f"Operation '{keyword}' is not allowed"
        
        # Ensure house_id restriction is present when required
        if house_id and 'house_id' not in query_lower:
            return False, "Query must include house_id restriction"
        
        return True, "Query passed security validation"
        
    except Exception as e:
        logger.error(f"Security validation error: {e}")
        return False, f"Security validation failed: {str(e)}"

def ask_agent(user_question, house_id=None, max_iterations=8):
    """Uses the ReAct agent to answer database queries with proper schema context and security measures."""
    try:
        # Get database schema information upfront
        schema_info = get_schema_info()
        logger.info("Retrieved database schema information")
        
        def secure_query(question):
            """Secure query wrapper with proper context formatting and validation"""
            try:
                # Prepare schema context as informational background
                context_prefix = f"Context: You have access to a database with the following schema:\n{schema_info}\n\nNote: Energy values are in Watts.\n\n"
                
                if house_id:
                    # Add house_id restriction for user queries
                    secure_question = (
                        f"{context_prefix}"
                        f"User Request: {question}\n\n"
                        f"CRITICAL SECURITY REQUIREMENT: Only return data for house_id='{house_id}'. "
                        f"You MUST include WHERE house_id='{house_id}' in your SQL queries.\n"
                        f"Generate appropriate SQL SELECT queries based on the schema above."
                    )
                else:
                    # Admin mode - no house_id restriction
                    secure_question = (
                        f"{context_prefix}"
                        f"User Request: {question}\n\n"
                        f"Generate appropriate SQL SELECT queries based on the schema above."
                    )
                
                # Execute the query
                result = query_database(secure_question)
                
                # Validate the executed query for security (basic check)
                if house_id:
                    is_valid, validation_msg = validate_query_security(str(result), house_id)
                    if not is_valid:
                        logger.warning(f"Security validation failed: {validation_msg}")
                        return f"Security validation failed: {validation_msg}"
                    
                    logger.info(f"Query executed with house_id restriction enforced: {house_id}")
                
                return result
                
            except Exception as e:
                logger.error(f"Error in secure_query: {e}")
                return f"Error executing query: {str(e)}"
        
        def check_schema_tool(input_text):
            """Tool to provide database schema information"""
            return (
                f"Database Schema Overview:\n\n"
                f"{schema_info}\n\n"
                f"Key Information:\n"
                f"- Energy values are measured in Watts\n"
                f"- Use proper table and column names from the schema above\n"
                f"- Only SELECT queries are allowed for security\n"
                f"- When house_id is specified, ALL queries must include house_id filter\n"
                f"- Available tables include energy_readings, devices, houses, users, etc."
            )
        
        # Define agent tools
        tools = [
            Tool(
                name="check_database_schema",
                func=check_schema_tool,
                description="""
                ALWAYS use this tool FIRST to understand the database structure.
                Returns comprehensive information about available tables, columns, and data types.
                Essential for writing correct SQL queries.
                """
            ),
            Tool(
                name="query_database", 
                func=secure_query,
                description="""
                Execute database queries after checking the schema first.
                Guidelines:
                - Only use after checking database schema
                - Generate proper SQL SELECT statements
                - Use correct table and column names from schema
                - Energy values are in Watts
                - Include appropriate WHERE clauses
                - MUST include house_id filter when specified
                - Only SELECT queries allowed (no INSERT/UPDATE/DELETE)
                """
            )
        ]
        
        # Initialize the ReAct agent
        agent = initialize_agent(
            tools=tools,
            llm=llm,
            agent="zero-shot-react-description",
            verbose=True,
            max_iterations=max_iterations,
            early_stopping_method="generate",
            handle_parsing_errors=True
        )
        
        # Prepare comprehensive input message
        system_instructions = [
            "1. MANDATORY: Start by using 'check_database_schema' to understand the database structure",
            "2. Analyze the user question and identify what data is needed",
            "3. Use 'query_database' with proper SQL based on the schema",
            "4. Provide a clear, conversational response",
            "5. Include units (Watts) when discussing energy values",
            "6. Do NOT show raw SQL or technical details in your final answer"
        ]
        
        if house_id:
            system_instructions.extend([
                f"7. CRITICAL SECURITY: Only show data for house_id='{house_id}'",
                f"8. MANDATORY: Every SQL query MUST include WHERE house_id='{house_id}'",
                f"9. Failure to include house_id filter will result in security violation"
            ])
        
        input_message = (
            f"User Question: {user_question}\n\n"
            f"Instructions:\n" + "\n".join(system_instructions) + "\n\n"
            f"Remember: Always check the database schema first, then query based on that information."
        )
        
        # Execute the agent
        logger.info(f"Executing agent for question: {user_question} with house_id: {house_id}")
        response = agent.invoke({"input": input_message})
        
        # Return the agent's output
        return response.get("output", "No response generated")
        
    except Exception as e:
        logger.error(f"Agent execution error: {e}")
        return f"Sorry, I encountered an error while processing your request: {str(e)}. Please try rephrasing your question."
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

def ask_agent(user_question, house_id=None, max_iterations=6):
    """
    Uses the ReAct agent to answer database queries with appropriate security measures.
    """
    try:
        # Create a wrapper function to enforce house_id restrictions if needed
        def secure_query(question):
            if house_id:
                # Add security context for house_id restriction
                enhanced_question = (
                    f"{question}\n\n"
                    f"IMPORTANT: Only return data for house_id='{house_id}'. "
                    f"Make sure to include a WHERE clause with house_id='{house_id}' in your query."
                )
                return query_database(enhanced_question)
            else:
                # No restrictions (admin mode)
                return query_database(question)
        
        # Define the tool
        tools = [Tool(
            name="query_database",
            func=secure_query,
            description="""
            Queries the energy database to answer questions. Before using:
            1. First determine what information is needed
            2. Check the database schema if necessary
            3. Create an appropriate SQL query
            4. If Note that enrgy unit is Watts
            This tool only allows SELECT queries for security reasons.
            """
        )]
        
        # Set up the agent
        agent = initialize_agent(
            tools=tools,
            llm=llm,
            agent="zero-shot-react-description",
            verbose=True,
            max_iterations=max_iterations,
            early_stopping_method="generate",
        )
        
        # Prepare input with necessary context
        input_message = (
            f"{user_question}\n\n"
            f"Please provide a clear, conversational answer. "
            f"Don't show raw SQL or data structures in your final response."
        )
        
        # Execute the agent
        response = agent.invoke({"input": input_message})
        
        return response["output"]
        
    except Exception as e:
        logger.error(f"Agent error: {e}")
        return f"Sorry, I encountered an error: {str(e)}. Please try again."
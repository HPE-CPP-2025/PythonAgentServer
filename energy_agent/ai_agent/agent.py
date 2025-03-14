from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.agent_toolkits import create_sql_agent
from db_connection import get_db_connection
import os

load_dotenv()


def create_sql_agent_gemini():
    """
    Create a SQL agent using Google's Gemini model and the database connection.
    """
    # Load environment variables
    load_dotenv()
    
    # Get database connection
    db = get_db_connection()
    
    # Initialize Gemini model
    gemini = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash"
    )
    
    # Create SQL agent with Gemini
    agent = create_sql_agent(
        llm=gemini,
        db=db,
        agent_type="structured-chat-zero-shot-react-description",  # Gemini works best with this agent type
        verbose=True
    )
    
    return agent
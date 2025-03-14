import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import initialize_agent
from langchain.tools import Tool
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from tools.sql_tool import query_database
from tools.electricity_cost import calculate_electricity_cost

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize LLM
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)

# Create agent with the SQL tool
agent_executor = initialize_agent(
    tools=[query_database,calculate_electricity_cost],  # Attach SQL query function
    llm=llm,
    agent="zero-shot-react-description",  # Use valid agent type instead of "openai-tools"
    verbose=True  # Enable debugging output
)

def ask_agent(user_question):
    """
    Uses the agent to generate answers based on database queries.
    """
    try:
        response = agent_executor.invoke({"input": user_question})
        return response["output"]
    except Exception as e:
        logger.error(f"Agent error: {e}")
        return f"Error: {str(e)}"

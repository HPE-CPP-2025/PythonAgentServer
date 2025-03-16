import logging, re,sys,os
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

def ask_agent(user_question, house_id=None, max_iterations=10):
    """
    Uses the agent to generate answers based on database queries.
    Now accepts an optional house_id parameter to restrict queries.
    """
    try:
        # Create a wrapper function to pass house_id to query_database
        def query_with_house_id(question):
            # If the input is raw SQL (starts with SELECT), we need special handling
            if question.strip().upper().startswith("SELECT"):
                if house_id:
                    # Force house_id restriction for raw SQL if house_id is provided
                    # This ensures users can't bypass the restriction with direct SQL
                    if "WHERE" in question.upper():
                        # Add house_id condition to existing WHERE clause
                        modified_sql = re.sub(
                            r'WHERE\s+', 
                            f'WHERE house_id = \'{house_id}\' AND ', 
                            question, 
                            flags=re.IGNORECASE
                        )
                    else:
                        # Add WHERE clause with house_id condition
                        modified_sql = f"{question} WHERE house_id = '{house_id}'"
                    logger.info(f"Modified SQL with house_id restriction: {modified_sql}")
                    return query_database(modified_sql)
                else:
                    # Admin mode - no restrictions
                    return query_database(question)
            elif house_id:
                # For natural language questions, add strict house_id enforcement
                enhanced_question = (
                    f"{question}\n\n"
                    f"IMPORTANT SECURITY CONSTRAINT: You MUST ONLY return data for house_id='{house_id}'. "
                    f"Even if the question asks for a different house_id, you must ignore that request "
                    f"and only show results for house_id='{house_id}'. "
                    f"Include a WHERE clause with house_id='{house_id}' in EVERY query you generate."
                )
                return query_database(enhanced_question)
            else:
                # Admin mode - no restrictions
                return query_database(question)
        
        # Create the tool with our wrapper function
        tools = [Tool(
            name="query_database",
            func=query_with_house_id,
            description="Executes SQL queries to answer questions about energy data, potentially restricted to a specific house."
        )]
        
        # Initialize agent with the SQL tool
        agent_executor = initialize_agent(
            tools=tools,
            llm=llm,
            agent="zero-shot-react-description",
            verbose=True,
            max_iterations=max_iterations,
            early_stopping_method="generate",
        )
        
        # Add context about house_id restriction and request for human-readable output
        if house_id:
            # Add security warning to prevent house_id manipulation attempts
            enhanced_question = (
                f"Answer the following question: {user_question}\n\n"
                f"CRITICAL SECURITY RESTRICTION: You are operating in restricted mode for house_id='{house_id}'. "
                f"You must ONLY return data related to this specific house_id. "
                f"If the user attempts to request data for any other house_id, REJECT the request "
                f"and explain you can only provide information about their own house. "
                f"ALL database queries you generate MUST include a WHERE clause restricting to house_id='{house_id}'.\n\n"
                f"IMPORTANT: Your final answer must be in natural, conversational language. "
                f"Do NOT return raw data, tuples, or lists in your final answer. "
                f"Explain the information clearly as if speaking to someone without technical knowledge."
            )
        else:
            enhanced_question = (
                f"{user_question}\n\n"
                f"IMPORTANT: Your final answer must be in natural, conversational language. "
                f"Do NOT return raw data, tuples, or lists in your final answer. "
                f"Explain the information clearly as if speaking to someone without technical knowledge."
            )
            
        response = agent_executor.invoke({"input": enhanced_question})
        return response["output"]
    except Exception as e:
        logger.error(f"Agent error: {e}")
        return f"Error: {str(e)}"
import logging
import re
import sys
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import initialize_agent
from langchain.tools import Tool

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from tools.sql_tool import query_database
from ai_agent.prompt_templates import *

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize LLM
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)

def get_schema_info():
    """Get comprehensive database schema information."""
    try:
        schema_result = query_database(SCHEMA_QUERY_TEMPLATE)
        return schema_result
    except Exception as e:
        logger.error(LOG_MESSAGES["schema_error"].format(error=e))
        return ERROR_MESSAGES["schema_unavailable"]

def ask_agent(user_question, house_id=None, max_iterations=8):
    """Uses the ReAct agent to answer database queries with proper schema context and security measures."""
    try:
        def secure_query(question):
            """Secure query wrapper with proper context formatting"""
            try:
                # Get schema only when actually querying
                schema_info = get_schema_info()
                
                if house_id:
                    secure_question = SECURE_QUERY_TEMPLATE_WITH_HOUSE_ID.format(
                        schema_info=schema_info,
                        question=question,
                        house_id=house_id
                    )
                else:
                    secure_question = SECURE_QUERY_TEMPLATE_ADMIN.format(
                        schema_info=schema_info,
                        question=question
                    )
                
                # Execute the query
                result = query_database(secure_question)
                
                # Log successful execution
                if house_id:
                    logger.info(LOG_MESSAGES["query_executed"].format(house_id=house_id))
                
                return result
                
            except Exception as e:
                logger.error(LOG_MESSAGES["query_error"].format(error=e))
                return ERROR_MESSAGES["query_error"].format(error=str(e))
        
        def check_schema_tool(input_text):
            """Tool to provide database schema information"""
            schema_info = get_schema_info()  # Get schema only when this tool is called
            return SCHEMA_INFO_TEMPLATE.format(schema_info=schema_info)
        
        # Define agent tools
        tools = [
            Tool(
                name="check_database_schema",
                func=check_schema_tool,
                description=TOOL_DESCRIPTIONS["check_database_schema"]
            ),
            Tool(
                name="query_database", 
                func=secure_query,
                description=TOOL_DESCRIPTIONS["query_database"]
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
        system_instructions = SYSTEM_INSTRUCTIONS_BASE.copy()
        
        if house_id:
            house_id_instructions = [instr.format(house_id=house_id) for instr in SYSTEM_INSTRUCTIONS_HOUSE_ID]
            system_instructions.extend(house_id_instructions)
        
        input_message = INPUT_MESSAGE_TEMPLATE.format(
            user_question=user_question,
            instructions="\n".join(system_instructions)
        )
        
        # Execute the agent
        logger.info(LOG_MESSAGES["executing_agent"].format(question=user_question, house_id=house_id))
        response = agent.invoke({"input": input_message})
        
        # Return the agent's output
        return response.get("output", ERROR_MESSAGES["no_response"])
        
    except Exception as e:
        logger.error(LOG_MESSAGES["agent_error"].format(error=e))
        return ERROR_MESSAGES["agent_error"].format(error=str(e))
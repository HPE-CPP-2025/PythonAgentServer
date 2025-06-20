TOOL_DESCRIPTIONS = {
    "check_database_schema": """
                Use this tool ONLY if you need to understand the database structure for data queries.
                Returns comprehensive information about available tables, columns, and data types.
                Do NOT use if you can answer the question without database access.
                """,
    "query_database": """
                Use this tool ONLY when you need actual data from the database.
                Do NOT use for general questions that can be answered without data.
                Guidelines:
                - Use when you need specific energy readings, device data, consumption statistics, or PREDICTIONS
                - Generate proper SQL SELECT statements
                - Use correct table and column names from schema
                - Energy values are in Watts
                - Include appropriate WHERE clauses
                - MUST include house_id filter when specified
                - Only SELECT queries allowed (no INSERT/UPDATE/DELETE)
                - For predictions, use the 'predictions' table with predicted_power column
                """
}

SYSTEM_INSTRUCTIONS_BASE = [
    "IMPORTANT: Only use database tools if you specifically need data from the database.",
    "If you can answer the question with general knowledge, do NOT access any tools.",
    "1. Analyze if the user question requires actual data from the database",
    "2. If YES, use 'check_database_schema' then 'query_database'", 
    "3. If NO, answer directly without using any tools",
    "4. For PREDICTIONS or FORECASTS, always check the 'predictions' table in the database",
    "5. Provide a clear, conversational response",
    "6. Include units (Watts) when discussing energy values",
    "7. Do NOT show raw SQL or technical details in your final answer"
]

SYSTEM_INSTRUCTIONS_HOUSE_ID = [
    "8. CRITICAL SECURITY: Only show data for house_id='{house_id}'",
    "9. MANDATORY: Every SQL query MUST include WHERE house_id='{house_id}'",
    "10. Failure to include house_id filter will result in security violation"
]
HARDCODED_SCHEMA = """
Database Schema:

Table: devices
- device_id (bigint), device_name (character varying), device_type (character varying)
- power_rating (character varying), location (character varying), house_id (bigint)

Table: energy_readings
- device_id (bigint), timestamp (timestamp with time zone), voltage (double precision)
- current (double precision), power (double precision), energy (double precision)
- frequency (double precision), power_factor (double precision), house_id (bigint)

Table: houses
- house_id (bigint), house_name (character varying), location (character varying)

Table: predictions
- id (integer), device_id (bigint), timestamp (timestamp with time zone)
- predicted_power (real), prediction_time (timestamp with time zone), house_id (bigint)

"""

SECURE_QUERY_TEMPLATE_WITH_HOUSE_ID = """Context: You have access to a PostgreSQL database with the following schema:
{schema_info}

Note: Energy values are in Watts.
Database: PostgreSQL (use PostgreSQL date functions like EXTRACT, DATE_TRUNC)

User Request: {question}

CRITICAL SECURITY REQUIREMENT: Only return data for house_id='{house_id}'. 
You MUST include WHERE house_id='{house_id}' in your SQL queries.

Important: Use PostgreSQL syntax:
- For date filtering: WHERE EXTRACT(month FROM timestamp) = 3 AND EXTRACT(year FROM timestamp) = 2025
- NOT SQLite strftime() function

Generate appropriate SQL SELECT queries based on the schema above."""

SECURE_QUERY_TEMPLATE_ADMIN = """Context: You have access to a database with the following schema:
{schema_info}

Note: Energy values are in Watts.

User Request: {question}

Generate appropriate SQL SELECT queries based on the schema above."""

SCHEMA_INFO_TEMPLATE = """Database Schema Overview:

{schema_info}

Key Information:
- Energy values are measured in Watts
- Use proper table and column names from the schema above
- Only SELECT queries are allowed for security
- When house_id is specified, ALL queries must include house_id filter
- Available tables: api_keys, device_status, devices, email_verifications, energy_readings, houses, predictions, refresh_tokens, users
- For predictions/forecasts, use the 'predictions' table with 'predicted_power' column
- For energy data, use 'energy_readings' table with 'power' column"""

INPUT_MESSAGE_TEMPLATE = """User Question: {user_question}

Instructions:
{instructions}

Remember: Only access database tools if you specifically need data. Answer directly if possible."""

ERROR_MESSAGES = {
    "schema_unavailable": "Schema information unavailable. Please check database connection.",
    "query_error": "Error executing query: {error}",
    "agent_error": "Sorry, I encountered an error while processing your request: {error}. Please try rephrasing your question.",
    "no_response": "No response generated"
}

LOG_MESSAGES = {
    "schema_error": "Error getting schema info: {error}",
    "query_error": "Error in secure_query: {error}",
    "agent_error": "Agent execution error: {error}",
    "executing_agent": "Executing agent for question: {question} with house_id: {house_id}",
    "query_executed": "Query executed with house_id restriction: {house_id}"
}

# Main.py templates
MAIN_DEBUG_MESSAGES = {
    "received_request": "recieved request for house id {house_id}",
    "chat_history_count": "DEBUG: Chat history for {house_id}: {count} messages",
    "using_history": "DEBUG: Using chat history in query",
    "no_history": "DEBUG: No chat history found",
    "saved_chat": "DEBUG: Saved chat. Total messages for {house_id}: {count}"
}

MAIN_INSTRUCTION_TEMPLATE = "CONTEXT: Today's date is {today} and current time is {current_datetime}.\nIMPORTANT: If you can answer this question without needing any external data from the database, do NOT use any database tools. Only access the database if you specifically need energy data, device information, or consumption statistics.\n\n"

CHAT_HISTORY_FORMAT = "Previous Q: {query}\nPrevious A: {response}\n\n"

APP_MESSAGE = "Energy AI Agent is running!"
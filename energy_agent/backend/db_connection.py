import os
from dotenv import load_dotenv
from langchain_community.utilities import SQLDatabase
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import create_sql_query_chain
from langchain.prompts import ChatPromptTemplate

# Load environment variables
load_dotenv()

# Initialize database connection
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
db_host = os.getenv("DB_HOST")
db_name = os.getenv("DB_NAME")

# Connection string for PostgreSQL
connection_string = f"postgresql://{db_user}:{db_password}@{db_host}/{db_name}?sslmode=require"
db = SQLDatabase.from_uri(connection_string)

# Initialize the LLM
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0)

# Instead of using the agent, use a simpler SQL chain
def ask_database(question):
    try:
        print(f"Question: {question}")
        
        # Special case for listing tables
        if "list all tables" in question.lower():
            tables = db.get_usable_table_names()
            return {"output": f"Tables in the database: {', '.join(tables)}"}
        
        # Create a SQL chain
        sql_chain = create_sql_query_chain(llm, db)
        
        # Generate SQL query
        query = sql_chain.invoke({"question": question})
        print(f"Generated SQL (raw): {query}")
        
        # Clean up the query - remove "SQLQuery:" prefix if present
        if query.startswith("SQLQuery:"):
            query = query.replace("SQLQuery:", "").strip()
        print(f"Generated SQL (cleaned): {query}")
        
        # Execute the query
        result = db.run(query)
        print(f"Query Result: {result}")
        
        # Format the response
        response = {
            "query": query,
            "output": result
        }
        
        return response
    except Exception as e:
        print(f"Error while querying the database: {e}")
        return {"error": str(e)}

# Example query
print(ask_database("show all the avaialble tables in teh database"))

# Additional example queries
print(ask_database("How many devices are in the database?"))
print(ask_database("What's the average energy reading?"))
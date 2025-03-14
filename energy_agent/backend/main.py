from fastapi import FastAPI
from pydantic import BaseModel
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from ai_agent.agent import ask_agent


# Initialize FastAPI app
app = FastAPI()

# Request model for the query
class QueryRequest(BaseModel):
    query: str

@app.post("/ask")
def ask_energy_agent(request: QueryRequest):
    """
    API endpoint to interact with the AI agent.
    """
    response = ask_agent(request.query)
    return {"query": request.query, "response": response}

# Root endpoint
@app.get("/")
def root():
    return {"message": "Energy AI Agent is running!"}

# filepath: c:\MY DRIVE\HPE\energy_agent\backend\main.py
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


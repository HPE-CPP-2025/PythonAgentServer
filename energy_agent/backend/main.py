from fastapi import FastAPI
from pydantic import BaseModel
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from ai_agent.agent import ask_agent


# Initialize FastAPI app
app = FastAPI()

# Updated Request model to include optional house_id
class QueryRequest(BaseModel):
    query: str
    house_id: str = None  # Optional house_id parameter

@app.post("/ask")
def ask_energy_agent(request: QueryRequest):
    """
    API endpoint to interact with the AI agent.
    """
    response = ask_agent(request.query, request.house_id)  # Pass house_id to the agent
    return {"query": request.query, "response": response}

# Root endpoint
@app.get("/")
def root():
    return {"message": "Energy AI Agent is running!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

    
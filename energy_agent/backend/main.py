from fastapi import FastAPI
from pydantic import BaseModel
import os
import sys
import time
import threading
from collections import defaultdict

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from ai_agent.agent import ask_agent

# Initialize FastAPI app
app = FastAPI()

# Simple memory system
chat_sessions = defaultdict(list)  # {house_id: [{"query": "", "response": "", "time": timestamp}]}
session_timers = {}  # {house_id: timestamp}

def clear_session(house_id):
    """Clear chat session for house_id"""
    if house_id in chat_sessions:
        del chat_sessions[house_id]
    if house_id in session_timers:
        del session_timers[house_id]

def start_timer(house_id):
    """Start 15-minute timer for session cleanup"""
    if house_id in session_timers:
        session_timers[house_id].cancel()
    
    timer = threading.Timer(900, clear_session, args=[house_id])  # 900 seconds = 15 minutes
    timer.start()
    session_timers[house_id] = timer

def get_chat_history(house_id):
    """Get formatted chat history for house_id"""
    if not house_id or house_id not in chat_sessions:
        return ""
    
    history = ""
    for chat in chat_sessions[house_id]:
        history += f"Previous Q: {chat['query']}\nPrevious A: {chat['response']}\n\n"
    return history

# Updated Request model to include optional house_id
class QueryRequest(BaseModel):
    query: str
    house_id: str = None

@app.post("/ask")
def ask_energy_agent(request: QueryRequest):
    """API endpoint to interact with the AI agent."""
    
    # Get chat history
    chat_history = get_chat_history(request.house_id)
    print(f"DEBUG: Chat history for {request.house_id}: {len(chat_sessions.get(request.house_id, []))} messages")
    
    # Add history and instruction to query
    instruction = "IMPORTANT: If you can answer this question without needing any external data from the database, do NOT use any database tools. Only access the database if you specifically need energy data, device information, or consumption statistics.\n\n"
    
    if chat_history:
        enhanced_query = f"{instruction}{chat_history}Current Question: {request.query}"
        print(f"DEBUG: Using chat history in query")
    else:
        enhanced_query = f"{instruction}{request.query}"
        print(f"DEBUG: No chat history found")
    
    # Get response from agent
    response = ask_agent(enhanced_query, request.house_id)
    
    # Save to memory if house_id provided
    if request.house_id:
        chat_sessions[request.house_id].append({
            "query": request.query,
            "response": response,
            "time": time.time()
        })
        start_timer(request.house_id)
        print(f"DEBUG: Saved chat. Total messages for {request.house_id}: {len(chat_sessions[request.house_id])}")
    
    return {"query": request.query, "response": response}

# Root endpoint
@app.get("/")
def root():
    return {"message": "Energy AI Agent is running!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
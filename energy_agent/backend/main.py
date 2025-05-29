from fastapi import FastAPI
from pydantic import BaseModel
import os
import sys
import time
import threading
from collections import defaultdict
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from ai_agent.agent import ask_agent
from ai_agent.prompt_templates import MAIN_DEBUG_MESSAGES, MAIN_INSTRUCTION_TEMPLATE, CHAT_HISTORY_FORMAT, APP_MESSAGE

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
        history += CHAT_HISTORY_FORMAT.format(query=chat['query'], response=chat['response'])
    return history

# Updated Request model to include optional house_id
class QueryRequest(BaseModel):
    query: str
    house_id: str = None

@app.post("/ask")
def ask_energy_agent(request: QueryRequest):
    """API endpoint to interact with the AI agent."""
    
    # Get chat history
    print(MAIN_DEBUG_MESSAGES["received_request"].format(house_id=request.house_id))
    chat_history = get_chat_history(request.house_id)
    print(MAIN_DEBUG_MESSAGES["chat_history_count"].format(house_id=request.house_id, count=len(chat_sessions.get(request.house_id, []))))
    
    today = datetime.now().strftime("%Y-%m-%d")
    current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Add history and instruction to query with date context
    instruction = MAIN_INSTRUCTION_TEMPLATE.format(today=today, current_datetime=current_datetime)
    
    if chat_history:
        enhanced_query = f"{instruction}{chat_history}Current Question: {request.query}"
        print(MAIN_DEBUG_MESSAGES["using_history"])
    else:
        enhanced_query = f"{instruction}{request.query}"
        print(MAIN_DEBUG_MESSAGES["no_history"])
    
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
        print(MAIN_DEBUG_MESSAGES["saved_chat"].format(house_id=request.house_id, count=len(chat_sessions[request.house_id])))
    
    return {"query": request.query, "response": response}

# Root endpoint
@app.get("/")
def root():
    return {"message": APP_MESSAGE}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
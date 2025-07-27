from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict
# Import the specific functions you need, including the new initializer
from rag_chatbot import (
    initialize_clients, 
    rewrite_query, 
    retrieve_context, 
    generate_answer
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Create the FastAPI app instance
app = FastAPI()

# --- Lifespan Events ---
@app.on_event("startup")
async def startup_event():
    """
    This function runs when the application starts.
    It's the perfect place to initialize our AI clients.
    """
    initialize_clients()

# --- CORS Middleware ---
# Remember to replace "*" with your actual frontend URL in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # e.g., ["https://your-frontend.netlify.app"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Models ---
class ChatRequest(BaseModel):
    query: str
    history: List[Dict[str, str]]

class ChatResponse(BaseModel):
    answer: str

# --- API Endpoints ---
@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    try:
        standalone_query = rewrite_query(request.query, request.history)
        context = retrieve_context(standalone_query)
        answer = generate_answer(request.query, context, request.history)
        return {"answer": answer}
    except Exception as e:
        print(f"An error occurred during chat processing: {e}")
        # Return a user-friendly error message
        return JSONResponse(
            status_code=500,
            content={"message": "An internal error occurred. Please try again later."}
        )

@app.get("/health")
def health_check():
    """A simple endpoint to check if the service is running."""
    return {"status": "OK"}

@app.options("/chat")
def options_chat():
    """Handles CORS preflight requests."""
    return JSONResponse(content={}, status_code=200)

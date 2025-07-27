from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import List, Dict
from rag_chatbot import RAGChatbot
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Create the FastAPI app instance
app = FastAPI()

# --- Lifespan Events ---
@app.on_event("startup")
async def startup_event():
    """
    On startup, create a single instance of the RAGChatbot and
    store it in the application's state for shared access.
    """
    app.state.chatbot = RAGChatbot()
    print("Chatbot is ready.")

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
def chat(request_data: ChatRequest, request: Request):
    """
    Handles the chat request by using the shared chatbot instance
    from the application state.
    """
    chatbot = request.app.state.chatbot
    try:
        standalone_query = chatbot.rewrite_query(request_data.query, request_data.history)
        context = chatbot.retrieve_context(standalone_query)
        answer = chatbot.generate_answer(request_data.query, context, request_data.history)
        return {"answer": answer}
    except Exception as e:
        print(f"An error occurred during chat processing: {e}")
        return JSONResponse(
            status_code=500,
            content={"message": "An internal error occurred. Please try again later."}
        )

@app.get("/health")
def health_check():
    """A simple endpoint to check if the service is running."""
    return {"status": "OK"}

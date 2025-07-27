import asyncio
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
async def chat(request_data: ChatRequest, request: Request):
    """
    Handles the chat request by running rewrite and retrieval in parallel.
    """
    chatbot = request.app.state.chatbot
    try:
        # Create tasks to run the rewrite and retrieval operations concurrently
        rewrite_task = chatbot.rewrite_query_async(request_data.query, request_data.history)
        retrieval_task = chatbot.retrieve_context_async(request_data.query)

        # Wait for both tasks to complete
        standalone_query, context = await asyncio.gather(rewrite_task, retrieval_task)
        
        # If the context from the original query was empty, try again with the rewritten query
        if not context and standalone_query != request_data.query:
            print("Initial context empty, retrieving with standalone query.")
            context = await chatbot.retrieve_context_async(standalone_query)

        # Now generate the final answer with the results
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

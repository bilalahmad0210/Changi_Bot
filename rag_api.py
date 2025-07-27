from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict
from rag_chatbot import rewrite_query, retrieve_context, generate_answer
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    query: str
    history: List[Dict[str, str]]  # [{'role': 'User', 'content': '...'}, ...]

class ChatResponse(BaseModel):
    answer: str
    updated_history: List[Dict[str, str]]

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    # Rewrite the query
    standalone_query = rewrite_query(request.query, request.history)

    # Retrieve context
    context = retrieve_context(standalone_query)

    # Generate the answer
    answer = generate_answer(request.query, context, request.history)

    # Return updated history
    new_history = request.history + [
        {"role": "User", "content": request.query},
        {"role": "Assistant", "content": answer}
    ]

    return {"answer": answer, "updated_history": new_history}

@app.get("/health")
def health_check():
    return {"status": "OK"}

@app.options("/chat")
def options_chat():
    return JSONResponse(content={}, status_code=200)

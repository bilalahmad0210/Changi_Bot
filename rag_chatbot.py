import os
from pinecone import Pinecone
from langchain_huggingface import HuggingFaceEmbeddings
from huggingface_hub import InferenceClient
from dotenv import load_dotenv

# --- Global Variables ---
# We will initialize these in the startup event of the FastAPI app
pc = None
index = None
embedding_model = None
client = None

def initialize_clients():
    """
    Initializes all the necessary AI clients. This function should be
    called once when the FastAPI application starts.
    """
    global pc, index, embedding_model, client
    
    # Load environment variables from .env file
    load_dotenv()

    # --- Configuration ---
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
    PINECONE_INDEX_NAME = "changi-rag-chatbot"
    HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")

    if not all([PINECONE_API_KEY, HUGGINGFACE_API_KEY]):
        raise ValueError("API keys for Pinecone or Hugging Face are not set in the environment.")

    # --- Initialize Clients ---
    print("Initializing clients...")
    pc = Pinecone(api_key=PINECONE_API_KEY)
    index = pc.Index(PINECONE_INDEX_NAME)
    embedding_model = HuggingFaceEmbeddings(model_name="BAAI/bge-base-en-v1.5")
    client = InferenceClient(token=HUGGINGFACE_API_KEY)
    print("Clients Initialized Successfully!")


def retrieve_context(query, top_k=5):
    if not index or not embedding_model:
        raise ConnectionError("Clients are not initialized. Cannot retrieve context.")
    try:
        query_vector = embedding_model.embed_query(query)
        query_results = index.query(vector=query_vector, top_k=top_k, include_metadata=True)
        context = [match['metadata']['text'] for match in query_results['matches']]
        print(f"Retrieved {len(context)} context chunks.")
        return "\n\n---\n\n".join(context)
    except Exception as e:
        print(f"Error retrieving context from Pinecone: {e}")
        return ""

def huggingface_generate(prompt):
    if not client:
        raise ConnectionError("Hugging Face client is not initialized.")
    try:
        completion = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-V3-0324",
            messages=[{"role": "user", "content": prompt}],
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error calling Hugging Face API: {e}")
        return "I'm having trouble generating a response right now."

def rewrite_query(query, history):
    limited_history = history[-6:]
    formatted_history = "\n".join([f"{msg['role']}: {msg['content']}" for msg in limited_history])

    rewrite_prompt = f"""
    Based on the following chat history and the user's latest question,
    rewrite the question into a standalone query that can be understood
    without the conversation context.

    Chat History:
    {formatted_history}

    User's Latest Question:
    {query}

    Standalone Query:
    """
    return huggingface_generate(rewrite_prompt)

def generate_answer(query, context, history):
    prompt_template = f"""
    You are a helpful assistant for Changi Airport. Answer the user's latest question based ONLY on the
    provided context. Use the chat history for conversational context. If the 
    retrieved context does not contain the answer, state that you don't have enough information.

    Chat History:
    {format_history(history)}

    Retrieved Context:
    ---
    {context}
    ---

    User's Latest Question:
    {query}

    ANSWER:
    """
    return huggingface_generate(prompt_template)

def format_history(history):
    return "\n".join([f"{msg['role']}: {msg['content']}" for msg in history[-6:]])

# The main function is for local testing and will not be used by the API
def main():
    initialize_clients() # Initialize for local run
    chat_history = []
    print("\n--- RAG Chatbot is Ready! (Using Hugging Face DeepSeek-V3-0324) ---")
    print("Ask a question about your documents. Type 'exit' to quit.")
    while True:
        user_query = input("\nYou: ")
        if user_query.lower() == 'exit':
            break
        standalone_query = rewrite_query(user_query, chat_history)
        retrieved_context = retrieve_context(standalone_query)
        if retrieved_context:
            final_answer = generate_answer(user_query, retrieved_context, chat_history)
        else:
            final_answer = "I could not retrieve any context to answer that. Please ask another question."
        print(f"\nBot: {final_answer}")
        chat_history.append({"role": "User", "content": user_query})
        chat_history.append({"role": "Assistant", "content": final_answer})

if __name__ == "__main__":
    main()

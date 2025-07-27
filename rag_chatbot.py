import os
from pinecone import Pinecone
from langchain_huggingface import HuggingFaceEmbeddings
from huggingface_hub import InferenceClient
from dotenv import load_dotenv

class RAGChatbot:
    def __init__(self):
        """
        Initializes the chatbot and all necessary clients upon creation.
        """
        load_dotenv()
        
        PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
        PINECONE_INDEX_NAME = "changi-rag-chatbot"
        HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")

        if not all([PINECONE_API_KEY, HUGGINGFACE_API_KEY]):
            raise ValueError("API keys for Pinecone or Hugging Face are not set.")

        print("Initializing clients...")
        self.pc = Pinecone(api_key=PINECONE_API_KEY)
        self.index = self.pc.Index(PINECONE_INDEX_NAME)
        self.embedding_model = HuggingFaceEmbeddings(model_name="BAAI/bge-base-en-v1.5")
        self.client = InferenceClient(token=HUGGINGFACE_API_KEY)
        print("Clients Initialized Successfully!")

    def retrieve_context(self, query, top_k=5):
        try:
            query_vector = self.embedding_model.embed_query(query)
            query_results = self.index.query(vector=query_vector, top_k=top_k, include_metadata=True)
            context = [match['metadata']['text'] for match in query_results['matches']]
            print(f"Retrieved {len(context)} context chunks.")
            return "\n\n---\n\n".join(context)
        except Exception as e:
            print(f"Error retrieving context from Pinecone: {e}")
            return ""

    def _huggingface_generate(self, prompt):
        try:
            completion = self.client.chat.completions.create(
                model="deepseek-ai/DeepSeek-V3-0324",
                messages=[{"role": "user", "content": prompt}],
            )
            return completion.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error calling Hugging Face API: {e}")
            return "I'm having trouble generating a response right now."

    def rewrite_query(self, query, history):
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
        return self._huggingface_generate(rewrite_prompt)

    def generate_answer(self, query, context, history):
        prompt_template = f"""
        You are a helpful assistant for Changi Airport. Answer the user's latest question based ONLY on the
        provided context. Use the chat history for conversational context. If the 
        retrieved context does not contain the answer, state that you don't have enough information.

        Chat History:
        {self._format_history(history)}

        Retrieved Context:
        ---
        {context}
        ---

        User's Latest Question:
        {query}

        ANSWER:
        """
        return self._huggingface_generate(prompt_template)

    def _format_history(self, history):
        return "\n".join([f"{msg['role']}: {msg['content']}" for msg in history[-6:]])

# This part is for local testing only and won't be used by the API.
if __name__ == "__main__":
    chatbot = RAGChatbot()
    chat_history = []
    print("\n--- RAG Chatbot is Ready! ---")
    while True:
        user_query = input("\nYou: ")
        if user_query.lower() == 'exit':
            break
        standalone_query = chatbot.rewrite_query(user_query, chat_history)
        retrieved_context = chatbot.retrieve_context(standalone_query)
        final_answer = chatbot.generate_answer(user_query, retrieved_context, chat_history)
        print(f"\nBot: {final_answer}")
        chat_history.append({"role": "User", "content": user_query})
        chat_history.append({"role": "Assistant", "content": final_answer})

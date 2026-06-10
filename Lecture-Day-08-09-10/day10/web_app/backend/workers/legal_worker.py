import os
import chromadb
from chromadb.utils import embedding_functions
from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

def get_chroma_collection():
    # Calculate path to day10/lab/chroma_db
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__))) # day10/web_app/backend -> day10
    db_path = os.path.join(base_dir, "lab", "chroma_db")
    
    client = chromadb.PersistentClient(path=db_path)
    emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    collection = client.get_or_create_collection(name="day10_kb", embedding_function=emb_fn)
    return collection

def legal_worker_node(state):
    """
    Worker phụ trách xử lý luật hình sự, quy định nội bộ, chính sách.
    Tích hợp RAG thật từ ChromaDB của Lab Day 10.
    """
    messages = state["messages"]
    last_message = messages[-1].content
    
    try:
        # 1. Retrieval
        collection = get_chroma_collection()
        results = collection.query(
            query_texts=[last_message],
            n_results=3
        )
        
        # 2. Xử lý Context
        retrieved_docs = results['documents'][0] if results['documents'] else []
        context = "\n\n".join(retrieved_docs)
        
        if not context.strip():
            context = "Không tìm thấy thông tin liên quan trong cơ sở dữ liệu."
            
        # 3. Generation (LLM)
        llm = ChatOpenAI(temperature=0, model="gpt-4o-mini")
        prompt = ChatPromptTemplate.from_messages([
            ("system", "Bạn là Legal Worker, chuyên gia pháp lý và chính sách nội bộ. Hãy trả lời câu hỏi dựa trên ngữ cảnh sau:\n\n{context}\n\nNếu ngữ cảnh không có thông tin, hãy nói rõ là không có thông tin trong CSDL."),
            ("human", "{question}")
        ])
        
        chain = prompt | llm
        response = chain.invoke({
            "context": context,
            "question": last_message
        })
        
        response_text = f"[Legal Worker - RAG Applied]\n{response.content}"
        
    except Exception as e:
        response_text = f"[Legal Worker - Lỗi RAG] Không thể truy xuất CSDL: {str(e)}"
    
    return {"messages": [AIMessage(content=response_text)], "next": "Supervisor"}

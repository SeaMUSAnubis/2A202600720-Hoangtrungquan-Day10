from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import asyncio
from agent_orchestrator import run_workflow

app = FastAPI(title="Legal AI Hub API")

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Legal AI Backend is running. Please use the frontend to interact, or send POST to /api/chat"}

class ChatRequest(BaseModel):
    query: str

class Citation(BaseModel):
    id: int
    title: str
    score: str
    content: str

class AgentResponse(BaseModel):
    agentType: str
    text: str
    citations: Optional[List[Citation]] = None

@app.post("/api/chat", response_model=AgentResponse)
async def chat(request: ChatRequest):
    """
    Sử dụng LangGraph StateGraph để xử lý câu hỏi với đa tác nhân.
    """
    query = request.query
    
    # Run the multi-agent workflow
    final_state = await run_workflow(query)
    
    # Gộp các câu trả lời từ các agents (bỏ qua HumanMessage đầu tiên)
    agent_messages = [msg.content for msg in final_state["messages"][1:]]
    combined_response = "\n\n".join(agent_messages)
    
    # Simple mock response in case of no agent matched
    if not combined_response:
        combined_response = f"Tôi không có đủ thông tin để tư vấn về: {query}"
        
    return AgentResponse(
        agentType="customer",
        text=combined_response,
        citations=[
            Citation(id=1, title='Điều 249 Bộ luật Hình sự 2015', score='0.92', content='Tội tàng trữ trái phép chất ma túy...')
        ]
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

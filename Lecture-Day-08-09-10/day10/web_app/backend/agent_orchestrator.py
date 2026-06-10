import operator
from typing import Annotated, Sequence, TypedDict, Literal
from langchain_core.messages import BaseMessage, HumanMessage
from pydantic import BaseModel
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

# Import workers
from workers.legal_worker import legal_worker_node
from workers.tax_worker import tax_worker_node
from workers.compliance_worker import compliance_worker_node

# --- 1. Define State ---
class AgentState(TypedDict):
    messages: list[BaseMessage]
    next: str

# --- 2. Define Supervisor ---
def supervisor_node(state: AgentState):
    """
    Supervisor phân tích câu hỏi để định tuyến tới Worker phù hợp.
    (Phiên bản Pure Python, không cần langgraph)
    """
    messages = state["messages"]
    
    last_message = messages[-1].content.lower()
    
    if "thuế" in last_message and "TaxWorker" not in [m.content for m in messages]:
        next_worker = "TaxWorker"
    elif "tuân thủ" in last_message and "ComplianceWorker" not in [m.content for m in messages]:
        next_worker = "ComplianceWorker"
    elif any(k in last_message for k in ["tù", "phạt", "ma túy", "luật", "quy định", "chính sách", "nghỉ phép"]) and "LegalWorker" not in [m.content for m in messages]:
        next_worker = "LegalWorker"
    else:
        next_worker = "FINISH"

    return {"next": next_worker}

# --- 3. Pure Python Workflow Runner ---
async def run_workflow(query: str):
    """
    Hàm chạy workflow bằng Pure Python thay vì langgraph để tránh lỗi dependency.
    """
    state: AgentState = {
        "messages": [HumanMessage(content=query)],
        "next": "Supervisor"
    }
    
    workers = {
        "LegalWorker": legal_worker_node,
        "TaxWorker": tax_worker_node,
        "ComplianceWorker": compliance_worker_node
    }
    
    max_steps = 5
    step = 0
    
    while state["next"] != "FINISH" and step < max_steps:
        step += 1
        current_node = state["next"]
        
        if current_node == "Supervisor":
            update = supervisor_node(state)
            state["next"] = update["next"]
        else:
            worker_func = workers.get(current_node)
            if worker_func:
                update = await asyncio.to_thread(worker_func, state)
                state["messages"].extend(update["messages"])
                state["next"] = update["next"]
            else:
                state["next"] = "FINISH"
                
    return state

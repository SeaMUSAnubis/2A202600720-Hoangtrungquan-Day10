from langchain_core.messages import AIMessage

def compliance_worker_node(state):
    """
    Worker phụ trách vấn đề tuân thủ, quy định chung.
    """
    messages = state["messages"]
    last_message = messages[-1].content
    
    response_text = f"[Compliance Worker] Về việc tuân thủ quy định: '{last_message}'..."
    
    return {"messages": [AIMessage(content=response_text)], "next": "Supervisor"}

from langchain_core.messages import AIMessage

def tax_worker_node(state):
    """
    Worker phụ trách tư vấn về thuế, tài chính doanh nghiệp.
    """
    messages = state["messages"]
    last_message = messages[-1].content
    
    response_text = f"[Tax Worker] Liên quan đến vấn đề thuế tài chính: '{last_message}', theo Luật Quản lý Thuế..."
    
    return {"messages": [AIMessage(content=response_text)], "next": "Supervisor"}

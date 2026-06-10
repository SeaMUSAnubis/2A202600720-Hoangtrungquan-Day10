import asyncio
import os
from agent_orchestrator import run_workflow

async def main():
    print("Running test query...")
    result = await run_workflow("Theo quy định mới năm 2026, nhân viên được nghỉ phép bao nhiêu ngày?")
    print("=== FINAL STATE ===")
    for msg in result["messages"]:
        print(f"{msg.__class__.__name__}: {msg.content}")

if __name__ == "__main__":
    asyncio.run(main())

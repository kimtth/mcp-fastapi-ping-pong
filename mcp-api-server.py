import uvicorn
import threading
from fastapi import FastAPI, Request
from fastmcp import FastMCP
from fastapi.middleware.cors import CORSMiddleware
from mcp import ListPromptsResult
from mcp.shared.memory import (
    create_connected_server_and_client_session as client_session,
)
from typing import Dict, Any
from utils.session_manager import SessionManager


app = FastAPI()
mcp = FastMCP("ping-pong")
session_manager = SessionManager()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@mcp.tool("ping-pong")
async def mcp_handler(command: str, session_id: str) -> str:
    """MCP handler for ping-pong commands"""
    try:
        # Ensure session exists
        session_manager.get_or_create(session_id)

        if command == "ping":
            session_manager.increment(session_id)
            return "pong"
        elif command == "pong":
            session_manager.increment(session_id)
            return "ping"
        elif command == "count":
            return str(session_manager.get_count(session_id))
        else:
            return "unknown command"
    except Exception as e:
        return str(e)


@mcp.prompt("ping-pong")
async def ping_pong_prompt() -> str:
    """Prompt for the ping-pong tool"""
    prompt_content = (
        "This is a simple ping-pong tool. Use 'ping' or 'pong' to interact."
    )
    return prompt_content


@app.get("/ping-pong")
async def ping_pong(request: Request) -> Dict[str, str]:
    prompt_name = request.query_params.get("prompt_name", "")
    if not prompt_name:
        return {"error": "prompt_name is required"}

    async with client_session(mcp._mcp_server) as client:
        try:
            list_prompts: ListPromptsResult = await client.list_prompts()
            for prompt in list_prompts.prompts:
                if prompt.name == prompt_name:
                    print(type(prompt))
                    prompt_msg = await client.get_prompt(prompt.name)
                    prompt_content = prompt_msg.messages[0].content.text
                    return {
                        "prompt": prompt.name,
                        "description": prompt.description,
                        "content": prompt_content,
                    }
        except Exception as e:
            return {"error": str(e)}
        return {"error": "Prompt not found"}


@app.post("/ping-pong")
async def handle_mcp_command(request: Request) -> Dict[str, Any]:
    session_id = None
    try:
        body = await request.json()

        # Get or create session
        session_id = session_manager.get_or_create(body.get("session_id"))
        command = body.get("command", "")

        async with client_session(mcp._mcp_server) as client:
            result = await client.call_tool(
                "ping-pong",
                {"command": command, "session_id": session_id},
            )

        mcp_response = result.content[0]
        if hasattr(mcp_response, "text"):
            mcp_response = mcp_response.text

        return {"data": mcp_response, "session_id": session_id}
    except Exception as e:
        return {"error": str(e), "session_id": session_id}


if __name__ == "__main__":
    # Rest of the code remains the same
    def start_mcp_server():
        mcp.run()

    def start_fastapi_server():
        uvicorn.run(app, host="0.0.0.0", port=8080)

    t1 = threading.Thread(target=start_mcp_server)
    t2 = threading.Thread(target=start_fastapi_server)

    print("MCP server started")
    t1.start()
    print("FastAPI server started")
    t2.start()

    t1.join()
    t2.join()

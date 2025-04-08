from fastapi.responses import PlainTextResponse
import mcp
import uvicorn
import asyncio
from utils.session_manager import SessionManager
from mcp.server.fastmcp import FastMCP
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.requests import Request


def init_mcp_tool(mcp: FastMCP) -> None:
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


def create_sse_server(mcp: FastMCP) -> Starlette:
    # Create the transport instance with the specified base path.
    sse = SseServerTransport("/sse-transport")

    async def handle_sse(request: Request):
        async with sse.connect_sse(
            request.scope, request.receive, request._send
        ) as streams:
            read_stream, write_stream = streams
            await mcp._mcp_server.run(
                read_stream,
                write_stream,
                mcp._mcp_server.create_initialization_options(),
            )

    async def handle_post(request: Request):
        await asyncio.sleep(0.1)
        await sse.handle_post_message(request, request.receive, request._send)
        return PlainTextResponse("Accepted", status_code=202)

    # Define explicit routes for GET (SSE connection) and POST (message handling).
    routes = [
        Route("/sse", endpoint=handle_sse, methods=["GET"]),
        Route("/sse-transport", endpoint=handle_post, methods=["POST"]),
    ]

    return Starlette(routes=routes)


if __name__ == "__main__":
    # Create the MCP server instance
    mcp = FastMCP("ping-pong")
    # Initialize the MCP tool and session manager
    init_mcp_tool(mcp)
    session_manager = SessionManager()

    # Create the SSE server
    sse_server = create_sse_server(mcp)
    # Run the server on localhost:8080
    uvicorn.run(sse_server, host="localhost", port=8080)

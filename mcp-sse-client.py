import asyncio
import uuid
from mcp.client.sse import sse_client
from mcp import ClientSession

SSE_SERVER_URL = "http://localhost:8080/sse"

async def get_async_input():
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, input, ">>> ")

async def main():
    async with sse_client(SSE_SERVER_URL) as streams:
        async with ClientSession(*streams) as client:
            await client.initialize()

            session_id = str(uuid.uuid4())
            await asyncio.sleep(0.5)  # Give some time for the initialization
            print("Type a command (e.g., 'ping', 'pong', 'count') or 'exit' to quit:")

            while True:
                try:
                    command = await get_async_input()
                    if command.lower() in ("exit", "quit"):
                        break

                    print("Sending command:", command)
                    try:
                        result = await asyncio.wait_for(
                            client.call_tool(
                                name="ping-pong",
                                arguments={"command": command, "session_id": session_id},
                            ),
                            timeout=5,
                        )
                        if hasattr(result, "content"):
                            result = result.content[0].text
                        print("Result:", result)
                    except asyncio.TimeoutError:
                        print("No response received within 5 seconds.")
                except Exception as e:
                    print("Error:", e)

if __name__ == "__main__":
    asyncio.run(main())

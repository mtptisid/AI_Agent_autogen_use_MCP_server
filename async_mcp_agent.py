import asyncio
import os
import aiohttp
from typing import Dict, Any, Optional
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.tools.mcp import SseMcpToolAdapter, SseServerParams
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.ui import Console
from autogen_core import CancellationToken

# MCP server configuration
MCP_CONFIG = {
    "url": "http://localhost:8000/mcp",  # Your MCP server URL
    "headers": {
        "Content-Type": "application/json"
    },
    "timeout": 30  # Connection timeout in seconds
}

async def setup_mcp_agent() -> AssistantAgent:
    """
    Set up the MCP-enabled agent with proper configuration
    """
    try:
        print(f"Attempting to connect to MCP server at {MCP_CONFIG['url']}...")
        
        # Create server params for the MCP service
        server_params = SseServerParams(
            url=MCP_CONFIG["url"],
            headers=MCP_CONFIG["headers"],
            timeout=MCP_CONFIG["timeout"]
        )
        
        print("Checking server availability...")
        async with aiohttp.ClientSession() as session:
            try:
                init_payload = {
                    "jsonrpc": "2.0",
                    "method": "initialize",
                    "id": 1
                }
                async with session.post(MCP_CONFIG["url"], json=init_payload) as response:
                    if response.status != 200:
                        raise Exception(f"Server returned status {response.status}")
                    result = await response.json()
                    print(f"Server is responding with capabilities: {result.get('result', {}).get('capabilities', {})}")
            except Exception as e:
                raise Exception(f"Failed to connect to MCP server: {str(e)}")

        # Set up the MCP tool adapter with the default tool
        print("Setting up MCP tool adapter...")
        try:
            adapter = await SseMcpToolAdapter.from_server_params(
                server_params,
                tool_name="execute"  # Using a basic execute tool since we know tools are supported
            )
            print("Successfully configured MCP tool adapter")
        except Exception as e:
            raise Exception(f"Failed to configure MCP adapter: {str(e)}")

        # Create an agent that can use MCP tools
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise Exception("OPENAI_API_KEY environment variable is not set")
            
        print("Initializing OpenAI client...")
        model_client = OpenAIChatCompletionClient(
            api_key=api_key,
            model="gpt-4"
        )

        print("Creating MCP assistant agent...")
        return AssistantAgent(
            name="mcp_assistant",
            model_client=model_client,
            tools=[adapter],
            system_message="""You are a helpful AI assistant that specializes in working with MCP servers.
            You can use various MCP commands and tools to interact with the server.
            Always check server capabilities before executing commands."""
        )
    except Exception as e:
        print(f"Error during setup: {str(e)}")
        raise

async def main() -> None:
    print("MCP Agent starting up...")
    
    try:
        # Create the MCP-enabled agent
        agent = await setup_mcp_agent()
        print("Successfully connected to MCP server!")
        
        # Main interaction loop
        while True:
            try:
                # Get user input
                user_input = input("\nMCP> ").strip()
                if user_input.lower() in ["exit", "quit"]:
                    print("Shutting down MCP Agent...")
                    break

                # Process the input through the agent
                await Console(
                    agent.run_stream(
                        task=user_input,
                        cancellation_token=CancellationToken()
                    )
                )
                
            except Exception as e:
                print(f"Error processing command: {str(e)}")
                
    except Exception as e:
        print(f"Failed to initialize MCP agent: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())

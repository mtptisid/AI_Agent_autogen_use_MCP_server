import asyncio
import aiohttp
import json
import os
from typing import Dict, Any, Optional
from autogen import AssistantAgent, UserProxyAgent, config_list_from_json

# MCP Server Configuration
MCP_CONFIG = {
    "url": "http://localhost:8000/mcp",
    "headers": {
        "Content-Type": "application/json"
    }
}

class MCPToolkit:
    def __init__(self, url: str, headers: Dict[str, str]):
        self.url = url
        self.headers = headers
        self.session = None
        self.capabilities = None

    async def initialize(self):
        """Initialize connection to MCP server and get capabilities"""
        self.session = aiohttp.ClientSession()
        try:
            response = await self._send_request("initialize", {})
            self.capabilities = response.get("result", {}).get("capabilities", {})
            return self.capabilities
        except Exception as e:
            raise Exception(f"Failed to initialize MCP connection: {e}")

    async def list_resources(self):
        """List available resources from MCP server"""
        return await self._send_request("resources/list", {})

    async def execute_tool(self, tool_name: str, params: Dict[str, Any]):
        """Execute a tool on the MCP server"""
        return await self._send_request(f"tools/{tool_name}", params)

    async def _send_request(self, method: str, params: Dict[str, Any]):
        """Send JSON-RPC request to MCP server"""
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": 1
        }
        
        async with self.session.post(self.url, json=payload, headers=self.headers) as response:
            if response.status != 200:
                raise Exception(f"MCP server error: {response.status}")
            return await response.json()

    async def close(self):
        """Close the session"""
        if self.session:
            await self.session.close()

class MCPAssistant:
    def __init__(self):
        self.mcp = MCPToolkit(MCP_CONFIG["url"], MCP_CONFIG["headers"])
        
        # Configure AutoGen
        config_list = [{
            "model": "gpt-4",
            "api_key": os.getenv("OPENAI_API_KEY")
        }]

        # Create assistant with enhanced prompt for MCP capabilities
        self.assistant = AssistantAgent(
            name="mcp_assistant",
            system_message="""You are an AI assistant that can use both general tools and MCP server capabilities.
            You can execute tools, manage resources, and help users interact with the MCP server.
            Always check capabilities before executing commands.""",
            llm_config={"config_list": config_list}
        )

        # Create user proxy for interaction
        self.user_proxy = UserProxyAgent(
            name="user_proxy",
            human_input_mode="TERMINATE",
            max_consecutive_auto_reply=10,
            code_execution_config={
                "work_dir": "workspace",
                "use_docker": False,
            }
        )

    async def start(self):
        """Start the MCP Assistant"""
        try:
            print("Initializing MCP connection...")
            capabilities = await self.mcp.initialize()
            print(f"MCP Server capabilities: {capabilities}")

            print("\nMCP Assistant is ready! Type 'exit' to quit.")
            print("Available commands:")
            print("- resources : List available MCP resources")
            print("- tool <name> <params> : Execute an MCP tool")
            print("- chat <message> : Chat with the AI assistant")

            while True:
                try:
                    command = input("\nMCP> ").strip()
                    if command.lower() in ["exit", "quit"]:
                        break

                    if command == "resources":
                        result = await self.mcp.list_resources()
                        print(f"Resources: {json.dumps(result, indent=2)}")
                        
                    elif command.startswith("tool "):
                        # Parse tool command (simple version)
                        parts = command.split(" ", 2)
                        if len(parts) < 3:
                            print("Usage: tool <name> <params_json>")
                            continue
                        
                        tool_name = parts[1]
                        try:
                            params = json.loads(parts[2])
                            result = await self.mcp.execute_tool(tool_name, params)
                            print(f"Tool result: {json.dumps(result, indent=2)}")
                        except json.JSONDecodeError:
                            print("Invalid JSON parameters")
                            
                    elif command.startswith("chat "):
                        message = command[5:]
                        # Use AutoGen for chat
                        self.user_proxy.initiate_chat(
                            self.assistant,
                            message=message
                        )
                        
                    else:
                        print("Unknown command")

                except Exception as e:
                    print(f"Error: {str(e)}")

        finally:
            await self.mcp.close()

def main():
    """Main entry point"""
    # Set up OpenAI key
    if not os.getenv("OPENAI_API_KEY"):
        key = input("Enter your OpenAI API key: ")
        os.environ["OPENAI_API_KEY"] = key

    # Run the assistant
    assistant = MCPAssistant()
    asyncio.run(assistant.start())

if __name__ == "__main__":
    main()

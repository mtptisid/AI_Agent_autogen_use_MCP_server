import asyncio
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.tools.mcp import SseMcpToolAdapter, SseServerParams
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.ui import Console
from autogen_core import CancellationToken
import os
from typing import Dict, Any, Optional

# Tool definitions
def query_gemini(prompt):
    model = genai.GenerativeModel('gemini-2.0-flash')
    response = model.generate_content(prompt)
    return response.text

# MCP server configuration
MCP_CONFIG = {
    "server_url": "http://localhost:8000",  
    "request_timeout": 30.0  # Increased timeout for stability
}

class MCPClient:
    def __init__(self, server_url: str, request_timeout: float = 30.0):
        self.server_url = server_url
        self.timeout = request_timeout
        self.session = requests.Session()
        print(f"Initializing MCP client, connecting to: {server_url}")

    def call(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make a JSON-RPC call to the MCP server
        """
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
            "id": 1
        }
        
        try:
            response = self.session.post(
                self.server_url,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()
            
            if "error" in result:
                raise Exception(f"MCP Error: {result['error'].get('message', 'Unknown error')}")
                
            return result.get("result", {})
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"MCP connection error: {str(e)}")
        except json.JSONDecodeError:
            raise Exception("Invalid JSON response from MCP server")
            
# Initialize MCP client
mcp_client = MCPClient(MCP_CONFIG["server_url"], MCP_CONFIG["request_timeout"])

def query_mcp(method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Send a request to the MCP server
    """
    try:
        print(f"Sending MCP request - Method: {method}, Params: {params}")
        result = mcp_client.call(method, params)
        print(f"MCP response received: {result}")
        return result
    except Exception as e:
        error_msg = str(e)
        print(f"MCP Error: {error_msg}")
        return {"error": error_msg}

def get_mcp_capabilities():
    """Get available methods from MCP server"""
    return query_mcp("get_capabilities")

def send_mcp_message(message):
    """Send a message through MCP"""
    return query_mcp("send_message", {"content": message})

def execute_mcp_command(command):
    """Execute a command through MCP"""
    return query_mcp("execute_command", {"command": command})

# Tool functions
def search_web(query):
    return f"Searching for: {query}"

def calculate(expression):
    try:
        return eval(expression)
    except:
        return "Invalid expression"

# Configure the Assistant with enhanced capabilities
config_list = [
    {
        'model': 'gemini-2.0-flash',
        'api_key': GEMINI_API_KEY
    }
]

llm_config = {
    "config_list": config_list,
    "seed": 42,
    "temperature": 0.7,
    "functions": [
        {
            "name": "mcp_get_capabilities",
            "description": "Get the capabilities of the MCP server",
            "parameters": {"type": "object", "properties": {}}
        },
        {
            "name": "mcp_send_message",
            "description": "Send a message through the MCP server",
            "parameters": {
                "type": "object",
                "properties": {
                    "msg": {
                        "type": "string",
                        "description": "The message to send"
                    }
                },
                "required": ["msg"]
            }
        },
        {
            "name": "mcp_execute_command",
            "description": "Execute a command through the MCP server",
            "parameters": {
                "type": "object",
                "properties": {
                    "cmd": {
                        "type": "string",
                        "description": "The command to execute"
                    }
                },
                "required": ["cmd"]
            }
        }
    ]
}

# Create the assistant agent with tools
assistant = AssistantAgent(
    name="assistant",
    system_message="""You are a helpful AI assistant that specializes in working with MCP (Model Context Protocol) servers.
    
    Capabilities:
    1. Connect to and interact with MCP servers using JSON-RPC protocol
    2. Execute MCP commands and handle responses
    3. Understand server capabilities and available methods
    4. Process and interpret MCP messages
    5. Perform web searches and calculations to support MCP operations
    
    When interacting with the MCP server:
    - Use proper JSON-RPC 2.0 format
    - Handle error responses appropriately
    - Check server capabilities before executing commands
    - Maintain context between interactions
    
    Available MCP functions:
    - get_mcp_capabilities(): Check available server methods
    - send_mcp_message(message): Send messages to the server
    - execute_mcp_command(command): Execute server commands
    
    Always try to use appropriate tools and maintain a clear understanding of the MCP protocol.""",
    llm_config=llm_config
)

# Initialize function calling config for MCP operations
function_map = {
    "mcp_get_capabilities": lambda: query_mcp("get_capabilities"),
    "mcp_send_message": lambda msg: query_mcp("send_message", {"content": msg}),
    "mcp_execute_command": lambda cmd: query_mcp("execute_command", {"command": cmd})
}

# Create user proxy agent with enhanced MCP capabilities
user_proxy = UserProxyAgent(
    name="user_proxy",
    human_input_mode="TERMINATE",
    max_consecutive_auto_reply=10,
    code_execution_config={
        "work_dir": "workspace",
        "use_docker": False,
    },
    function_map=function_map
)

def main():
    print("MCP Agent starting up...")
    print("Testing connection to MCP server...")
    
    # Test MCP connection
    capabilities = get_mcp_capabilities()
    if "error" in capabilities:
        print(f"Error connecting to MCP server: {capabilities['error']}")
        return
        
    print(f"Successfully connected to MCP server!")
    print(f"Available capabilities: {capabilities}")
    print("\nMCP Agent CLI ready! Type 'exit' to quit.")
    print("Commands:")
    print("- capabilities : Show MCP server capabilities")
    print("- send <message> : Send a message to MCP server")
    print("- exec <command> : Execute a command via MCP server")
    
    while True:
        user_input = input("\nMCP> ").strip()
        if user_input.lower() in ["exit", "quit"]:
            print("Shutting down MCP Agent...")
            break
            
        try:
            if user_input == "capabilities":
                print(get_mcp_capabilities())
            elif user_input.startswith("send "):
                message = user_input[5:].strip()
                print(send_mcp_message(message))
            elif user_input.startswith("exec "):
                command = user_input[5:].strip()
                print(execute_mcp_command(command))
            else:
                print("Unknown command. Type 'capabilities', 'send <message>', or 'exec <command>'")
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()

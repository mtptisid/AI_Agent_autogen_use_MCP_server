import google.generativeai as genai
import requests

# Set your Gemini API key here or use an environment variable
GEMINI_API_KEY = "AIzaSyB8qzpyFpMqQ2_fAYTc7lZYQyrijpjSxGk"
genai.configure(api_key=GEMINI_API_KEY)

# Initialize Gemini model
model = genai.GenerativeModel('gemini-2.0-flash')

# MCP server integration
mcp_url = 'http://localhost:8000/mcp'

def query_mcp(message):
    try:
        payload = {
            "jsonrpc": "2.0",
            "method": "chat",
            "params": {"message": message},
            "id": 1
        }
        resp = requests.post(mcp_url, json=payload)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print('Error connecting to MCP server:', e)
        return None

# Tool functions
def search_web(query):
    return f"Searching for: {query}"

def calculate(expression):
    try:
        return eval(expression)
    except:
        return "Invalid expression"

def process_command(user_input):
    # Check for special commands
    if user_input.lower().startswith('search '):
        query = user_input[7:]
        return search_web(query)
    elif user_input.lower().startswith('calculate '):
        expression = user_input[10:]
        return calculate(expression)
    elif user_input.lower().startswith('mcp '):
        message = user_input[4:]
        return query_mcp({"message": message})
    else:
        # Use Gemini for general queries
        response = model.generate_content(user_input)
        return response.text

def main():
    print("Welcome to Gemini AI Agent! Type 'exit' to quit.")
    print("\nAvailable commands:")
    print("1. Ask any question")
    print("2. 'search [query]' to search the web")
    print("3. 'calculate [expression]' for math")
    print("4. 'mcp [message]' to send to MCP server")
    print("5. 'exit' to quit\n")
    
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ["exit", "quit"]:
            print("Goodbye!")
            break
        
        if not user_input:
            continue
            
        try:
            response = process_command(user_input)
            print("\nAI:", response, "\n")
        except Exception as e:
            print(f"\nError: {str(e)}\n")

if __name__ == "__main__":
    main()

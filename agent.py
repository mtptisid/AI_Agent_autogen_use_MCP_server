import autogen
import requests
import google.generativeai as genai

# Set your Gemini API key here or use an environment variable

genai.configure(api_key=GEMINI_API_KEY)

# Example prompt to Gemini model

def query_gemini(prompt):
    model = genai.GenerativeModel('gemini-2.0-flash')
    response = model.generate_content(prompt)
    return response.text




# Connect to MCP server
mcp_url = 'http://localhost:8000/mcp'

def query_mcp(payload):
    try:
        resp = requests.post(mcp_url, json=payload)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print('Error connecting to MCP server:', e)
        return None






# Autogen agent setup using Gemini
class GeminiAgent(autogen.ConversableAgent):
    def __init__(self, name="GeminiAgent"):
        super().__init__(name=name)

    def generate_reply(self, messages, **kwargs):
        # Get the latest user message
        prompt = messages[-1]["content"] if messages else "Hello!"
        return query_gemini(prompt)

def main():
    agent = GeminiAgent()
    print("Welcome to Gemini CLI! Type 'exit' to quit.")
    history = []
    while True:
        user_input = input("You: ")
        if user_input.strip().lower() in ["exit", "quit"]:
            print("Goodbye!")
            break
        history.append({"role": "user", "content": user_input})
        reply = agent.generate_reply(history)
        print("Gemini:", reply)
        history.append({"role": "assistant", "content": reply})

if __name__ == "__main__":
    main()

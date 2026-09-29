import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# Load variables from .env
load_dotenv()

# Initialize the model
llm = ChatOpenAI(model="gpt-4o-mini")

# Test a simple invocation
try:
    response = llm.invoke("Hello! Say 'Ready to build agents!' if you can hear me.")
    print("\n🚀 Success! Response from OpenAI:")
    print(response.content)
except Exception as e:
    print(f"\n❌ Error connecting to OpenAI: {e}")

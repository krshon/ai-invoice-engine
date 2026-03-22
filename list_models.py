import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load API key from .env
load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Print available models
for model in genai.list_models():
    print(model.name)
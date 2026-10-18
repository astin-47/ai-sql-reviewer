
import os
from dotenv import load_dotenv
from openai import OpenAI

# Load the API key from the local .env file
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError(
        "OPENAI_API_KEY was not found. "
        "Check that your .env file is in the project folder."
    )

client = OpenAI(api_key=api_key)

try:
    response = client.responses.create(
        model="gpt-4.1-mini",
        input="Reply with exactly: API connection successful."
    )

    print("OpenAI API connection successful!")
    print("Model response:", response.output_text)

except Exception as error:
    print(f"API request failed: {type(error).__name__}")
    print("Check your API access, model availability, and billing.")


import os
import json
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

# Load our private Nebius configuration
load_dotenv()

api_key = os.getenv("NEBIUS_API_KEY")
model_id = os.getenv("NEBIUS_MODEL")

if not api_key:
    raise RuntimeError("NEBIUS_API_KEY is missing from .env")

if not model_id:
    raise RuntimeError("NEBIUS_MODEL is missing from .env")

# Connect to Nebius Token Factory
client = OpenAI(
    base_url="https://api.tokenfactory.nebius.com/v1/",
    api_key=api_key,
    timeout=60.0
)


def investigate_bug():
    # Read the financial investigation results
    report = json.loads(
        Path("financial_report.json").read_text(
            encoding="utf-8"
        )
    )

    # Read the Python code containing the bug
    source_code = Path("transactions.py").read_text(
        encoding="utf-8"
    )

    # Ask NVIDIA Nemotron to investigate
    response = client.chat.completions.create(
        model=model_id,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are RootCause AI, a financial software "
                    "debugging assistant. Analyze financial "
                    "discrepancies and Python code. "
                    "Identify possible root causes and suggest "
                    "minimal code repairs. Do not claim any "
                    "repair is verified without test evidence."
                )
            },
            {
                "role": "user",
                "content": (
                    "Investigate this financial software bug.\n\n"
                    "FINANCIAL REPORT:\n"
                    + json.dumps(report, indent=2)
                    + "\n\nSOURCE CODE:\n"
                    + source_code
                    + "\n\nExplain the root cause and recommend "
                    "a minimal correction."
                )
            }
        ]
    )

    return response.choices[0].message.content


if __name__ == "__main__":
    print("ROOTCAUSE AI - NVIDIA NEMOTRON INVESTIGATION")
    print("=" * 45)
   
    result = investigate_bug()
    print(result)

    # Save Nemotron's investigation to a text file
    with open("ai_investigation.txt", "w", encoding="utf-8") as file:
        file.write(result)

    print("AI investigation saved successfully!")

  

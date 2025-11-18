"""
Inspect the current timesheet assistant configuration to understand structure
"""

import asyncio
import os
import sys
import httpx
import json
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

VAPI_API_KEY = os.getenv("VAPI_API_KEY")
TIMESHEET_ASSISTANT_ID = "d3a5e1cf-82cb-4f6e-a406-b0170ede3d10"


async def inspect_assistant():
    """Fetch and inspect current assistant configuration"""

    headers = {
        "Authorization": f"Bearer {VAPI_API_KEY}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.vapi.ai/assistant/{TIMESHEET_ASSISTANT_ID}",
            headers=headers
        )

        if response.status_code == 200:
            config = response.json()
            print(json.dumps(config, indent=2))
        else:
            print(f"Failed: {response.status_code}")
            print(response.text)


if __name__ == "__main__":
    asyncio.run(inspect_assistant())

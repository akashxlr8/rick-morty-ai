import httpx
import asyncio
import json

async def main():
    url = "http://localhost:8000/search"
    query = {"query": "Rick"}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=query)
            print(f"Status: {response.status_code}")
            print(json.dumps(response.json(), indent=2))
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())

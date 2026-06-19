import asyncio
import json
import httpx

async def main():
    async with httpx.AsyncClient(timeout=180.0) as client:
        body = {"prompt": "一只猫", "mode": "auto"}
        print("starting stream generate...")
        async with client.stream("POST", "http://localhost:8080/api/v1/generate/stream", json=body) as response:
            print("status:", response.status_code)
            count = 0
            async for line in response.aiter_lines():
                print(line[:200])
                count += 1
                if count >= 20:
                    print("(read 20 lines, stopping)")
                    break

if __name__ == "__main__":
    asyncio.run(main())

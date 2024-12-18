from httpx import AsyncClient
import asyncio

async def make_request(url:str):
    async with AsyncClient() as client:
        res = await client.post(url, json={
            'vacancy':"Джун нужен",
            "cv":"php dev"
        })
        print(res.json())
        return res

if __name__ == '__main__':
    asyncio.run(make_request("http://0.0.0.0:8001/hr/analyze_cv_by_vacancy"))
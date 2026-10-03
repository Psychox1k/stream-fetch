import asyncio
import json
import os
import traceback
import uuid

import aioboto3
import aiohttp
from dotenv import load_dotenv
import redis.asyncio as redis
from aiohttp import web

load_dotenv()
print(f"DEBUG: Access Key starts with: {str(os.getenv('AWS_ACCESS_KEY_ID'))[:4]}")
AWS_BUCKET_NAME = os.getenv("AWS_BUCKET_NAME")
AWS_REGION = os.getenv("AWS_REGION_NAME")



async def init_redis(app: web.Application):
    redis_url = "redis://localhost:6379/0"
    app["redis"] = await redis.from_url(redis_url, decode_responses=True)
    print("Successful connecting to redis")

async def close_redis(app: web.Application):
    await app["redis"].close()
    print("Closing Redis Connection")

async def init_app():
    app = web.Application()
    app.on_startup.append(init_redis)
    app.on_cleanup.append(close_redis)

    app.router.add_post("/api/v1/fetch", fetch_assets_handler)

    return app

async def fetch_assets_handler(request: web.Request):
    try:
        data = await request.json()
    except json.JSONDecodeError:
        return web.json_response({"error": "Wrong JSON FILE"}, status=400)

    urls = data.get("urls")

    if not urls or not isinstance(urls, list):
        return web.json_response({"error": "Where is the list?"}, status=400)

    job_id = str(uuid.uuid4())


    redis_client = request.app["redis"]

    initial_state = {
        "status": "processing",
        "total": len(urls),
        "done": 0,
        "failed": 0
    }
    await redis_client.set(f"job:{job_id}", json.dumps(initial_state), ex=86400)

    asyncio.create_task(process_download_task(job_id, urls, request.app))

    return web.json_response({
        "job_id": job_id,
        "message": "Task is being in processing"
    }, status=202)


async def process_download_task(job_id: str, urls: list, app: web.Application):
    redis_client = app["redis"]
    boto_session = aioboto3.Session(
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
    )
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    async with aiohttp.ClientSession(headers=headers) as http_session:
        async with boto_session.client("s3", region_name=AWS_REGION) as s3_client:
            done_count = 0
            failed_count = 0

            for i, url in enumerate(urls):
                try:
                    object_key = f"raw/{job_id}/file{i}.bin"

                    async with http_session.get(url) as response:
                        response.raise_for_status()
                        await s3_client.upload_fileobj(
                            response.content,
                            AWS_BUCKET_NAME,
                            object_key
                        )
                    done_count += 1
                except Exception as e:
                    print(f"[Error] Failed to fetch {url}: {repr(e)}\n{traceback.format_exc()}")
                    failed_count += 1
                is_finished = (done_count + failed_count) == len(urls)
                state = {
                    "status": "completed" if is_finished else "processing",
                    "total": len(urls),
                    "done": done_count,
                    "failed": failed_count
                }
                await redis_client.set(f"job:{job_id}", json.dumps(state), ex=86400)

async def status_handler(request: web.Request):
    job_id = request.match_info.get("job_id")
    redis_client = request.app["redis"]

    data = await redis_client.get(f"job:{job_id}")
    if not data:
        return web.json_response({"error": "Job not found or expired"}, status=404)

    return web.json_response(json.loads(data))


if __name__ == '__main__':
    web.run_app(init_app(), port=8080)
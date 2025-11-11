from fastapi import FastAPI
from fastapi.responses import StreamingResponse

from .src.main import search_stream


app = FastAPI()

async def event_stream(query: str):
    async for source, resources in search_stream(query):
        yield {
            "source" : source,
            "resources" : resources
        }

@app.get("/search")
async def search(query: str):
    async def stream():
        async for item in event_stream(query):
            yield (str(item) + "\n")
    
    return StreamingResponse(stream(), media_type="text/plain")


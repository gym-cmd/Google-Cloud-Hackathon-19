import os
import asyncio

import vertexai


PROJECT = os.environ["GOOGLE_CLOUD_PROJECT"]
LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "europe-west1")
AGENT_ENGINE_RESOURCE_ID = os.environ["AGENT_ENGINE_RESOURCE_ID"]

client = vertexai.Client(
    project=PROJECT,
    location=LOCATION,
)

adk_app = client.agent_engines.get(
    name=f"projects/{PROJECT}/locations/{LOCATION}/reasoningEngines/{AGENT_ENGINE_RESOURCE_ID}"
)


async def run():
    session = await adk_app.async_create_session(user_id="user-123")
    print("Session:", session)

    async for event in adk_app.async_stream_query(
        user_id="user-123",
        session_id=session["id"],
        message="I want to learn Python for data analysis",
    ):
        print(event)


if __name__ == "__main__":
    asyncio.run(run())

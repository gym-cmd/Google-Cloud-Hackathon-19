import vertexai
import asyncio


PROJECT = "qwiklabs-asl-03-35787841388f"
LOCATION = "europe-west1"
# get from https://console.cloud.google.com/vertex-ai/agents/agent-engines?authuser=0&project=qwiklabs-asl-03-35787841388f
EXAMPLE_LEARNING_ENGINE_RESOURCE_ID = "1982331503949905920"

client = vertexai.Client(  # For service interactions via client.agent_engines
    project=PROJECT,
    location=LOCATION,
)

adk_app = client.agent_engines.get(
    name=f"projects/{PROJECT}/locations/{LOCATION}/reasoningEngines/{EXAMPLE_LEARNING_ENGINE_RESOURCE_ID}"
)


async def run():
    # Create a session
    session = await adk_app.async_create_session(user_id="user-123")
    print("Session:", session)

    # Query the agent
    async for event in adk_app.async_stream_query(
        user_id="user-123",
        session_id=session["id"],
        message="What is the weather in NY?",
    ):
        print(event)

asyncio.run(run())
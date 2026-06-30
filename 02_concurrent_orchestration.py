import asyncio
import os

from agent_framework import Agent, Message
from agent_framework.foundry import FoundryChatClient
from agent_framework.orchestrations import ConcurrentBuilder
from azure.identity import AzureCliCredential
from dotenv import load_dotenv


load_dotenv()


client = FoundryChatClient(
    project_endpoint=os.environ.get("FOUNDRY_PROJECT_ENDPOINT"),
    model=os.environ.get("FOUNDRY_MODEL"),
    credential=AzureCliCredential(),
)

commercial_agent = Agent(
    client=client,
    name="commercial_agent",
    instructions="You assess market positioning, customer value, and pricing tradeoffs.",
)
legal_agent = Agent(
    client=client,
    name="legal_agent",
    instructions="You assess compliance risks, product claims, and regulatory concerns.",
)
technical_agent = Agent(
    client=client,
    name="technical_agent",
    instructions="You assess product feasibility, engineering tradeoffs, and implementation risks.",
)

workflow = ConcurrentBuilder(participants=[commercial_agent, legal_agent, technical_agent]).build()


async def main() -> None:
    prompt = "Review this budget e-bike launch proposal from commercial, legal, and technical angles."
    result = await workflow.run(prompt)

    print("===== Concurrent Orchestration =====")
    for output in result.get_outputs():
        messages: list[Message] = output
        for index, message in enumerate(messages, start=1):
            speaker = message.author_name or message.role
            print(f"{index:02d} [{speaker}] {message.text}")


if __name__ == "__main__":
    asyncio.run(main())
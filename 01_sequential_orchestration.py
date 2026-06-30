import asyncio
import os

from agent_framework import Agent, AgentResponse, Message
from agent_framework.foundry import FoundryChatClient
from agent_framework.orchestrations import SequentialBuilder
from azure.identity import AzureCliCredential
from dotenv import load_dotenv


load_dotenv()


client = FoundryChatClient(
    project_endpoint=os.environ.get("FOUNDRY_PROJECT_ENDPOINT"),
    model=os.environ.get("FOUNDRY_MODEL"),
    credential=AzureCliCredential(),
)

intake_agent = Agent(
    client=client,
    name="intake_agent",
    instructions=(
        "You extract the key requirements from a short business brief. "
        "Respond with a concise bullet summary."
    ),
)

drafter_agent = Agent(
    client=client,
    name="drafter_agent",
    instructions=(
        "You write a polished first draft based on the prior agent's summary. "
        "Keep the result short and practical."
    ),
)

workflow = SequentialBuilder(participants=[intake_agent, drafter_agent], output_from="all").build()


async def main() -> None:
    prompt = "We need a one-paragraph launch update for a new budget-friendly e-bike."
    result = await workflow.run(prompt)

    conversation = [Message(role="user", contents=[prompt])]
    for output in result.get_outputs():
        if isinstance(output, AgentResponse):
            conversation.extend(output.messages)

    print("===== Sequential Orchestration =====")
    for index, message in enumerate(conversation, start=1):
        speaker = message.author_name or ("assistant" if message.role == "assistant" else "user")
        print(f"{index:02d} [{speaker}] {message.text}")


if __name__ == "__main__":
    asyncio.run(main())
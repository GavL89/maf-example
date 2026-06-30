import asyncio
import os
from typing import cast

from agent_framework import Agent, AgentResponseUpdate, Message
from agent_framework.foundry import FoundryChatClient
from agent_framework.orchestrations import GroupChatBuilder
from azure.identity import AzureCliCredential
from dotenv import load_dotenv


load_dotenv()


client = FoundryChatClient(
    project_endpoint=os.environ.get("FOUNDRY_PROJECT_ENDPOINT"),
    model=os.environ.get("FOUNDRY_MODEL"),
    credential=AzureCliCredential(),
)

writer = Agent(
    client=client,
    name="writer",
    instructions="Write a crisp, useful first draft from the prompt.",
)
reviewer = Agent(
    client=client,
    name="reviewer",
    instructions="Review the draft, call out issues, and suggest a sharper revision.",
)
orchestrator_agent = Agent(
    client=client,
    name="orchestrator",
    instructions=(
        "You coordinate the conversation between writer and reviewer. "
        "Keep the discussion focused and stop after enough progress has been made."
    ),
)

workflow = GroupChatBuilder(
    participants=[writer, reviewer],
    orchestrator_agent=orchestrator_agent,
    intermediate_output_from=[writer, reviewer],
).with_termination_condition(lambda messages: sum(1 for msg in messages if msg.role == "assistant") >= 4).build()


async def main() -> None:
    task = "Draft a short launch tagline for a new budget-friendly e-bike."
    last_response_id: str | None = None
    output: list[Message] | None = None

    async for event in workflow.run(task, stream=True):
        if event.type in ("intermediate", "output") and isinstance(event.data, AgentResponseUpdate):
            response_id = event.data.response_id
            if response_id != last_response_id:
                if last_response_id is not None:
                    print()
                print(f"{event.data.author_name}:", end=" ", flush=True)
                last_response_id = response_id
            print(event.data.text, end="", flush=True)
        elif event.type == "output":
            output = cast(list[Message], event.data)

    if output:
        print("\n===== Group Chat =====")
        for message in output:
            print(f"{message.author_name or message.role}: {message.text}")


if __name__ == "__main__":
    asyncio.run(main())
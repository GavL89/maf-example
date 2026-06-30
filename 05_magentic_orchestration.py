import asyncio
import json
import os
from typing import cast

from agent_framework import Agent, AgentResponseUpdate, Message, WorkflowEvent
from agent_framework.foundry import FoundryChatClient
from agent_framework.orchestrations import MagenticBuilder, MagenticProgressLedger
from azure.identity import AzureCliCredential
from dotenv import load_dotenv


load_dotenv()


client = FoundryChatClient(
    project_endpoint=os.environ.get("FOUNDRY_PROJECT_ENDPOINT"),
    model=os.environ.get("FOUNDRY_MODEL"),
    credential=AzureCliCredential(),
)

researcher_agent = Agent(
    client=client,
    name="researcher_agent",
    description="Finds and summarizes relevant background information.",
    instructions="You are a researcher. Gather useful facts without doing unnecessary computation.",
)
analyst_agent = Agent(
    client=client,
    name="analyst_agent",
    description="Turns research into recommendations and conclusions.",
    instructions="You are an analyst. Synthesize findings into a practical recommendation.",
)
manager_agent = Agent(
    client=client,
    name="manager_agent",
    description="Coordinates a research-and-analysis workflow.",
    instructions="Coordinate the team to solve the user's task clearly and efficiently.",
)

workflow = MagenticBuilder(
    participants=[researcher_agent, analyst_agent],
    intermediate_output_from=[researcher_agent, analyst_agent],
    manager_agent=manager_agent,
    max_round_count=6,
    max_stall_count=2,
    max_reset_count=1,
).build()


async def main() -> None:
    task = "Summarize the main enterprise benefits of Microsoft Agent Framework for a local devcontainer demo."
    last_response_id: str | None = None
    output_event: WorkflowEvent | None = None

    async for event in workflow.run(task, stream=True):
        if event.type in ("intermediate", "output") and isinstance(event.data, AgentResponseUpdate):
            response_id = event.data.response_id
            if response_id != last_response_id:
                if last_response_id is not None:
                    print()
                print(f"- {event.executor_id}:", end=" ", flush=True)
                last_response_id = response_id
            print(event.data.text, end="", flush=True)
        elif event.type == "magentic_orchestrator":
            print(f"\n[Magentic] {event.data.event_type.name}")
            if isinstance(event.data.content, Message):
                print(event.data.content.text)
            elif isinstance(event.data.content, MagenticProgressLedger):
                print(json.dumps(event.data.content.to_dict(), indent=2))
        elif event.type == "output":
            output_event = event

    if output_event:
        transcript = cast(list[Message], output_event.data)
        print("\n===== Magentic Orchestration =====")
        for message in transcript:
            print(f"{message.author_name or message.role}: {message.text}")


if __name__ == "__main__":
    asyncio.run(main())
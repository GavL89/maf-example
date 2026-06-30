import asyncio
import os
from typing import Annotated, cast

from agent_framework import Agent, AgentResponse, Message, WorkflowEvent, WorkflowRunState, tool
from agent_framework.foundry import FoundryChatClient
from agent_framework.orchestrations import HandoffAgentUserRequest, HandoffBuilder
from azure.identity import AzureCliCredential
from dotenv import load_dotenv


load_dotenv()


@tool(approval_mode="never_require")
def lookup_order(order_id: Annotated[str, "Order identifier, for example EBIKE-123"]) -> str:
    return f"Order {order_id}: dispatched, with delivery scheduled for tomorrow."


def create_agents(client: FoundryChatClient) -> tuple[Agent, Agent, Agent]:
    triage_agent = Agent(
        client=client,
        name="triage_agent",
        instructions="Route the user's request to the correct specialist and explain why.",
        require_per_service_call_history_persistence=True,
    )
    billing_agent = Agent(
        client=client,
        name="billing_agent",
        instructions="Handle billing and refund questions. Keep answers short.",
        require_per_service_call_history_persistence=True,
        tools=[lookup_order],
    )
    technical_agent = Agent(
        client=client,
        name="technical_agent",
        instructions="Handle technical support for the product.",
        require_per_service_call_history_persistence=True,
    )
    return triage_agent, billing_agent, technical_agent


client = FoundryChatClient(
    project_endpoint=os.environ.get("FOUNDRY_PROJECT_ENDPOINT"),
    model=os.environ.get("FOUNDRY_MODEL"),
    credential=AzureCliCredential(),
)

triage_agent, billing_agent, technical_agent = create_agents(client)

workflow = HandoffBuilder(
    name="support_handoff",
    participants=[triage_agent, billing_agent, technical_agent],
    termination_condition=lambda conversation: bool(conversation) and "thanks" in conversation[-1].text.lower(),
).with_start_agent(triage_agent).build()


def handle_events(events: list[WorkflowEvent]) -> list[WorkflowEvent[HandoffAgentUserRequest]]:
    requests: list[WorkflowEvent[HandoffAgentUserRequest]] = []
    for event in events:
        if event.type == "handoff_sent":
            print(f"[handoff] {event.data.source} -> {event.data.target}")
        elif event.type == "status" and event.state in {WorkflowRunState.IDLE, WorkflowRunState.IDLE_WITH_PENDING_REQUESTS}:
            print(f"[status] {event.state}")
        elif event.type == "output":
            data = event.data
            if isinstance(data, AgentResponse):
                for message in data.messages:
                    if message.text:
                        print(f"[{message.author_name or message.role}] {message.text}")
            else:
                conversation = cast(list[Message], data)
                for message in conversation:
                    if message.text:
                        print(f"{message.author_name or message.role}: {message.text}")
        elif event.type == "request_info" and isinstance(event.data, HandoffAgentUserRequest):
            response = event.data.agent_response
            for message in response.messages:
                if message.text:
                    print(f"[{message.author_name or message.role}] {message.text}")
            requests.append(cast(WorkflowEvent[HandoffAgentUserRequest], event))
    return requests


async def main() -> None:
    initial_message = "My e-bike order EBIKE-123 arrived with a dead battery and I want to understand the return options."
    scripted_responses = ["The order number is EBIKE-123.", "Thanks for the help."]

    print(f"[user] {initial_message}")
    pending_requests = handle_events([event async for event in workflow.run(initial_message, stream=True)])

    while pending_requests:
        if scripted_responses:
            response_text = scripted_responses.pop(0)
            print(f"[user] {response_text}")
            responses = {req.request_id: HandoffAgentUserRequest.create_response(response_text) for req in pending_requests}
        else:
            responses = {req.request_id: HandoffAgentUserRequest.terminate() for req in pending_requests}

        pending_requests = handle_events(await workflow.run(responses=responses))


if __name__ == "__main__":
    asyncio.run(main())
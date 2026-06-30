import asyncio
import os
from collections.abc import Awaitable, Callable
from typing import Annotated

from agent_framework import Agent, AgentContext, FunctionInvocationContext, tool
from agent_framework.foundry import FoundryChatClient
from azure.identity import AzureCliCredential
from dotenv import load_dotenv


load_dotenv()


@tool(approval_mode="never_require")
def lookup_ticket(ticket_id: Annotated[str, "Support ticket id"]) -> str:
    return f"Ticket {ticket_id}: customer reported a broken charging cable."


async def security_agent_middleware(context: AgentContext, call_next: Callable[[], Awaitable[None]]) -> None:
    last_message = context.messages[-1] if context.messages else None
    if last_message and last_message.text and "secret" in last_message.text.lower():
        print("[middleware:agent] blocked sensitive request")
        return

    print(f"[middleware:agent] messages={len(context.messages)}")
    await call_next()


async def logging_function_middleware(
    context: FunctionInvocationContext,
    call_next: Callable[[], Awaitable[None]],
) -> None:
    print(f"[middleware:function] {context.function.name}")
    await call_next()
    print(f"[middleware:function] completed {context.function.name}")


client = FoundryChatClient(
    project_endpoint=os.environ.get("FOUNDRY_PROJECT_ENDPOINT"),
    model=os.environ.get("FOUNDRY_MODEL"),
    credential=AzureCliCredential(),
)

agent = Agent(
    client=client,
    name="support_agent",
    instructions="You help with support tickets and should use tools when needed.",
    tools=lookup_ticket,
    middleware=[security_agent_middleware, logging_function_middleware],
)


async def main() -> None:
    result = await agent.run("Check ticket T-123 and summarize it.")
    print(result.text)


if __name__ == "__main__":
    asyncio.run(main())
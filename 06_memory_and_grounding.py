import asyncio
import json
import os
from pathlib import Path
from typing import Annotated, Any

from dotenv import load_dotenv
from agent_framework import Agent, AgentSession, ContextProvider, InMemoryHistoryProvider, SessionContext, tool
from agent_framework.foundry import FoundryChatClient
from azure.identity import AzureCliCredential


load_dotenv()


MEMORY_FILE = Path(__file__).with_name("persistent_user_memory.json")


def _load_persistent_memory() -> dict[str, str]:
    if not MEMORY_FILE.exists():
        return {}
    try:
        data = json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return {str(k): str(v) for k, v in data.items()}
    except (OSError, json.JSONDecodeError):
        pass
    return {}


def _save_persistent_memory(memory: dict[str, str]) -> None:
    MEMORY_FILE.write_text(json.dumps(memory, indent=2), encoding="utf-8")


def _normalize_name(raw_name: str) -> str | None:
    candidate = raw_name.strip().split()[0].strip(".,!?\"'()[]{}")
    if not candidate or not candidate.isalpha():
        return None
    return candidate.capitalize()


@tool(approval_mode="never_require")
def store_user_name(user_name: Annotated[str, "The user's first name to persist"]) -> str:
    normalized_name = _normalize_name(user_name)
    if not normalized_name:
        return "Could not store name: provide a valid first name."

    _save_persistent_memory({"user_name": normalized_name})
    return f"Stored user name: {normalized_name}"


class PersistentUserMemoryProvider(ContextProvider):
    """ContextProvider-based memory using session state plus a simple file store."""

    DEFAULT_SOURCE_ID = "user_memory"

    def __init__(self) -> None:
        super().__init__(self.DEFAULT_SOURCE_ID)

    async def before_run(
        self,
        *,
        agent: Any,
        session: AgentSession | None,
        context: SessionContext,
        state: dict[str, Any],
    ) -> None:
        user_name = state.get("user_name")
        if not user_name:
            user_name = _load_persistent_memory().get("user_name")
            if user_name:
                state["user_name"] = user_name

        if user_name:
            context.extend_instructions(
                self.source_id,
                f"The user's name is {user_name}. Always address them by name. "
                "If the user provides a corrected name, call store_user_name immediately with the updated name.",
            )
        else:
            context.extend_instructions(
                self.source_id,
                "You don't know the user's name yet. Ask for it politely before handling other requests. "
                "As soon as the user gives their name (including short replies like 'Bob'), "
                "call store_user_name immediately before continuing.",
            )

    async def after_run(
        self,
        *,
        agent: Any,
        session: AgentSession | None,
        context: SessionContext,
        state: dict[str, Any],
    ) -> None:
        persisted_name = _load_persistent_memory().get("user_name")
        if persisted_name:
            state["user_name"] = persisted_name


memory_store = InMemoryHistoryProvider(load_messages=True)


client = FoundryChatClient(
    project_endpoint=os.environ.get("FOUNDRY_PROJECT_ENDPOINT"),
    model=os.environ.get("FOUNDRY_MODEL"),
    credential=AzureCliCredential(),
)

agent = Agent(
    client=client,
    name="memory_agent",
    instructions="You are a friendly assistant.",
    context_providers=[memory_store, PersistentUserMemoryProvider()],
    tools=[store_user_name],
)


async def main() -> None:
    session_one = agent.create_session()
    for prompt in [
        "Hello, I need help with my e-bike order.",
        "My name is Alice.",
        "What is the status of my order?",
    ]:
        result = await agent.run(prompt, session=session_one)
        print(f"User: {prompt}")
        print(f"Agent: {result}")

    provider_state = session_one.state.get("user_memory", {})
    print(f"[Session State] stored user name: {provider_state.get('user_name')}")

    session_two = agent.create_session()
    new_thread_prompt = "What is my name?"
    result = await agent.run(new_thread_prompt, session=session_two)
    print(f"User (new conversation): {new_thread_prompt}")
    print(f"Agent: {result}")


if __name__ == "__main__":
    asyncio.run(main())
import asyncio
import os
from typing import Annotated

from agent_framework import Agent, tool
from agent_framework.foundry import FoundryChatClient
from agent_framework.observability import configure_otel_providers, get_tracer
from azure.identity import AzureCliCredential
from dotenv import load_dotenv
from opentelemetry.trace import SpanKind
from opentelemetry.trace.span import format_trace_id


load_dotenv()


# DevUI entity discovery requires a module-level export named `agent` or `workflow`.
client = FoundryChatClient(
    credential=AzureCliCredential(),
    project_endpoint=os.environ.get("FOUNDRY_PROJECT_ENDPOINT"),
    model=os.environ.get("FOUNDRY_MODEL"),
)


@tool(approval_mode="never_require")
async def get_status(topic: Annotated[str, "The DevUI topic to inspect"]) -> str:
    return f"{topic}: the agent emitted a traceable run with tool use and event output."


agent = Agent(
    client=client,
    name="observability_agent",
    instructions="You explain why DevUI helps inspect agent behavior and you can use tools when helpful.",
    tools=get_status,
)


async def main() -> None:
    configure_otel_providers(enable_sensitive_data=True)

    with get_tracer().start_as_current_span("DevUI observability demo", kind=SpanKind.CLIENT) as current_span:
        print(f"Trace ID: {format_trace_id(current_span.get_span_context().trace_id)}")

        session = agent.create_session()
        for question in [
            "Why is DevUI useful for agent workflows?",
            "What do I inspect when a tool is selected?",
        ]:
            print(f"User: {question}")
            print(f"{agent.name}: ", end="")
            async for update in agent.run(question, session=session, stream=True):
                if update.text:
                    print(update.text, end="")
            print()


if __name__ == "__main__":
    asyncio.run(main())
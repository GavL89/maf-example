import asyncio
import os
from typing import Annotated

from agent_framework import Agent, tool
from agent_framework.foundry import FoundryChatClient
from azure.identity import AzureCliCredential
from dotenv import load_dotenv


load_dotenv()


@tool(approval_mode="never_require")
def calculate_price(
    quantity: Annotated[int, "How many bikes are being ordered"],
    product_tier: Annotated[str, "The product tier"],
) -> str:
    price_table = {"basic": 999, "plus": 1299, "pro": 1599}
    unit_price = price_table.get(product_tier.lower(), 999)
    total = quantity * unit_price
    return f"Tier={product_tier}, quantity={quantity}, unit_price={unit_price}, total={total}"


client = FoundryChatClient(
    project_endpoint=os.environ.get("FOUNDRY_PROJECT_ENDPOINT"),
    model=os.environ.get("FOUNDRY_MODEL"),
    credential=AzureCliCredential(),
)

agent = Agent(
    client=client,
    name="pricing_agent",
    instructions="Use the pricing tool for exact calculations and explain the result clearly.",
    tools=[calculate_price],
)


async def main() -> None:
    result = await agent.run("We need pricing for 3 pro bikes.")
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
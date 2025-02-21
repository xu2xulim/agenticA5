from typing import Dict, List, Optional

from fastapi import APIRouter, Body, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

from pydantic import BaseModel, Field
from pydantic_ai import Agent, ModelRetry, RunContext, Tool
from pydantic_ai.models.openai import OpenAIModel

import os

from app.dependencies.common import instantTrello, instantHandler, to_markdown
from app.core.config import settings

import httpx
import json

router = APIRouter()

model = OpenAIModel("gpt-4o")

# --------------------------------------------------------------
# 1. Simple Agent - Hello World Example
# --------------------------------------------------------------
"""
This example demonstrates the basic usage of PydanticAI agents.
Key concepts:
- Creating a basic agent with a system prompt
- Running synchronous queries
- Accessing response data, message history, and costs
"""

class ResponseModel(BaseModel):
    """Structured response with metadata."""

    response: str
    needs_escalation: bool
    follow_up_required: bool
    sentiment: str = Field(description="Customer sentiment analysis")

class TriageModel(BaseModel):
    """Structured response with metadata."""

    response: str
    needs_escalation: bool
    follow_up_required: bool
    sentiment: str = Field(description="Customer sentiment analysis")
    triage: str = Field(description="Message classification analysis")

@router.post("/agent/entry/{contactId}", status_code=200, tags=["Agent"])
async def simple (
    contactId : str,
    prompt: str
):

    agent = Agent(
        model=model,
        result_type=TriageModel,
        system_prompt=(
            "You are an intelligent customer support agent. "
            "Analyze queries carefully to classify the query into the following : General, Appointment, Order"
        ),  # These are known when writing the code
    )

    # Example usage of basic agent
    response = await agent.run(user_prompt=prompt)

    result = jsonable_encoder(response.data)

    print(result)

    if result['triage'] == 'Order' :
        async with httpx.AsyncClient() as client:
            r = await client.post(f"https://aiagent-w0r4nj3g.b4a.run/v1/agent/with_dep?prompt={prompt}")
            print(r)
            return JSONResponse(content=r.json())
    else:

        return JSONResponse(content={'response' : 'We will attend to your message shortly.'})

    return JSONResponse(content={'result' : 'Just Testing'})
    
# Define order schema
class Order(BaseModel):
    """Structure for order details."""

    order_id: str
    status: str
    items: List[str]


# Define customer schema
class CustomerDetails(BaseModel):
    """Structure for incoming customer queries."""

    customer_id: str
    name: str
    email: str
    orders: Optional[List[Order]] = None

@router.post("/agent/with_dep", status_code=200, tags=["Agent"])
async def simple (
    prompt: str
):
    def get_shipping_info(ctx: RunContext[CustomerDetails]) -> str:
        """Get the customer's shipping information."""
        return shipping_info_db[ctx.deps.orders[0].order_id]
    
    agent = Agent(
        model=model,
        result_type=ResponseModel,
        deps_type=CustomerDetails,
        retries=3,
        system_prompt=(
            "You are an intelligent customer support agent. "
            "Analyze queries carefully and provide structured responses. "
            "Use tools to look up relevant information."
            "Always greet the customer and provide a helpful response."
        ),  # These are known when writing the code
        tools=[Tool(get_shipping_info, takes_ctx=True)],  # Add tool via kwarg
    )

    @agent.system_prompt
    async def add_customer_name(ctx: RunContext[CustomerDetails]) -> str:
        return f"Customer details: {to_markdown(ctx.deps)}"  # These depend in some way on context that isn't known until runtime
    
    @agent.tool_plain()  # Add plain tool via decorator
    def get_shipping_status(order_id: str) -> str:
        """Get the shipping status for a given order ID."""
        shipping_status = shipping_info_db.get(order_id)
        if shipping_status is None:
            raise ModelRetry(
                f"No shipping information found for order ID {order_id}. "
                "Make sure the order ID starts with a #: e.g, #624743 "
                "Self-correct this if needed and try again."
            )
        return shipping_info_db[order_id]
    
    customer = CustomerDetails(
        customer_id="1",
        name="John Doe",
        email="john.doe@example.com",
        orders=[
            Order(order_id="12345", status="shipped", items=["Blue Jeans", "T-Shirt"]),
        ]
    )

    shipping_info_db: Dict[str, str] = {
        "12345": "Shipped on 2024-12-01",
        "67890": "Out for delivery",
    }

    # Example usage of basic agent
    #async with agent.run_stream(user_prompt=prompt, deps=customer) as response:
        
        #return JSONResponse(content= jsonable_encoder(await response.get_data()))

    response = await agent.run(user_prompt=prompt, deps=customer)
    
    
    return JSONResponse(content=jsonable_encoder(response.data))




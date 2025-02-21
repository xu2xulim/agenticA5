from typing import Dict, List, Optional

from fastapi import APIRouter, Body, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext #, Tool, ModelRetry,
from pydantic_ai.models.openai import OpenAIModel

import os
import httpx
import json

from app.dependencies.common import instantTrello, instantHandler, to_markdown
from app.core.config import settings

from dataclasses import dataclass

router = APIRouter()

model = OpenAIModel("gpt-4o")


@dataclass
class ClientAndKey:  
    http_client: httpx.AsyncClient
    api_key: str


identify_contact_agent = Agent(
    'openai:gpt-4o',
    deps_type=ClientAndKey,  
    system_prompt=(
        'Use the contacts to identify the contact'
    ),
)
get_contacts_agent = Agent(
    'openai:gpt-4o',
    deps_type=ClientAndKey,  
    result_type=list[str],
    system_prompt=(
        'Use the `get_contacts` tool to get contacts from GHL location, '
        'then try to find the contact that best fit the query'
    ),
)


@identify_contact_agent.tool
async def entry_agent (ctx: RunContext[ClientAndKey], count: int) -> list[str]:
    r = await get_contacts_agent.run(
        f'Uniquely identify the contact based on the query',
        deps=ctx.deps,  
        usage=ctx.usage,
    )
    return r.data


@get_contacts_agent.tool  
async def get_contacts(ctx: RunContext[ClientAndKey], count: int) -> str:
    response = await ctx.deps.http_client.get(
        'https://services.leadconnectorhq.com/contacts/',
        params={'locationId' : 'Q0f3mEZDVp9iwtG8HOvW'},
        headers={'Authorization': f'Bearer {ctx.deps.api_key}', 'Version' : '2021-07-28'},
    )
    response.raise_for_status()
    return response.text

@router.post("/delegation", status_code=200, tags=["Agent Delegation"])
async def main(
    prompt: str,
):
    async with httpx.AsyncClient() as client:
        deps = ClientAndKey(client, 'pit-2f70896a-f344-4010-ba7a-bb09271b4fa2')
        result = await identify_contact_agent.run(prompt, deps=deps)
        print(result.data)
        #> Did you hear about the toothpaste scandal? They called it Colgate.
        print(result.usage())  
        """

        Usage(
            requests=4,
            request_tokens=309,
            response_tokens=32,
            total_tokens=341,
            details=None,
        )
        """
        return JSONResponse(content=jsonable_encoder(result))
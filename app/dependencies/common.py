#from app.services.assistant_service import AssistantService
from app.core.config import settings
from fastapi.responses import JSONResponse

from pydantic import BaseModel

import datetime

import trello
import httpx

def to_markdown(data, indent=0):
    markdown = ""
    if isinstance(data, BaseModel):
        data = data.model_dump()
    if isinstance(data, dict):
        for key, value in data.items():
            markdown += f"{'#' * (indent + 2)} {key.upper()}\n"
            if isinstance(value, (dict, list, BaseModel)):
                markdown += to_markdown(value, indent + 1)
            else:
                markdown += f"{value}\n\n"
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, (dict, list, BaseModel)):
                markdown += to_markdown(item, indent)
            else:
                markdown += f"- {item}\n"
        markdown += "\n"
    else:
        markdown += f"{data}\n\n"
    return markdown 

async def instantTrello(case, data):

    instant_app_headers = {
        'Content-Type' : 'application/json',
        'instant-app-id' : settings.INSTANT_APP_ID,
        'instant-app-secret' : settings.INSTANT_APP_SECRET,
    }
    
    if case == 'getCredentials' :
        
        query = {'query': {'where' : {'project' : data['project']}}}
        url = f"https://{INSTANT_DETA_HOSTNAME}/v0/credentials/query"
        response = httpx.post(url, json=query, headers=instant_app_headers)
        if response.json()['count'] == 1:
            return response.json()['items'][0]
        else:
            return response.json()['items']
    
    elif case == 'getClient' :
        
        client = trello.TrelloClient(
            api_key = data['apikey'],
            token = data['token']
        )

        return client
    
    elif case == 'getContalistAPIHeader' :

        query = {'query': {'where' : {'project' : data['project']}}}
        url = f"https://{INSTANT_DETA_HOSTNAME}/v0/contalist/query"
        response = httpx.post(url, json=query, headers=instant_app_headers)
        if response.json()['count'] == 1:
            return  {
                "Content-Type" : "application/json",
                "Authorization" : f"APIKEY {response.json()['items'][0]['apikey']}",
                }
        else:
            return None

    else:
        return JSONResponse(content={'message' : f'Invalid Request'}, status_code=400)

async def instantHandler(case, collection, id, data):

    instant_app_headers = {
        'Content-Type' : 'application/json',
        'App-Id' : settings.INSTANT_APP_ID,
        'Authorization' : f"Bearer {settings.INSTANT_APP_SECRET}"
    }
    
    url = f"https://api.instantdb.com/admin/{case}"


    if case == 'transact' :

        if id == None:
            id = str(uuid.uuid4())

        data['created'] = datetime.now().isoformat()

        response = httpx.post(url, json={
           "steps": [
             [
               "update",
               collection,
               id,
               data
             ]
           ]
         }, headers=instant_app_headers)
        
    elif case =='query':
        
        response = httpx.post(url, json={'query' : data}, headers=instant_app_headers)
    else:
        return JSONResponse(content={'result' : 'Case not supported'})
    
    return JSONResponse(content=response.json())






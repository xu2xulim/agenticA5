from typing import Dict, List, Optional

from fastapi import APIRouter, WebSocket # Body, Request, BackgroundTasks
from fastapi.responses import HTMLResponse #JSONResponse
from pydantic import BaseModel, Field
from pydantic_ai import Agent #, ModelRetry, RunContext, Tool
from pydantic_ai.models.openai import OpenAIModel

import os

from app.dependencies.common import instantTrello, instantHandler, to_markdown
from app.core.config import settings

import httpx
import json

router = APIRouter()

model = OpenAIModel("gpt-4o")

html = """
<!DOCTYPE html>
<html>
<head>
    <title>WebSocket Example</title>
</head>
<body>
    <h1>WebSocket Example</h1>
    <button onclick="connectWebSocket()">Connect WebSocket</button>
    <script>
        function connectWebSocket() {
            const socket = new WebSocket('https://{hostname}/v1/socket/ws);
            socket.onmessage = function(event) {
                alert(`Message from server: ${event.data}`);
            };
            socket.onopen = function(event) {
                socket.send("Hello, Server!");
            };
        }
    </script>
</body>
</html>
""".format(hostname=settings.HOSTNAME)

@router.get("/socket/html")
async def get():
    return HTMLResponse(html)

@router.websocket("/socket/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    data = await websocket.receive_text()
    await websocket.send_text(f"Message text was: {data}")
    await websocket.close()


html_input = """
<!DOCTYPE html>
<html>
<head>
    <title>WebSocket Example</title>
</head>
<body>
    <h1>WebSocket Example</h1>
    <input id="userInput" type="text" placeholder="Enter your prompt here">
    <button onclick="sendMessage()">Send</button>
    <div id="response"></div>
    
    <script>
        let socket;

        function connectWebSocket() {
            socket = new WebSocket('https://${hostname}/v1/socket/ws_input');

            socket.onmessage = function(event) {
                const responseDiv = document.getElementById("response");
                responseDiv.innerHTML = `Message from server: ${event.data}`;
            };

            socket.onopen = function(event) {
                console.log("WebSocket connection established");
            };

            socket.onclose = function(event) {
                console.log("WebSocket connection closed");
            };

            socket.onerror = function(error) {
                console.log("WebSocket error:", error);
            };
        }

        function sendMessage() {
            const input = document.getElementById("userInput");
            const message = input.value;

            if (socket && socket.readyState === WebSocket.OPEN) {
                socket.send(message);
            } else {
                alert("WebSocket connection is not established.");
            }
        }

        // Establish WebSocket connection when the page loads
        window.onload = connectWebSocket;
    </script>
</body>
</html>
""".format(hostname=settings.HOSTNAME)

class UserPreferences(BaseModel):
    summary: list[str] = Field(description="The summary of user preferences")


agent = Agent(
    model=model,
    result_type=UserPreferences | str,  # type: ignore
    system_prompt=(
        "You're goal is to help the user to find the best smartphone model based on his preferences.\n"
        "- Ask questions one at a time.\n"
        "- Ask no more than 4 questions, but you may finish earlier if you gather enough information.\n"
        "- Focus on key aspects like budget, preferred OS, camera quality, battery life, and screen size.\n"
        "- Be concise but friendly in your questions.\n"
        "- After gathering information, provide a summary of preferences in the result.\n"
        "- Do not recommend specific phone models, just summarize preferences.\n"
        "- If user provides preferences without being asked, incorporate them into your understanding."
    ),
)

@router.get("/socket/html_input")
async def get():
    return HTMLResponse(html_input)

@router.websocket("/socket/ws_input")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    message_history = None
    while True:
        data = await websocket.receive_text()
        #response_message = f"Received your prompt: {data}"
        if data.lower() not in ["q", "quit", "exit"]:
            res = await agent.run(user_prompt=data, message_history=message_history)
            if isinstance(res.data, UserPreferences):
                break
            #user_prompt = input(f"{res.data}   ('q'/'quit'/'exit' to quit) > ")
            message_history = res.all_messages()
            await websocket.send_text(f"{res.data} ('q'/'quit'/'exit' to quit) >")
        else:
            await websocket.send_text(f"Thank you. Visit us again should you need any help on smartphone recommendations")
            await websocket.close()
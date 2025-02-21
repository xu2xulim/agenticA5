from app.core.config import settings

import json

async def create_note(contactId):

    url = f"https://services.leadconnectorhq.com/contacts/{contactId}/notes"

    return {"success" : True, "message" : "It is successful. Rgds "}
    
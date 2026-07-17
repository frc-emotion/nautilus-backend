from nautilus_api.controllers.utils import success_response
from nautilus_api.services import scouting_service

async def submit_data(data, collection_name):
    await scouting_service.submit(data, collection_name)
    return success_response("Scouting data submitted", 200)

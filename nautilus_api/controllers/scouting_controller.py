from nautilus_api.services import scouting_service

async def submit_data(data):
    print(data)
    await scouting_service.submit(data)
    return
from nautilus_api.services import scouting_service

async def submit_data(data, collection_name):
    print(data)
    print(collection_name)
    await scouting_service.submit(data)
    return
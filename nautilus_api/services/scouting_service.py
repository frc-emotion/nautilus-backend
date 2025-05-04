from quart import current_app

async def get_collection(collection_name: str):
    """Helper to retrieve a MongoDB collection from the current app's database."""
    return current_app.db[collection_name]

async def submit(data, collection_name):
    scouting_collection = await get_collection(collection_name)

    print(await scouting_collection.insert_one(data))
    return
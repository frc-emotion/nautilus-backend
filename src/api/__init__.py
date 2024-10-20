from quart import Quart
from quart import request

from dataclasses import dataclass
from datetime import datetime

from quart import Quart
from quart_schema import QuartSchema, validate_request, validate_response

app = Quart(__name__)

QuartSchema(app)

@app.get("/ping")
def ping():
    return {"message": "pong"}

def run() -> None:
    app.run()

    
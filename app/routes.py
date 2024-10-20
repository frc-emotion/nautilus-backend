from quart import Blueprint
from app.controllers.attendance import get_attendance, record_attendance
from app.controllers.scouting import get_scouting_data

api = Blueprint('api', __name__)

# @api.route("/attendance", methods=["GET"])
# async def attendance():
#     return await get_attendance()

# @api.route("/attendance", methods=["POST"])
# async def record():
#     return await record_attendance()

# @api.route("/scouting", methods=["GET"])
# async def scouting():
#     return await get_scouting_data()

def register_routes(app):
    app.register_blueprint(api, url_prefix="/api")
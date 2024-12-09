from nautilus_api import create_app
from nautilus_api.config import Config

app = create_app()

if __name__ == "__main__":
    try:
        app.run(host="0.0.0.0", port=Config.PORT, debug=Config.ENVIRONMENT != "prod")
    except Exception as e:
        app.logger.error(f"Error starting app: {e}")
        raise e
    finally:
        app.logger.stop()
        app.db.client.close()
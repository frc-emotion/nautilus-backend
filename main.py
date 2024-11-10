from app import create_app
from app.config import Config

app = create_app()

if __name__ == "__main__":
    try:
        app.run(host="0.0.0.0", port=7001, debug=Config.DEBUG)
    except Exception as e:
        app.logger.error(f"Error starting app: {e}")
        raise e
    finally:
        app.logger_listener.stop()
        app.db.client.close()
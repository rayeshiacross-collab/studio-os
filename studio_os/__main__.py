"""Allow `python -m studio_os` to start the API."""
import uvicorn
from .interfaces.api import app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

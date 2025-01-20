import uvicorn
from dotenv import load_dotenv

from fxfacebook.app import app

if __name__ == "__main__":
    load_dotenv()
    uvicorn.run(app, port=8041)

import uvicorn
from fastapi import FastAPI

from payments.entrypoints.http.routes import router



app = FastAPI()
app.include_router(router)


if __name__ == "__main__":

    uvicorn.run(app="payments.main:app", host="0.0.0.0", port=8000, reload=True)

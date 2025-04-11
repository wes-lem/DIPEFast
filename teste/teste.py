from fastapi import FastAPI
import uvicorn

app = FastAPI()


@app.get("/")
def read_root():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("teste:app", host="127.0.0.1", port=8000, reload=True)

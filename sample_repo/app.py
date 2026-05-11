from fastapi import FastAPI

app = FastAPI(title="Sample Service")


@app.get("/")
def root() -> dict:
    return {"message": "hello"}

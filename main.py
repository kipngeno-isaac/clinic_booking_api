from fastapi import FastAPI

app = FastAPI(title="Clinic Booking API")


@app.get("/")
def hello_world() -> dict[str, str]:
    return {"message": "Hello, World!"}

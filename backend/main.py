from fastapi import FastAPI

app = FastAPI(title="Rick & Morty AI Explorer")

@app.get("/")
async def read_root():
    return {"message": "Rick & Morty AI Backend is running!", "status": "ok"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

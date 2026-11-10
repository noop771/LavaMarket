from fastapi import FastAPI

from app.routers import products

app = FastAPI(title="LavaMarket API", version="0.1.0")

app.include_router(products.router)


@app.get("/")
async def root():
    return {"message": "LavaMarket API is running"}
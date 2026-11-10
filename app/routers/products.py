from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import Product
from app.schemas import ProductResponse

router = APIRouter(prefix="/products", tags=["products"])


@router.get("/", response_model=list[ProductResponse])
async def get_products(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product))
    products = result.scalars().all()
    return products
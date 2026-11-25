from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db import get_db
from app.dependencies import get_current_user
from app.models import Product, User, CartItem
from app.schemas import CartItemCreate, CartItemResponse


router = APIRouter(prefix="/cart", tags=["cart"])

@router.get("/", response_model=list[CartItemResponse])
async def get_cart(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(CartItem)
        .options(selectinload(CartItem.product))
        .where(CartItem.user_id == current_user.id)
    )
    items = result.scalars().all()
    return items

@router.post("/items", response_model=CartItemResponse, status_code=status.HTTP_201_CREATED)
async def add_to_cart(
    item_in: CartItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    product = await db.get(Product, item_in.product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    result = await db.execute(
        select(CartItem).where(
            CartItem.user_id == current_user.id,
            CartItem.product_id == item_in.product_id,
        )
    )
    cart_item = result.scalars().first()

    if cart_item is not None:
        cart_item.quantity += item_in.quantity
    else:
        cart_item = CartItem(
            user_id=current_user.id,
            product_id=item_in.product_id,
            quantity=item_in.quantity,
        )
        db.add(cart_item)

    if cart_item.quantity > product.stock_quantity:
        raise HTTPException(status_code=400, detail="Not enough stock")

    await db.commit()

    loaded = await db.execute(
        select(CartItem)
        .options(selectinload(CartItem.product))
        .where(CartItem.id == cart_item.id)
    )
    return loaded.scalars().first()

@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_to_cart(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cart_item = await db.get(CartItem, item_id)

    if cart_item is None or cart_item.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Cart item not found")
    await db.delete(cart_item)
    await db.commit()
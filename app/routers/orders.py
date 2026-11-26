from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db import get_db
from app.dependencies import get_current_user
from app.models import CartItem, Order, OrderItem, User
from app.schemas import OrderResponse

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(CartItem)
        .options(selectinload(CartItem.product))
        .where(CartItem.user_id == current_user.id)
    )
    cart_items = result.scalars().all()

    if not cart_items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cart is empty")
    total_price = Decimal("0")

    for item in cart_items:
        if item.product.stock_quantity < item.quantity:
            raise HTTPException(status_code=404, detail="Not enough stock")
        else:
            item.product.stock_quantity -= item.quantity

        total_price += item.product.price * item.quantity

    order = Order(
        user_id=current_user.id,
        total_price=total_price,
    )
    db.add(order)
    await db.flush()

    for item in cart_items:
        order_item = OrderItem(
            order_id=order.id,
            product_id=item.product_id,
            quantity=item.quantity,
            price_at_purchase=item.product.price,
        )
        db.add(order_item)
        await db.delete(item)

    await db.commit()

    loaded = await db.execute(
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.id == order.id)
    )
    return loaded.scalars().first()

@router.get("/", response_model=list[OrderResponse])
async def read_orders(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.user_id == current_user.id)
        .order_by(Order.created_at.desc())
    )

    return result.scalars().all()

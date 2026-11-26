from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Product, User


async def test_register_and_login(client: AsyncClient):
    #Регистрация пользователя
    reg_res = await client.post(
        "/auth/register",
        json={"email": "buyer@lava.ru", "password": "strongpassword"},
    )
    assert reg_res.status_code == 201
    assert reg_res.json()["email"] == "buyer@lava.ru"

    # Логин и проверка
    login_res = await client.post(
        "/auth/login",
        data={"username": "buyer@lava.ru", "password": "strongpassword"},
    )
    assert login_res.status_code == 200
    assert "access_token" in login_res.json()


async def test_product_permissions(client: AsyncClient, db_session: AsyncSession):
    # Создание пользователя и логин
    await client.post(
        "/auth/register",
        json={"email": "user@lava.ru", "password": "strongpassword"},
    )
    login_res = await client.post(
        "/auth/login",
        data={"username": "user@lava.ru", "password": "strongpassword"},
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    forbidden_res = await client.post(
        "/products/",
        json={"name": "Маргарита", "price": 500, "stock_quantity": 10},
        headers=headers,
    )
    assert forbidden_res.status_code == 403

    # Права админа в тестовой бд
    result = await db_session.execute(select(User).where(User.email == "user@lava.ru"))
    user = result.scalars().first()
    user.is_admin = True
    await db_session.commit()

    ok_res = await client.post(
        "/products/",
        json={"name": "Маргарита", "price": 500, "stock_quantity": 10},
        headers=headers,
    )
    assert ok_res.status_code == 201
    assert ok_res.json()["name"] == "Маргарита"


async def test_full_order_flow(client: AsyncClient, db_session: AsyncSession):
    pizza = Product(name="Дьябло", price=800, stock_quantity=10)
    db_session.add(pizza)
    await db_session.commit()
    await db_session.refresh(pizza)

    # Регистрация покупателя и получение токена
    await client.post(
        "/auth/register",
        json={"email": "hungry@lava.ru", "password": "strongpassword"},
    )
    login_res = await client.post(
        "/auth/login",
        data={"username": "hungry@lava.ru", "password": "strongpassword"},
    )
    headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    cart_res = await client.post(
        "/cart/items",
        json={"product_id": pizza.id, "quantity": 3},
        headers=headers,
    )
    assert cart_res.status_code == 201

    # Оформление заказа
    order_res = await client.post("/orders/", headers=headers)
    assert order_res.status_code == 201
    order_data = order_res.json()
    assert order_data["total_price"] == 2400.0
    assert len(order_data["items"]) == 1

    # Проверка корзины
    empty_cart = await client.get("/cart/", headers=headers)
    assert empty_cart.json() == []

    product_res = await client.get(f"/products/{pizza.id}")
    assert product_res.json()["stock_quantity"] == 7

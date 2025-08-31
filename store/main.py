from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, APIRouter, Body, Depends, HTTPException, Path, Query, status
from pydantic import UUID4

from store.core.config import settings
from store.core.exceptions import NotFoundException, DuplicateException
from store.models.product import ProductModel
from store.schemas.product import ProductIn, ProductOut, ProductUpdate, ProductUpdateOut


# --- Usecase ---
class ProductUsecase:

    async def create(self, body: ProductIn) -> ProductOut:
        existing = await ProductModel.find_one({"name": body.name})
        if existing:
            raise DuplicateException(message=f"Produto '{body.name}' já existe.")
        new_product = await ProductModel.insert_one(body.dict())
        created = await ProductModel.find_one({"_id": new_product.inserted_id})
        return ProductOut(**created)

    async def get(self, id: str) -> ProductOut:
        product = await ProductModel.find_one({"_id": id})
        if not product:
            raise NotFoundException(message=f"Produto com id {id} não encontrado.")
        return ProductOut(**product)

    async def query(self, min_price: Optional[float] = None, max_price: Optional[float] = None) -> List[ProductOut]:
        query_filter = {}
        if min_price is not None or max_price is not None:
            query_filter["price"] = {}
            if min_price is not None:
                query_filter["price"]["$gte"] = min_price
            if max_price is not None:
                query_filter["price"]["$lte"] = max_price

        products_cursor = ProductModel.find(query_filter)
        products = await products_cursor.to_list(length=100)
        return [ProductOut(**p) for p in products]

    async def update(self, id: str, body: ProductUpdate) -> ProductUpdateOut:
        update_data = {k: v for k, v in body.dict().items() if v is not None}

        result = await ProductModel.update_one({"_id": id}, {"$set": update_data})
        if result.matched_count == 0:
            raise NotFoundException(message=f"Produto com id {id} não encontrado.")

        updated_product = await ProductModel.find_one({"_id": id})
        return ProductUpdateOut(**updated_product)

    async def delete(self, id: str) -> None:
        result = await ProductModel.delete_one({"_id": id})
        if result.deleted_count == 0:
            raise NotFoundException(message=f"Produto com id {id} não encontrado.")


# --- Router de produtos ---
router = APIRouter(tags=["products"])

@router.post("/", status_code=status.HTTP_201_CREATED)
async def post(body: ProductIn = Body(...), usecase: ProductUsecase = Depends()) -> ProductOut:
    try:
        return await usecase.create(body=body)
    except DuplicateException as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message)

@router.get("/{id}", status_code=status.HTTP_200_OK)
async def get(id: UUID4 = Path(...), usecase: ProductUsecase = Depends()) -> ProductOut:
    try:
        return await usecase.get(id=id)
    except NotFoundException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)

@router.get("/", status_code=status.HTTP_200_OK)
async def query(
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    usecase: ProductUsecase = Depends()
) -> List[ProductOut]:
    return await usecase.query(min_price=min_price, max_price=max_price)

@router.patch("/{id}", status_code=status.HTTP_200_OK)
async def patch(
    id: UUID4 = Path(...),
    body: ProductUpdate = Body(...),
    usecase: ProductUsecase = Depends()
) -> ProductUpdateOut:
    try:
        if body.updated_at is None:
            body.updated_at = datetime.utcnow()
        return await usecase.update(id=id, body=body)
    except NotFoundException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(id: UUID4 = Path(...), usecase: ProductUsecase = Depends()) -> None:
    try:
        await usecase.delete(id=id)
    except NotFoundException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)


# --- App FastAPI ---
class App(FastAPI):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(
            *args,
            **kwargs,
            version="0.0.1",
            title=settings.PROJECT_NAME,
            root_path=settings.ROOT_PATH
        )

app = App()
app.include_router(router, prefix="/products")

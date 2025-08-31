from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query, status
from pydantic import UUID4
from store.core.exceptions import NotFoundException, DuplicateException
from store.schemas.product import ProductIn, ProductOut, ProductUpdate, ProductUpdateOut
from store.usecases.product import ProductUsecase

router = APIRouter(tags=["products"])

# --- Create ---
@router.post("/", status_code=status.HTTP_201_CREATED)
async def post(
    body: ProductIn = Body(...),
    usecase: ProductUsecase = Depends()
) -> ProductOut:
    try:
        return await usecase.create(body=body)
    except DuplicateException as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message)

# --- Get by ID ---
@router.get("/{id}", status_code=status.HTTP_200_OK)
async def get(
    id: UUID4 = Path(...),
    usecase: ProductUsecase = Depends()
) -> ProductOut:
    try:
        return await usecase.get(id=id)
    except NotFoundException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)

# --- Query with filters ---
@router.get("/", status_code=status.HTTP_200_OK)
async def query(
    min_price: Optional[float] = Query(None, description="Preço mínimo"),
    max_price: Optional[float] = Query(None, description="Preço máximo"),
    usecase: ProductUsecase = Depends()
) -> List[ProductOut]:
    return await usecase.query(min_price=min_price, max_price=max_price)

# --- Update ---
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

# --- Delete ---
@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(
    id: UUID4 = Path(...),
    usecase: ProductUsecase = Depends()
) -> None:
    try:
        await usecase.delete(id=id)
    except NotFoundException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)

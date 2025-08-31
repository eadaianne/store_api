from typing import List
from fastapi import APIRouter, Body, Depends, HTTPException, Path, status
from pydantic import UUID4
from store.core.exceptions import NotFoundException

from store.schemas.product import ProductIn, ProductOut, ProductUpdate, ProductUpdateOut
from store.usecases.product import ProductUsecase

router = APIRouter(tags=["products"])


@router.post(path="/", status_code=status.HTTP_201_CREATED)
async def post(
    body: ProductIn = Body(...), usecase: ProductUsecase = Depends()
) -> ProductOut:
    return await usecase.create(body=body)


@router.get(path="/{id}", status_code=status.HTTP_200_OK)
async def get(
    id: UUID4 = Path(alias="id"), usecase: ProductUsecase = Depends()
) -> ProductOut:
    try:
        return await usecase.get(id=id)
    except NotFoundException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)


@router.get("/", status_code=200)
async def query(
    min_price: Optional[float] = Query(None, description="Preço mínimo"),
    max_price: Optional[float] = Query(None, description="Preço máximo"),
    usecase: ProductUsecase = Depends()
) -> List[ProductOut]:
    """
    Lista produtos com filtros opcionais de preço.
    Exemplo: /?min_price=5000&max_price=8000
    """
    return await usecase.query(min_price=min_price, max_price=max_price)


@router.patch("/{id}", status_code=status.HTTP_200_OK)
async def patch(
    id: UUID4 = Path(...),
    body: ProductUpdate = Body(...),
    usecase: ProductUsecase = Depends()
) -> ProductUpdateOut:
    """
    Atualiza um produto. 
    - Retorna 404 se não encontrado.
    - Atualiza updated_at automaticamente.
    - Permite sobrescrever updated_at manualmente.
    """
    try:
        if body.updated_at is None:
            body.updated_at = datetime.utcnow()
        return await usecase.update(id=id, body=body)
    except NotFoundException as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.message
        )


@router.delete(path="/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(
    id: UUID4 = Path(alias="id"), usecase: ProductUsecase = Depends()
) -> None:
    try:
        await usecase.delete(id=id)
    except NotFoundException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)

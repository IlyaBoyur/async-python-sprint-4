from typing import Any, Generic, Type, TypeVar

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import func

from db.db import Base


class Repository:
    def get(self, *args, **kwargs):
        raise NotImplementedError

    def get_multi(self, *args, **kwargs):
        raise NotImplementedError

    def create(self, *args, **kwargs):
        raise NotImplementedError

    def update(self, *args, **kwargs):
        raise NotImplementedError

    def delete(self, *args, **kwargs):
        raise NotImplementedError


ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class RepositoryDB(
    Repository, Generic[ModelType, CreateSchemaType, UpdateSchemaType]
):
    def __init__(self, model: Type[ModelType]):
        self._model = model

    async def get(self, db: AsyncSession, id: Any) -> ModelType | None:
        statement = select(self._model).where(self._model.id == id)
        results = await db.execute(statement=statement)
        return results.scalar_one_or_none()

    async def get_multi(
        self, db: AsyncSession, *, filter=dict[str, Any], skip=0, limit=100
    ) -> list[ModelType]:
        statement = (
            select(self._model).filter_by(**filter).offset(skip).limit(limit)
        )
        results = await db.execute(statement=statement)
        return results.scalars().all()

    async def create(
        self, db: AsyncSession, *, object_in: CreateSchemaType | dict[str, Any]
    ) -> ModelType:
        object_in_data = jsonable_encoder(object_in)
        db_object = self._model(**object_in_data)
        db.add(db_object)
        await db.commit()
        await db.refresh(db_object)
        return db_object

    async def update(
        self,
        db: AsyncSession,
        *,
        db_object: ModelType,
        object_in: UpdateSchemaType | dict[str, Any],
    ) -> ModelType:
        obj_in_data = jsonable_encoder(object_in)
        obj_in_data.pop("id")
        statement = (
            update(self._model)
            .where(self._model.id == db_object.id)
            .values(**obj_in_data)
        )
        await db.execute(statement=statement)
        await db.refresh(db_object)
        return db_object

    async def delete(self, db: AsyncSession, *, id: int) -> None:
        db_object = db.get(entity=self._model, ident=id)
        await db.delete(db_object)
        await db.commit()

    async def count(self, db: AsyncSession, *, filter=dict[str, Any]) -> int:
        statement = (
            select(self._model)
            .filter_by(**filter)
            .with_only_columns(*[func.count()])
            .order_by(None)
        )
        result = await db.execute(statement=statement)
        return result.scalar()

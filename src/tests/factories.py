import factory

from models.models import BlacklistedClient, ShortenedURL, ShortenedURLUse

from .conftest import testing_session


class AsyncModelFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        abstract = True

    @classmethod
    def _save(cls, model_class, session, args, kwargs):
        """Add asynchronous creation support"""

        async def create_coro(*args, **kwargs):
            db_object = model_class(*args, **kwargs)
            async with session() as s:
                s.add(db_object)
                await s.commit()
                await s.refresh(db_object)
            return db_object

        return create_coro(*args, **kwargs)


class ShortenedURLFactory(AsyncModelFactory):
    class Meta:
        model = ShortenedURL
        sqlalchemy_session = testing_session


class ShortenedURLUseFactory(AsyncModelFactory):
    class Meta:
        model = ShortenedURLUse
        sqlalchemy_session = testing_session


class BlacklistClientFactory(AsyncModelFactory):
    host = factory.Faker("ipv4")
    until = factory.Faker("date_time")

    class Meta:
        model = BlacklistedClient
        sqlalchemy_session = testing_session

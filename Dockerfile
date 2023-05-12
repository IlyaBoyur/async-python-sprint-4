# Указываем образ, от которого берётся наследование
FROM python:3.11-slim
EXPOSE 8080/tcp
WORKDIR /code
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt
COPY src src
COPY migrations migrations
COPY alembic.ini alembic.ini
COPY pytest.ini pytest.ini
COPY setup.cfg setup.cfg
COPY entrypoint.sh entrypoint.sh
RUN chmod +x entrypoint.sh


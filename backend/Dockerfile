# backend/Dockerfile
FROM python:3.10-slim

WORKDIR /app

RUN pip install websockets

COPY websocket_server.py .

EXPOSE 8765

CMD ["python", "websocket_server.py"]
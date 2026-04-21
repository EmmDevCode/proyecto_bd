# backend/Dockerfile
FROM python:3.10-slim

WORKDIR /app

# Instalamos solo la librería necesaria para el server
RUN pip install websockets

# Copiamos el script al contenedor
COPY websocket_server.py .

# Exponemos el puerto
EXPOSE 8765

# Comando para iniciar el servidor
CMD ["python", "websocket_server.py"]
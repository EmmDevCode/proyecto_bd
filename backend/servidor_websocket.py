# backend/websocket_server.py
import asyncio
import websockets
import json

clientes_conectados = set()

async def manejador_conexiones(websocket):
    # Registrar nuevo cliente
    clientes_conectados.add(websocket)
    print(f"Nuevo cliente conectado. Total: {len(clientes_conectados)}")
    try:
        # Escuchar mensajes continuamente
        async for mensaje in websocket:
            print(f"Mensaje recibido: {mensaje}")
            # Reenviar el mensaje a todos los DEMÁS clientes conectados 
            for cliente in clientes_conectados:
                if cliente != websocket:
                    await cliente.send(mensaje)
    except websockets.exceptions.ConnectionClosed:
        print("Un cliente se ha desconectado.")
    finally:
        # Eliminar al cliente cuando cierre el programa
        clientes_conectados.remove(websocket)

async def main():
    print("Iniciando Servidor WebSocket en ws://localhost:8765...")
    # Inicia el servidor en el puerto 8765
    async with websockets.serve(manejador_conexiones, "localhost", 8765):
        await asyncio.Future()  # Ejecutar para siempre

if __name__ == "__main__":
    asyncio.run(main())
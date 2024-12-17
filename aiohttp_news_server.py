import aiohttp
from aiohttp import web
import asyncio
import json

# Список для хранения подключенных веб-сокетов
connected_clients = []

# Обработчик для подключения веб-сокетов
async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    # Добавляем клиента в список
    connected_clients.append(ws)
    print('Новый клиент подключился')

    # Ожидание сообщений от клиента (не используем для чего-либо, просто пинг)
    try:
        async for msg in ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                print(f'Получено сообщение от клиента: {msg.data}')
            elif msg.type == aiohttp.WSMsgType.ERROR:
                print(f'Ошибка WebSocket: {ws.exception()}')
    finally:
        # Убираем клиента из списка, если он отключился
        connected_clients.remove(ws)
    print('Клиент отключился')
    return ws

# Обработчик POST запросов для приема новостей
async def post_news_handler(request):
    try:
        data = await request.json()
        news_message = data.get('message', 'Без сообщения')
        print(f'Получены новости: {news_message}')

        # Рассылка новостей всем подключенным клиентам
        for ws in connected_clients:
            if not ws.closed:
                await ws.send_str(news_message)

        return web.json_response({'status': 'success'})
    except Exception as e:
        return web.json_response({'status': 'error', 'message': str(e)}, status=500)

# Периодическая проверка соединения (ping)
async def ping_clients(app):
    while True:
        for ws in connected_clients:
            if not ws.closed:
                try:
                    await ws.ping()
                except Exception as e:
                    print(f'Ошибка при отправке ping: {e}')
        await asyncio.sleep(10)  # Интервал пинга 10 секунд

# Запуск сервера и роутов
async def init_app():
    app = web.Application()
    app.router.add_get('/ws', websocket_handler)
    app.router.add_post('/news', post_news_handler)

    # Фоновая задача для пингования клиентов
    app.on_startup.append(lambda app: asyncio.create_task(ping_clients(app)))

    return app

# Маршрут для клиентской страницы
async def index(request):
    return web.FileResponse('index.html')

# Добавим маршрут для страницы и запустим сервер
if __name__ == '__main__':
    app = asyncio.run(init_app())
    web.run_app(app, host='localhost', port=8080)
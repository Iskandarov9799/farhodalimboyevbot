"""
Render.com "uxlab qolmasligi" uchun oddiy HTTP server.
Bot bilan parallel ishga tushadi.
"""
from aiohttp import web
import asyncio

async def health_check(request):
    return web.Response(text="✅ Bot ishlayapti!", status=200)

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", health_check)
    app.router.add_get("/health", health_check)
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()
    print("🌐 Web server port 8080 da ishga tushdi")

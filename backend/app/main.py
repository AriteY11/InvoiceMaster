from contextlib import asynccontextmanager

import hmac

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .api.routes.invoices import router as invoices_router
from .api.routes.stats import router as stats_router
from .config import STATIC_DIR, ensure_directories, settings
from .db import init_db


@asynccontextmanager
async def lifespan(_: FastAPI):
    ensure_directories()
    init_db()
    yield


app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# 设置 INVOICEMASTER_API_TOKEN 后启用 Bearer Token 鉴权（未设置时完全关闭）。
# /api/health 保持公开，供桌面壳与部署脚本就绪探测使用。
if settings.api_token:

    @app.middleware('http')
    async def require_api_token(request: Request, call_next):
        path = request.url.path
        if path.startswith('/api/') and path != '/api/health':
            authorization = request.headers.get('Authorization', '')
            token = authorization[7:].strip() if authorization.startswith('Bearer ') else ''
            if not hmac.compare_digest(token, settings.api_token):
                return JSONResponse(status_code=401, content={'detail': '未授权：API Token 缺失或无效'})
        return await call_next(request)


app.include_router(invoices_router)
app.include_router(stats_router)


@app.get('/api/health')
def health_check() -> dict[str, str]:
    return {'status': 'ok', 'service': settings.app_name}


if STATIC_DIR.exists():
    assets_dir = STATIC_DIR / 'assets'
    if assets_dir.exists():
        app.mount('/assets', StaticFiles(directory=assets_dir), name='assets')

    favicon = STATIC_DIR / 'favicon.svg'
    if favicon.exists():

        @app.get('/favicon.svg', include_in_schema=False)
        def serve_favicon() -> FileResponse:
            return FileResponse(favicon)

    @app.get('/', include_in_schema=False)
    def serve_index() -> FileResponse:
        return FileResponse(STATIC_DIR / 'index.html')

    @app.api_route('/{full_path:path}', methods=['GET'], include_in_schema=False)
    async def spa_fallback(full_path: str, request: Request):
        if full_path.startswith('api/'):
            return JSONResponse(status_code=404, content={'detail': 'Not Found'})

        candidate = STATIC_DIR / full_path
        if candidate.exists() and candidate.is_file():
            return FileResponse(candidate)

        index_file = STATIC_DIR / 'index.html'
        if index_file.exists():
            return FileResponse(index_file)

        return JSONResponse(status_code=404, content={'detail': 'Not Found'})
else:

    @app.api_route('/{full_path:path}', methods=['GET'], include_in_schema=False)
    async def api_fallback(full_path: str) -> dict[str, object]:
        return {
            'message': 'InvoiceMaster backend is running.',
            'api_docs': '/docs',
            'static_ready': False,
        }

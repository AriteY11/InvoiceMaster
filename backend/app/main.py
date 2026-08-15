from contextlib import asynccontextmanager

import hmac

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .api.routes.auth import router as auth_router
from .api.routes.invoices import router as invoices_router
from .api.routes.stats import router as stats_router
from .config import STATIC_DIR, ensure_directories, settings
from .db import SessionLocal, init_db
from .models.auth import Account, AuthSession


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

# 鉴权三模式（按优先级）：
# 1. 设置 INVOICEMASTER_API_TOKEN  → 静态 Bearer Token 鉴权（/api/health 除外）；
#    若同时存在账号，账号会话 Token 同样有效（任一生效）。
# 2. 数据库存在账号               → 账号会话鉴权（登录后携带会话 Token；/api/health、/api/auth/login 除外）
# 3. 无账号且无静态 Token         → 不鉴权（离线版桌面应用即此模式）
_PUBLIC_PATHS = {"/api/health", "/api/auth/login"}


@app.middleware('http')
async def auth_middleware(request: Request, call_next):
    path = request.url.path
    request.state.username = None
    request.state.session_token = None
    if not path.startswith('/api/') or path in _PUBLIC_PATHS:
        return await call_next(request)

    api_token = settings.api_token
    authorization = request.headers.get('Authorization', '')
    bearer = authorization[7:].strip() if authorization.startswith('Bearer ') else ''

    if api_token and bearer and hmac.compare_digest(bearer, api_token):
        return await call_next(request)

    db = SessionLocal()
    try:
        has_accounts = db.query(Account.id).first() is not None
        if not has_accounts:
            if api_token:
                return JSONResponse(status_code=401, content={'detail': '未授权：API Token 缺失或无效'})
            return await call_next(request)

        if not bearer:
            return JSONResponse(status_code=401, content={'detail': '未登录：请先登录'})

        session = db.query(AuthSession).filter(AuthSession.token == bearer).first()
        if session is None:
            return JSONResponse(status_code=401, content={'detail': '登录已失效：请重新登录'})
        if session.is_expired():
            db.delete(session)
            db.commit()
            return JSONResponse(status_code=401, content={'detail': '登录已过期：请重新登录'})
        request.state.username = session.username
        request.state.session_token = session.token
        return await call_next(request)
    finally:
        db.close()


app.include_router(auth_router)
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

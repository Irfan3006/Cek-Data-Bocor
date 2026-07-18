import logging
import sys
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError

from api.routers.check import router as check_router
from api.core.middleware import SecurityHeadersMiddleware
from api.config.config import settings

# Inisialisasi logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger(__name__)

# Buat aplikasi FastAPI
# docs_url=None dan redoc_url=None untuk menyembunyikan spesifikasi API di lingkungan production (Security Best Practice)
app = FastAPI(
    title="Cek Kebocoran Data API",
    description="Backend API untuk mendeteksi kebocoran email menggunakan database XposedOrNot.",
    version="1.0.0",
    docs_url=None,
    redoc_url=None
)

# 1. Tambahkan Middleware Keamanan (Security Headers)
app.add_middleware(SecurityHeadersMiddleware)

# 2. Tambahkan Middleware CORS
# Mengizinkan akses dari frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["Content-Type", "Accept"],
    max_age=3600
)

# 3. Daftarkan router dengan prefix /api
app.include_router(check_router, prefix="/api")

# 4. Exception Handler untuk Validasi Input (Email tidak valid, parameter kurang)
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    logger.warning(f"Validation error for path {request.url.path}: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status": "error",
            "detail": "Format input tidak valid. Pastikan alamat email yang dimasukkan benar."
        }
    )

# 5. Global Exception Handler untuk menyembunyikan stack trace sistem internal dari client
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(f"Unhandled exception on {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "detail": "Terjadi kesalahan internal pada server. Silakan coba beberapa saat lagi."
        }
    )

# Endpoint health check dasar untuk verifikasi serverless status
@app.get("/api/health", tags=["System"])
async def health_check():
    return {"status": "ok", "message": "API Cek Kebocoran Data aktif."}

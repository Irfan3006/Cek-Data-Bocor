import time
from fastapi import APIRouter, Depends, Query, HTTPException, status
from pydantic import EmailStr
from typing import Dict, Any

from api.schemas.check import CheckResponse, BreachDetail, EmailCheckRequest
from api.cache.store import cache_store
from api.core.limiter import rate_limit_dependency
from api.core.pow import challenge_manager
from api.services.xposedornot import xon_service
from api.risk.calculator import risk_calculator
from api.recommendation.engine import recommendation_engine
from api.config.config import settings
from api.services.translator import translator_service

router = APIRouter()

@router.post(
    "/check",
    response_model=CheckResponse,
    summary="Periksa kebocoran email",
    description="Memeriksa apakah email pernah bocor, mengembalikan detail kebocoran, skor risiko, dan rekomendasi mitigasi.",
    dependencies=[Depends(rate_limit_dependency)]
)
async def check_email(
    request_data: EmailCheckRequest
) -> Any:
    if not challenge_manager.validate_solution(
        request_data.challenge,
        request_data.nonce,
        request_data.challenge_token,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Verifikasi keamanan gagal. Silakan muat ulang halaman dan coba lagi.",
        )

    normalized_email = str(request_data.email).strip().lower()
    
    cached_result = cache_store.get(normalized_email)
    if cached_result:
        response_data = cached_result.copy()
        response_data["cached"] = True
        return response_data

    try:
        breaches_raw = await xon_service.check_email_breaches(normalized_email)
    except HTTPException as e:
        raise e
    except Exception as e:
        # Sembunyikan stack trace internal untuk alasan keamanan
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Terjadi kesalahan internal pada server saat memeriksa data."
        )

    breaches_list = []
    is_breached = len(breaches_raw) > 0
    status_text = "success" if is_breached else "clean"
    
    for b in breaches_raw:
        raw_xposed = b.get("xposed_data", "")
        xposed_clean = raw_xposed.replace(";", ", ").replace(" ,", ",")
        raw_records = b.get("xposed_records", 0)
        try:
            records_int = int(raw_records)
        except (ValueError, TypeError):
            records_int = 0
        
        raw_pwd_risk = b.get("password_risk")
        pwd_risk_translated = None
        if raw_pwd_risk:
            pwd_risk_lower = str(raw_pwd_risk).strip().lower()
            if pwd_risk_lower == "plaintext":
                pwd_risk_translated = "Teks Polos (Plaintext)"
            elif pwd_risk_lower == "unknown":
                pwd_risk_translated = "Tidak Diketahui"
            elif pwd_risk_lower == "encrypted":
                pwd_risk_translated = "Terenkripsi"
            elif pwd_risk_lower == "easytocrack":
                pwd_risk_translated = "Lemah (Mudah Didekripsi)"
            elif pwd_risk_lower in ("hardtocrack", "stronghash"):
                pwd_risk_translated = "Kuat (Sulit Didekripsi)"
            else:
                pwd_risk_translated = raw_pwd_risk.title()

        breaches_list.append(
            BreachDetail(
                breach=b.get("breach", "Tidak Diketahui"),
                details=b.get("details", "Detail kebocoran tidak tersedia."),
                domain=b.get("domain", ""),
                industry=b.get("industry", "Umum"),
                logo=b.get("logo", ""),
                breach_date=b.get("xposed_date"),
                records=records_int,
                password_risk=pwd_risk_translated,
                xposed_data=xposed_clean
            )
        )

    if breaches_list:
        descriptions = [b.details for b in breaches_list]
        translated = await translator_service.translate_batch(descriptions)
        for i, b in enumerate(breaches_list):
            b.details = translated[i]

    risk_assessment = risk_calculator.calculate_risk(breaches_raw)

    recommendations = recommendation_engine.generate_recommendations(breaches_raw)

    result = {
        "email": normalized_email,
        "is_breached": is_breached,
        "status": status_text,
        "breaches_count": len(breaches_list),
        "breaches": breaches_list,
        "risk_assessment": risk_assessment.model_dump(),
        "recommendations": [r.model_dump() for r in recommendations],
        "cached": False,
        "timestamp": time.time()
    }

    cache_store.set(normalized_email, result, settings.cache_ttl_seconds)

    return result

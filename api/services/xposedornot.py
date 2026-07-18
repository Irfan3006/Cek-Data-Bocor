import httpx
from fastapi import HTTPException, status
from api.config.config import settings

class XposedOrNotService:
    def __init__(self) -> None:
        self.api_url = settings.xposedornot_api_url
        self.headers = {
            "User-Agent": "Cek-Kebocoran-Data-ID/1.0",
            "Accept": "application/json"
        }

    async def check_email_breaches(self, email: str) -> list[dict]:
        """
        Memanggil API XposedOrNot untuk mendapatkan data kebocoran email secara detail.
        Mengembalikan list rincian kebocoran (breach details).
        Jika tidak ada kebocoran (404), mengembalikan list kosong [].
        """
        normalized_email = email.strip().lower()
        url = f"{self.api_url}/breach-analytics"
        params = {"email": normalized_email}

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(url, params=params, headers=self.headers)
                
                if response.status_code == status.HTTP_404_NOT_FOUND:
                    return []
                
                if response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
                    retry_after = response.headers.get("Retry-After", "60")
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail="Layanan eksternal sedang sibuk. Silakan coba lagi nanti.",
                        headers={"Retry-After": retry_after}
                    )
                
                if response.status_code == status.HTTP_200_OK:
                    data = response.json()
                    exposed_breaches = data.get("ExposedBreaches", {})
                    breaches_details = exposed_breaches.get("breaches_details", [])
                    return breaches_details
                
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Gagal menghubungi database kebocoran data."
                )
                
            except httpx.RequestError:
                # Menutupi stack trace jaringan agar aman
                raise HTTPException(
                    status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                    detail="Batas waktu koneksi ke database kebocoran habis."
                )

xon_service = XposedOrNotService()

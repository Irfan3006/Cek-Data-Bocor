from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List

class EmailCheckRequest(BaseModel):
    email: EmailStr

class BreachDetail(BaseModel):
    breach: str = Field(..., description="Nama layanan yang bocor")
    details: str = Field(..., description="Deskripsi detail mengenai kejadian kebocoran")
    domain: str = Field(..., description="Domain layanan yang bocor")
    industry: str = Field(..., description="Kategori industri layanan")
    logo: str = Field(..., description="URL logo layanan")
    breach_date: Optional[str] = Field(None, description="Tanggal kebocoran terjadi (Format YYYY-MM-DD)")
    records: int = Field(..., description="Jumlah akun/data yang bocor")
    password_risk: Optional[str] = Field(None, description="Tingkat risiko sandi")
    xposed_data: str = Field(..., description="Daftar jenis data yang bocor (pemisah koma)")

class RiskBreakdown(BaseModel):
    breaches_count: int = Field(..., description="Jumlah total kebocoran yang ditemukan")
    has_password: bool = Field(..., description="Apakah kata sandi ikut bocor")
    has_phone: bool = Field(..., description="Apakah nomor telepon ikut bocor")
    has_username: bool = Field(..., description="Apakah username ikut bocor")
    is_recent: bool = Field(..., description="Apakah ada kebocoran yang baru (dalam 2 tahun terakhir)")
    is_critical: bool = Field(..., description="Apakah terdapat tingkat keparahan tinggi (e.g. password_risk tinggi)")

class RiskAssessment(BaseModel):
    score: int = Field(..., description="Skor risiko dari 0 hingga 100")
    rating: str = Field(..., description="Tingkat risiko (Aman, Rendah, Sedang, Tinggi, Kritis)")
    breakdown: RiskBreakdown

class Recommendation(BaseModel):
    priority: str = Field(..., description="Prioritas rekomendasi (Tinggi, Sedang, Rendah)")
    title: str = Field(..., description="Judul rekomendasi tindakan")
    description: str = Field(..., description="Penjelasan rekomendasi")
    action_steps: List[str] = Field(..., description="Langkah-langkah taktis mitigasi")

class CheckResponse(BaseModel):
    email: str = Field(..., description="Email yang diperiksa")
    is_breached: bool = Field(..., description="Apakah email tersebut pernah bocor")
    status: str = Field(..., description="Status hasil pemeriksaan ('success' atau 'clean')")
    breaches_count: int = Field(..., description="Jumlah kebocoran")
    breaches: List[BreachDetail] = Field(default_factory=list, description="Daftar kebocoran data")
    risk_assessment: RiskAssessment
    recommendations: List[Recommendation] = Field(default_factory=list, description="Rekomendasi pencegahan pintar")
    cached: bool = Field(..., description="Apakah hasil ini diambil dari cache")
    timestamp: float = Field(..., description="Epoch timestamp saat pemeriksaan dilakukan")

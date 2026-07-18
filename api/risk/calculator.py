import re
from typing import Optional
from api.schemas.check import RiskAssessment, RiskBreakdown

class RiskCalculator:
    CURRENT_YEAR = 2026

    def _extract_year(self, date_str: Optional[str]) -> Optional[int]:
        """Ekstrak tahun dari string tanggal kebocoran (format YYYY-MM-DD atau teks bebas)."""
        if not date_str:
            return None
        match = re.search(r"\b(19\d\d|20\d\d)\b", date_str)
        if match:
            return int(match.group(1))
        return None

    def calculate_risk(self, breaches: list[dict]) -> RiskAssessment:
        """
        Kalkulasi skor risiko keamanan berdasarkan data kebocoran (0-100).
        """
        if not breaches:
            return RiskAssessment(
                score=0,
                rating="Aman",
                breakdown=RiskBreakdown(
                    breaches_count=0,
                    has_password=False,
                    has_phone=False,
                    has_username=False,
                    is_recent=False,
                    is_critical=False
                )
            )

        has_password = False
        has_phone = False
        has_username = False
        is_recent = False
        is_medium_recent = False
        is_critical = False
        has_high_volume = False

        for b in breaches:
            xposed_data_lower = b.get("xposed_data", "").lower()
            if "password" in xposed_data_lower or "sandi" in xposed_data_lower:
                has_password = True
            if "phone" in xposed_data_lower or "mobile" in xposed_data_lower or "telepon" in xposed_data_lower:
                has_phone = True
            if "username" in xposed_data_lower:
                has_username = True

            year = self._extract_year(b.get("xposed_date"))
            if year:
                # Baru: dalam 2 tahun terakhir (2024-2026)
                if self.CURRENT_YEAR - year <= 2:
                    is_recent = True
                # Sedang: dalam 5 tahun terakhir (2021-2023)
                elif self.CURRENT_YEAR - year <= 5:
                    is_medium_recent = True

            pwd_risk = b.get("password_risk", "").lower() if b.get("password_risk") else ""
            if pwd_risk in ("high", "plaintext", "unsafe"):
                is_critical = True

            raw_records = b.get("xposed_records", 0)
            try:
                records = int(raw_records)
            except (ValueError, TypeError):
                records = 0
            if records > 10_000_000:
                has_high_volume = True

        # Perhitungan Skor Berdasarkan Faktor (Maksimal 100)
        # 1. Faktor Jumlah Kebocoran (Maksimal 40 poin)
        breach_points = min(40, len(breaches) * 8)

        # 2. Faktor Jenis Data Bocor (Maksimal 40 poin)
        data_points = 0
        if has_password:
            data_points += 30
        if has_phone:
            data_points += 15
        if has_username:
            data_points += 10
        data_points = min(40, data_points)

        # 3. Faktor Recency (Maksimal 15 poin)
        recency_points = 0
        if is_recent:
            recency_points = 15
        elif is_medium_recent:
            recency_points = 8

        # 4. Faktor Severity / Kerentanan Ekstra (Maksimal 15 poin)
        severity_points = 0
        if is_critical:
            severity_points += 10
        if has_high_volume:
            severity_points += 5

        score = breach_points + data_points + recency_points + severity_points
        score = min(100, max(0, score))

        if score <= 25:
            rating = "Rendah"
        elif score <= 50:
            rating = "Sedang"
        elif score <= 75:
            rating = "Tinggi"
        else:
            rating = "Kritis"

        return RiskAssessment(
            score=score,
            rating=rating,
            breakdown=RiskBreakdown(
                breaches_count=len(breaches),
                has_password=has_password,
                has_phone=has_phone,
                has_username=has_username,
                is_recent=is_recent,
                is_critical=is_critical
            )
        )

risk_calculator = RiskCalculator()

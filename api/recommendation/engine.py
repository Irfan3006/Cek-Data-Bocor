import re
from typing import List, Optional
from api.schemas.check import Recommendation

class RecommendationEngine:
    CURRENT_YEAR = 2026

    def _extract_year(self, date_str: Optional[str]) -> Optional[int]:
        """Ekstrak tahun dari string tanggal kebocoran."""
        if not date_str:
            return None
        match = re.search(r"\b(19\d\d|20\d\d)\b", date_str)
        if match:
            return int(match.group(1))
        return None

    def generate_recommendations(self, breaches: list[dict]) -> List[Recommendation]:
        """
        Menghasilkan rekomendasi keamanan berbasis aturan.
        """
        recommendations: List[Recommendation] = []
        
        if not breaches:
            # Jika tidak ada kebocoran sama sekali
            recommendations.append(
                Recommendation(
                    priority="Rendah",
                    title="Pertahankan Keamanan Akun",
                    description="Email Anda tidak ditemukan dalam database kebocoran. Tetap jaga kerahasiaan data Anda dengan praktik keamanan dasar.",
                    action_steps=[
                        "Gunakan kata sandi unik (minimal 12 karakter) untuk setiap layanan digital.",
                        "Selalu aktifkan Autentikasi Dua Faktor (2FA) di platform media sosial dan email utama.",
                        "Hati-hati terhadap email mencurigakan yang meminta verifikasi data pribadi (phishing)."
                    ]
                )
            )
            return recommendations

        breach_count = len(breaches)
        has_password = False
        has_phone = False
        has_username = False
        has_new_breach = False
        old_breach_count = 0

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
                if self.CURRENT_YEAR - year <= 2:
                    has_new_breach = True
                elif self.CURRENT_YEAR - year >= 5:
                    old_breach_count += 1

        # Pemetaan Rekomendasi Berdasarkan Aturan
        
        if has_password:
            recommendations.append(
                Recommendation(
                    priority="Tinggi",
                    title="Ganti Kata Sandi Segera",
                    description="Kata sandi Anda terdeteksi bocor dalam database kebocoran data. Ini adalah ancaman paling berbahaya karena peretas dapat langsung mengambil alih akun Anda.",
                    action_steps=[
                        "Segera ubah kata sandi pada layanan terkait yang mengalami kebocoran.",
                        "Ganti kata sandi di akun lain yang masih menggunakan kata sandi yang sama.",
                        "Aktifkan autentikasi dua faktor (2FA) di seluruh layanan penting Anda."
                    ]
                )
            )

        if has_new_breach:
            recommendations.append(
                Recommendation(
                    priority="Tinggi",
                    title="Amankan Kebocoran Baru",
                    description="Email Anda terdeteksi dalam kebocoran data yang baru terjadi (dalam 2 tahun terakhir). Tindakan cepat sangat krusial sebelum data Anda disalahgunakan secara aktif.",
                    action_steps=[
                        "Ubah password akun yang baru bocor menggunakan kombinasi karakter acak yang kuat.",
                        "Periksa riwayat aktivitas login terbaru untuk mendeteksi akses mencurigakan yang tidak Anda kenal.",
                        "Gunakan Password Manager untuk mengelola kredensial unik pada setiap situs."
                    ]
                )
            )

        if has_phone:
            recommendations.append(
                Recommendation(
                    priority="Sedang",
                    title="Waspadai Upaya Phishing & Spam",
                    description="Nomor telepon Anda terkompromi. Anda berisiko tinggi menjadi target penipuan, panggilan spam, atau pembajakan akun melalui SMS/WhatsApp (phishing).",
                    action_steps=[
                        "Abaikan pesan teks atau telepon mencurigakan yang meminta kode OTP, PIN, atau informasi perbankan.",
                        "Gunakan aplikasi pendeteksi spam panggilan (seperti Getcontact) untuk menyaring nomor asing.",
                        "Jangan pernah mengklik tautan tidak dikenal yang dikirim melalui SMS atau WhatsApp."
                    ]
                )
            )

        if has_username:
            recommendations.append(
                Recommendation(
                    priority="Sedang",
                    title="Amankan Akun dengan Username Sejenis",
                    description="Nama pengguna (username) Anda terekspos. Peretas sering kali melakukan 'Credential Stuffing' dengan mencocokkan username ini di platform sosial media lainnya.",
                    action_steps=[
                        "Ganti kata sandi akun lain yang memiliki nama pengguna (username) serupa.",
                        "Gunakan nama pengguna atau variasi nama yang unik untuk pendaftaran akun digital baru.",
                        "Terapkan verifikasi keamanan ganda di akun-akun media sosial Anda."
                    ]
                )
            )

        if old_breach_count >= 3:
            recommendations.append(
                Recommendation(
                    priority="Sedang",
                    title="Audit Keamanan Akun Lama",
                    description="Email Anda memiliki riwayat kebocoran data yang cukup lama dari tahun-tahun sebelumnya. Akun-akun lawas yang sudah terlupakan berpotensi disusupi.",
                    action_steps=[
                        "Lakukan penutupan atau penghapusan permanen pada akun di situs web lama yang sudah tidak Anda gunakan.",
                        "Audit password di seluruh akun digital Anda untuk memastikan tidak ada pengulangan password lama.",
                        "Pastikan email pemulihan pada akun penting Anda masih aktif dan aman."
                    ]
                )
            )

        # Rule 6: Rekomendasi Berdasarkan Jumlah Breach (Level Rendah/Sedang/Tinggi)
        if breach_count <= 2:
            recommendations.append(
                Recommendation(
                    priority="Rendah",
                    title="Tingkatkan Proteksi Dasar",
                    description="Tingkat keterpaparan email Anda relatif rendah. Cukup lakukan langkah proteksi berkala agar tetap aman.",
                    action_steps=[
                        "Lakukan pemeriksaan berkala minimal 3 bulan sekali menggunakan layanan cek kebocoran.",
                        "Hindari mendaftarkan email utama pada situs web yang tidak tepercaya."
                    ]
                )
            )
        elif 3 <= breach_count <= 5:
            recommendations.append(
                Recommendation(
                    priority="Sedang",
                    title="Tinjau Keamanan Akun Anda",
                    description="Kebocoran email Anda tergolong sedang. Beberapa data penting Anda berpotensi besar sudah ada di tangan pihak tidak bertanggung jawab.",
                    action_steps=[
                        "Segera periksa daftar detail layanan yang bocor di bawah dan pastikan kata sandinya telah diganti.",
                        "Hapus data profil sensitif (seperti KTP, alamat rumah, nomor rekening) dari platform yang tidak lagi aktif digunakan."
                    ]
                )
            )
        else: # breach_count > 5
            recommendations.append(
                Recommendation(
                    priority="Tinggi",
                    title="Lakukan Pengamanan Menyeluruh",
                    description="Peringatan: Tingkat keterpaparan email Anda sangat tinggi. Email ini terdeteksi di banyak database ilegal. Risiko penyalahgunaan identitas digital Anda sangat besar.",
                    action_steps=[
                        "Ubah kata sandi utama akun email ini dan aktifkan Autentikasi Dua Faktor (2FA) dengan aplikasi authenticator (Google Authenticator/Microsoft Authenticator) daripada SMS.",
                        "Pertimbangkan untuk migrasi data penting ke email baru yang bersih dan gunakan email ini hanya untuk keperluan tidak penting."
                    ]
                )
            )

        priority_map = {"Tinggi": 0, "Sedang": 1, "Rendah": 2}
        recommendations.sort(key=lambda x: priority_map.get(x.priority, 2))

        return recommendations

recommendation_engine = RecommendationEngine()

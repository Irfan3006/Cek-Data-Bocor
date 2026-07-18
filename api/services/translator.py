import asyncio
import hashlib
import logging
import re
import threading
from typing import Optional

from deep_translator import GoogleTranslator

logger = logging.getLogger(__name__)

POST_TRANSLATION_FIXES: list[tuple[str, str]] = [
    # Data breach terminology
    ("pelanggaran data", "kebocoran data"),
    ("pelanggaran", "kebocoran"),
    ("dilanggar", "mengalami kebocoran"),
    ("pelanggaran keamanan", "insiden keamanan"),

    # Password / hashing
    ("kata sandi yang di-hash dengan garam", "kata sandi terenkripsi (salted hash)"),
    ("kata sandi yang di-hash", "kata sandi terenkripsi"),
    ("kata sandi hash", "kata sandi terenkripsi"),
    ("kata sandi asin", "kata sandi terenkripsi (salted)"),
    ("di-hash dengan garam", "terenkripsi (salted hash)"),
    ("hash asin", "salted hash"),
    ("garam hash", "salted hash"),
    ("hash bcrypt", "hash bcrypt"),
    ("teks biasa", "teks polos (plaintext)"),
    ("teks polos", "teks polos (plaintext)"),

    # Common tech terms that shouldn't be translated
    ("surel", "email"),
    ("Surel", "Email"),
    ("nama pengguna", "username"),
    ("Nama pengguna", "Username"),
    ("catatan pengguna", "data pengguna"),
    ("catatan", "data"),

    # Forum / dark web
    ("forum peretasan", "forum peretas"),
    ("web gelap", "dark web"),
    ("pasar gelap", "dark web"),

    # Security concepts
    ("isian kredensial", "credential stuffing"),
    ("pengisian kredensial", "credential stuffing"),
    ("kredensial", "kredensial"),
    ("otentikasi dua faktor", "autentikasi dua faktor (2FA)"),
    ("autentikasi multi-faktor", "autentikasi multi-faktor (MFA)"),
    ("pengambilalihan akun", "pembajakan akun"),

    # Misc
    ("bocor di alam liar", "bocor ke publik"),
    ("di alam liar", "ke publik"),
    ("Aktor ancaman", "Pelaku serangan"),
    ("aktor ancaman", "pelaku serangan"),
    ("pelaku ancaman", "pelaku serangan"),
    ("pengikisan data", "scraping data"),
    ("mengikis", "scraping"),
    ("Perangkat lunak perusak", "Malware"),
    ("perangkat lunak perusak", "malware"),
    ("pengelabuan", "phishing"),
    ("Pengelabuan", "Phishing"),
]


class TranslatorService:
    """
    Service terjemahan otomatis EN → ID menggunakan Google Translate (gratis).
    Dilengkapi cache memori dan koreksi istilah teknis pasca-terjemahan.
    """

    def __init__(self) -> None:
        self._cache: dict[str, str] = {}
        self._lock = threading.Lock()

    def _cache_key(self, text: str) -> str:
        """Buat hash pendek dari teks untuk key cache."""
        return hashlib.md5(text.strip().encode("utf-8")).hexdigest()

    def _post_process(self, text: str) -> str:
        """Perbaiki istilah teknis yang salah diterjemahkan oleh Google Translate."""
        result = text
        for wrong, correct in POST_TRANSLATION_FIXES:
            # Case-insensitive replacement, pertahankan case jika cocok
            result = re.sub(re.escape(wrong), correct, result, flags=re.IGNORECASE)
        return result

    def _translate_sync(self, text: str) -> str:
        """Terjemahkan teks secara sinkron (dipanggil di thread pool)."""
        if not text or not text.strip():
            return text

        key = self._cache_key(text)

        with self._lock:
            if key in self._cache:
                return self._cache[key]

        try:
            translator = GoogleTranslator(source="en", target="id")
            result = translator.translate(text)
            if result and result.strip():
                result = self._post_process(result)
                with self._lock:
                    self._cache[key] = result
                return result
        except Exception as e:
            logger.warning(f"Gagal menerjemahkan teks: {e}")

        return text

    async def translate(self, text: str) -> str:
        """Terjemahkan teks secara asinkron (non-blocking)."""
        if not text or not text.strip():
            return text

        key = self._cache_key(text)
        with self._lock:
            if key in self._cache:
                return self._cache[key]

        # Jalankan di thread pool agar tidak memblokir event loop
        return await asyncio.to_thread(self._translate_sync, text)

    async def translate_batch(self, texts: list[str]) -> list[str]:
        """
        Terjemahkan daftar teks secara batch untuk optimalisasi performa.
        Memanfaatkan cache untuk teks yang sudah pernah diterjemahkan.
        Teks yang belum ada di cache akan digabung dan diterjemahkan dalam satu request.
        """
        if not texts:
            return []

        results = [None] * len(texts)
        uncached_indices = []
        uncached_texts = []

        for i, text in enumerate(texts):
            if not text or not text.strip():
                results[i] = text
                continue
            
            key = self._cache_key(text)
            with self._lock:
                if key in self._cache:
                    results[i] = self._cache[key]
                    continue
            
            uncached_indices.append(i)
            uncached_texts.append(text.strip())

        if not uncached_texts:
            return results

        delimiter = " ||| "
        joined_text = delimiter.join(uncached_texts)
        
        try:
            translated_joined = await self.translate(joined_text)
            
            parts = re.split(r'\s*\|\|\|\s*', translated_joined)
            
            if len(parts) == len(uncached_texts):
                for idx, part_text in zip(uncached_indices, parts):
                    part_clean = part_text.strip()
                    results[idx] = part_clean
                    
                    orig_text = uncached_texts[uncached_indices.index(idx)]
                    key = self._cache_key(orig_text)
                    with self._lock:
                        self._cache[key] = part_clean
                return results
            else:
                logger.warning(
                    f"Jumlah bagian terjemahan batch tidak sesuai ({len(parts)} vs {len(uncached_texts)}). "
                    "Menggunakan fallback terjemahan individual."
                )
        except Exception as e:
            logger.warning(f"Gagal melakukan terjemahan batch: {e}. Menggunakan fallback.")

        fallback_tasks = [self.translate(text) for text in uncached_texts]
        fallback_results = await asyncio.gather(*fallback_tasks)
        
        for idx, translated_text in zip(uncached_indices, fallback_results):
            results[idx] = translated_text
            
        return results

translator_service = TranslatorService()

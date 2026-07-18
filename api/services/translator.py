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
        Membagi daftar teks ke dalam beberapa chunk dengan batasan maksimal karakter
        dan membatasi request konkruen menggunakan Semaphore untuk menghindari rate-limit Google.
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

        max_chars = 4000
        delimiter = " ||| "
        chunks = []
        current_chunk = []
        current_length = 0

        for idx, text in zip(uncached_indices, uncached_texts):
            text_len = len(text)
            if current_length + text_len + len(delimiter) > max_chars and current_chunk:
                chunks.append(current_chunk)
                current_chunk = []
                current_length = 0
            current_chunk.append((idx, text))
            current_length += text_len + len(delimiter)

        if current_chunk:
            chunks.append(current_chunk)

        sem = asyncio.Semaphore(3)

        async def translate_chunk(chunk) -> list[tuple[int, str]]:
            chunk_indices = [item[0] for item in chunk]
            chunk_texts = [item[1] for item in chunk]
            chunk_joined = delimiter.join(chunk_texts)
            
            async with sem:
                try:
                    translated_joined = await self.translate(chunk_joined)
                    parts = re.split(r'\s*\|\|\|\s*', translated_joined)
                    
                    if len(parts) == len(chunk_texts):
                        chunk_results = []
                        for idx, part_text, orig_text in zip(chunk_indices, parts, chunk_texts):
                            part_clean = part_text.strip()
                            key = self._cache_key(orig_text)
                            with self._lock:
                                self._cache[key] = part_clean
                            chunk_results.append((idx, part_clean))
                        return chunk_results
                except Exception as e:
                    logger.warning(f"Gagal menerjemahkan chunk batch: {e}. Menggunakan fallback.")

            chunk_results = []
            for idx, orig_text in chunk:
                async with sem:
                    try:
                        translated_text = await self.translate(orig_text)
                        key = self._cache_key(orig_text)
                        with self._lock:
                            self._cache[key] = translated_text
                        chunk_results.append((idx, translated_text))
                    except Exception:
                        chunk_results.append((idx, orig_text))
            return chunk_results

        tasks = [translate_chunk(chunk) for chunk in chunks]
        chunks_results = await asyncio.gather(*tasks)

        for chunk_res in chunks_results:
            for idx, translated_text in chunk_res:
                results[idx] = translated_text

        return results

translator_service = TranslatorService()

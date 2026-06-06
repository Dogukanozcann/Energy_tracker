"""
Email servisi: token yönetimi ve e-posta gönderimi.
SMTP ayarları yoksa sadece token üretir (geliştirme modu).
"""

import secrets
from datetime import datetime, timedelta, timezone

from app.core.config import settings


class EmailService:
    """Token üretimi, doğrulama ve e-posta gönderme."""

    @staticmethod
    def generate_token() -> str:
        """Kriptografik olarak güvenli rastgele token üretir."""
        return secrets.token_urlsafe(48)

    @staticmethod
    def generate_reset_expiry() -> datetime:
        """Reset token son kullanma zamanı (1 saat)."""
        return datetime.now(timezone.utc) + timedelta(hours=1)

    @staticmethod
    async def send_verification_email(email: str, token: str) -> None:
        """E-posta doğrulama bağlantısı gönderir.
        SMTP yoksa sadece log atar (token endpoint'ten okunabilir).
        """
        if settings.SMTP_HOST:
            # TODO: Gerçek SMTP entegrasyonu
            pass
        # Geliştirme ortamında token bilgisi için log
        print(f"[EMAIL] Verification token for {email}: {token}")
        print(f"[EMAIL] Verify URL: http://localhost:3000/verify-email?token={token}")

    @staticmethod
    async def send_reset_password_email(email: str, token: str) -> None:
        """Şifre sıfırlama bağlantısı gönderir."""
        if settings.SMTP_HOST:
            # TODO: Gerçek SMTP entegrasyonu
            pass
        print(f"[EMAIL] Reset token for {email}: {token}")
        print(f"[EMAIL] Reset URL: http://localhost:3000/reset-password?token={token}")

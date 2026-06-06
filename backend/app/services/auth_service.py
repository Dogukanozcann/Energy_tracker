from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password, create_access_token
from app.models.user import User
from app.schemas.auth import RegisterRequest
from app.services.email_service import EmailService


class AuthService:
    """Kullanıcı kaydı, girişi ve token yönetimi."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(self, data: RegisterRequest) -> User:
        """Yeni kullanıcı oluşturur. Email varsa 409 hatası döner."""

        existing = await self.db.execute(
            select(User).where(User.email == data.email)
        )
        if existing.scalar_one_or_none():
            raise ValueError("Bu email adresi zaten kayıtlı.")

        token = EmailService.generate_token()
        user = User(
            email=data.email,
            password_hash=hash_password(data.password),
            full_name=data.full_name,
            company_name=data.company_name,
            user_type=data.user_type,
            verification_token=token,
        )
        self.db.add(user)
        await self.db.flush()

        await EmailService.send_verification_email(data.email, token)
        return user

    async def authenticate(self, email: str, password: str) -> User:
        """Email + şifre doğrulaması. Başarısız → ValueError."""

        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if user is None or not verify_password(password, user.password_hash):
            raise ValueError("Email veya şifre hatalı.")

        if not user.is_active:
            raise ValueError("Hesabınız devre dışı bırakılmış.")

        return user

    async def verify_email(self, token: str) -> User:
        """Email doğrulama token'ını kontrol eder."""
        result = await self.db.execute(
            select(User).where(User.verification_token == token)
        )
        user = result.scalar_one_or_none()
        if user is None:
            raise ValueError("Geçersiz doğrulama token'ı.")
        if user.email_verified_at:
            raise ValueError("Email zaten doğrulanmış.")

        user.email_verified_at = datetime.now(timezone.utc)
        user.verification_token = None
        await self.db.flush()
        return user

    async def forgot_password(self, email: str) -> str | None:
        """Şifre sıfırlama token'ı oluşturur ve email gönderir.
        Email yoksa hata fırlatmaz (güvenlik için).
        """
        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if user is None:
            return None

        token = EmailService.generate_token()
        user.reset_token = token
        user.reset_token_expires = EmailService.generate_reset_expiry()
        await self.db.flush()

        await EmailService.send_reset_password_email(email, token)
        return token

    async def reset_password(self, token: str, new_password: str) -> User:
        """Token ile şifre sıfırlama."""
        result = await self.db.execute(
            select(User).where(User.reset_token == token)
        )
        user = result.scalar_one_or_none()
        if user is None:
            raise ValueError("Geçersiz sıfırlama token'ı.")

        if user.reset_token_expires and user.reset_token_expires < datetime.now(timezone.utc):
            raise ValueError("Token'ın süresi dolmuş.")

        user.password_hash = hash_password(new_password)
        user.reset_token = None
        user.reset_token_expires = None
        await self.db.flush()
        return user

    @staticmethod
    def issue_token(user: User) -> str:
        """Kullanıcı ID'si ile JWT token üretir."""
        return create_access_token(subject=str(user.id))

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from passlib.context import CryptContext
from app.database import get_db
from app.auth import create_access_token

router = APIRouter(prefix="/admin", tags=["Admin"])

pwd_context = CryptContext(schemes=["bcrypt_sha256"], deprecated="auto")


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/login")
def admin_login(data: LoginRequest):
    db = get_db()
    admins = db["admins"]

    admin = admins.find_one({"email": data.email})

    if not admin:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not pwd_context.verify(data.password, admin["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({
        "email": admin["email"],
        "organization": admin["organization"]
    })

    return {
        "access_token": token,
        "token_type": "bearer"
    }

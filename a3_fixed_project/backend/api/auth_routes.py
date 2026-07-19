from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from datetime import datetime, timedelta
import jwt
import hashlib
import logging
from config import settings
from database import get_db
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(plain: str, hashed: str) -> bool:
    return hash_password(plain) == hashed


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    to_encode.update({"exp": datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


class LoginRequest(BaseModel):
    username: str
    password: str
    role: str = "student"
    education_level: str | None = None
    grade: str | None = None


class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    role: str = "student"
    education_level: str = "high_school"
    grade: str = ""


@router.post("/login")
async def login(req: LoginRequest, db: Session = Depends(get_db)):
    from models.database_models import Student, StudentProfile

    user = db.query(Student).filter(Student.username == req.username).first()

    is_demo = (req.username == "demo" and req.password == "demo123")

    if not user and not is_demo:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    if user and not is_demo:
        if user.password_hash != hash_password(req.password):
            raise HTTPException(status_code=401, detail="用户名或密码错误")

    sid = str(user.id if user else 1)

    if user and req.role and user.role != req.role:
        user.role = req.role
        db.commit()

    if user and req.education_level:
        profile = db.query(StudentProfile).filter(StudentProfile.student_id == user.id).first()
        if not profile:
            profile = StudentProfile(
                student_id=user.id,
                education_level=req.education_level,
                grade=req.grade or "",
                subjects=[],
                weak_points=[],
            )
            db.add(profile)
        else:
            if req.education_level:
                profile.education_level = req.education_level
            if req.grade:
                profile.grade = req.grade
        db.commit()

    token = create_access_token({
        "sub": req.username,
        "student_id": sid,
        "role": req.role,
        "education_level": req.education_level or "",
    })

    return {
        "status": "success",
        "token": token,
        "username": req.username,
        "student_id": sid,
        "role": req.role,
        "education_level": req.education_level or "",
    }


@router.post("/register")
async def register(req: RegisterRequest, db: Session = Depends(get_db)):
    from models.database_models import Student, StudentProfile

    existing = db.query(Student).filter(Student.username == req.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")

    try:
        user = Student(
            username=req.username,
            password_hash=hash_password(req.password),
            role=req.role,
        )
        db.add(user)
        db.flush()

        profile = StudentProfile(
            student_id=user.id,
            education_level=req.education_level,
            grade=req.grade or "",
            subjects=[],
            weak_points=[],
        )
        db.add(profile)
        db.commit()
        db.refresh(user)

        token = create_access_token({
            "sub": req.username,
            "student_id": str(user.id),
            "role": req.role,
            "education_level": req.education_level,
        })

        return {
            "status": "success",
            "message": "注册成功",
            "token": token,
            "username": req.username,
            "student_id": str(user.id),
            "role": req.role,
            "education_level": req.education_level,
        }
    except Exception as e:
        db.rollback()
        logger.error(f"register error: {e}")
        raise HTTPException(status_code=500, detail=f"注册失败: {e}")


@router.post("/set-education")
async def set_education(
    student_id: str,
    education_level: str,
    grade: str = "",
    role: str = "student",
    db: Session = Depends(get_db)
):
    from models.database_models import Student, StudentProfile
    try:
        sid_int = int(student_id)
    except Exception:
        sid_int = None

    if sid_int is None:
        return {"status": "error", "detail": "无效学生ID"}

    student = db.query(Student).filter(Student.id == sid_int).first()
    if not student:
        return {"status": "error", "detail": "用户不存在"}

    if role:
        student.role = role
    db.commit()

    profile = db.query(StudentProfile).filter(StudentProfile.student_id == sid_int).first()
    if not profile:
        profile = StudentProfile(
            student_id=sid_int,
            education_level=education_level,
            grade=grade,
            subjects=[],
            weak_points=[],
        )
        db.add(profile)
    else:
        profile.education_level = education_level
        if grade:
            profile.grade = grade
    db.commit()

    return {
        "status": "success",
        "student_id": student_id,
        "role": role,
        "education_level": education_level,
        "grade": grade,
    }


@router.get("/verify")
async def verify_token(token: str):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return {"status": "success", "valid": True, "payload": payload}
    except jwt.ExpiredSignatureError:
        return {"status": "success", "valid": False, "message": "Token已过期"}
    except jwt.InvalidTokenError:
        return {"status": "success", "valid": False, "message": "无效的Token"}

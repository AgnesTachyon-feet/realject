from sqlalchemy.orm import Session
from tables.families import Family, FamilyMember
from tables.users import Users, RoleEnum
import secrets

def generate_unique_code(db: Session) -> str:
    while True:
        code = f"FAM-{secrets.token_hex(3).upper()}"
        exists = db.query(Family).filter(Family.code == code).first()
        if not exists:
            return code

def create_family(db: Session, parent_id: int, family_name: str) -> Family:
    code = generate_unique_code(db)
    fam = Family(name=family_name, code=code, owner_parent_id=parent_id)
    db.add(fam); db.commit(); db.refresh(fam)
    # ใส่ parent เป็นสมาชิกด้วย
    db.add(FamilyMember(family_id=fam.id, user_id=parent_id, role=RoleEnum.parent.value))
    db.commit()
    return fam

def join_family(db: Session, kid_id: int, code: str):
    code = code.strip().upper()
    fam = db.query(Family).filter(Family.code == code).first()
    if not fam:
        raise ValueError("Invalid family code")
    kid = db.get(Users, kid_id)
    if not kid or getattr(kid.role, "value", str(kid.role)) != "kid":
        raise ValueError("Invalid user")
    exists = db.query(FamilyMember).filter(FamilyMember.user_id == kid_id, FamilyMember.family_id == fam.id).first()
    if exists:
        raise ValueError("Already joined")
    db.add(FamilyMember(family_id=fam.id, user_id=kid_id, role=RoleEnum.kid.value))
    db.commit()

def is_same_family(db: Session, parent_id: int, kid_id: int) -> bool:
    fam_ids = [fm.family_id for fm in db.query(FamilyMember).filter(FamilyMember.user_id == parent_id).all()]
    if not fam_ids:
        return False
    return db.query(FamilyMember).filter(
        FamilyMember.user_id == kid_id,
        FamilyMember.family_id.in_(fam_ids)
    ).first() is not None
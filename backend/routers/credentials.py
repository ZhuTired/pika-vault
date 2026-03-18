from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.database import get_db
from backend.models import Credential
from backend.schemas import CredentialCreate, CredentialUpdate, CredentialResponse, CredentialField
from backend.crypto import is_vault_unlocked, encrypt_value, decrypt_value

router = APIRouter(
    prefix="/api/credentials",
    tags=["credentials"],
    responses={404: {"description": "Not found"}},
)

def check_vault_status():
    if not is_vault_unlocked():
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="Vault is locked. Please unlock first."
        )

@router.get("/", response_model=List[CredentialResponse])
def read_credentials(
    skip: int = 0,
    limit: int = 100,
    tag: Optional[str] = None,
    type: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    check_vault_status()
    query = db.query(Credential).filter(Credential.is_deleted == False)
    
    if type:
        query = query.filter(Credential.type == type)
    
    # Simple tag filtering - stored as JSON array
    # In SQLite/MySQL JSON handling might differ. For simplicity, we might fetch and filter in python if DB JSON support is tricky
    # But let's assume standard SQLAlchemy JSON handling.
    # For now, let's filter in Python for tags/search if needed or use basic LIKE for name
    if search:
        query = query.filter(Credential.name.ilike(f"%{search}%"))
        
    creds = query.offset(skip).limit(limit).all()
    
    # Decrypt sensitive fields
    results = []
    for cred in creds:
        decrypted_fields = []
        for field in cred.fields:
            # field is a dict
            f_data = field.copy()
            if f_data.get("is_sensitive"):
                try:
                    f_data["value"] = decrypt_value(f_data["value"])
                except:
                    f_data["value"] = "[Decryption Error]"
            decrypted_fields.append(CredentialField(**f_data))
        
        # We need to construct the response object manually or let Pydantic handle it
        # Pydantic expects objects with attributes. cred is an ORM object.
        # But we modified fields. We can't modify the ORM object directly safely without affecting session state potentially?
        # Actually, we can just return a dict or a new object.
        
        # Filter by tag in python if requested (since JSON array contains query is dialect specific)
        if tag and tag not in cred.tags:
            continue
            
        cred_dict = {
            "id": cred.id,
            "name": cred.name,
            "type": cred.type,
            "tags": cred.tags,
            "fields": decrypted_fields,
            "notes": cred.notes,
            "created_at": cred.created_at,
            "updated_at": cred.updated_at
        }
        results.append(cred_dict)
        
    return results

@router.post("/", response_model=CredentialResponse)
def create_credential(cred: CredentialCreate, db: Session = Depends(get_db)):
    check_vault_status()
    
    encrypted_fields = []
    for field in cred.fields:
        f_data = field.model_dump()
        if f_data["is_sensitive"]:
            f_data["value"] = encrypt_value(f_data["value"])
        encrypted_fields.append(f_data)
    
    db_cred = Credential(
        name=cred.name,
        type=cred.type,
        tags=cred.tags,
        fields=encrypted_fields,
        notes=cred.notes
    )
    db.add(db_cred)
    db.commit()
    db.refresh(db_cred)
    
    # Return with decrypted values (which are the input values)
    # But response model expects decrypted. Since we just encrypted it, we can return the input `cred` plus ID/timestamps
    # Or just construct response from DB object but decrypt fields again.
    # Let's decrypt from DB object to be consistent.
    
    response_fields = []
    for field in db_cred.fields:
        f_data = field.copy()
        if f_data.get("is_sensitive"):
            f_data["value"] = decrypt_value(f_data["value"])
        response_fields.append(CredentialField(**f_data))

    return {
        "id": db_cred.id,
        "name": db_cred.name,
        "type": db_cred.type,
        "tags": db_cred.tags,
        "fields": response_fields,
        "notes": db_cred.notes,
        "created_at": db_cred.created_at,
        "updated_at": db_cred.updated_at
    }

@router.put("/{cred_id}", response_model=CredentialResponse)
def update_credential(cred_id: int, cred: CredentialUpdate, db: Session = Depends(get_db)):
    check_vault_status()
    db_cred = db.query(Credential).filter(Credential.id == cred_id, Credential.is_deleted == False).first()
    if not db_cred:
        raise HTTPException(status_code=404, detail="Credential not found")
    
    if cred.name is not None:
        db_cred.name = cred.name
    if cred.type is not None:
        db_cred.type = cred.type
    if cred.tags is not None:
        db_cred.tags = cred.tags
    if cred.notes is not None:
        db_cred.notes = cred.notes
    
    if cred.fields is not None:
        encrypted_fields = []
        for field in cred.fields:
            f_data = field.model_dump()
            if f_data["is_sensitive"]:
                # If value is already encrypted? No, input is always plaintext from frontend
                f_data["value"] = encrypt_value(f_data["value"])
            encrypted_fields.append(f_data)
        db_cred.fields = encrypted_fields
    
    db.commit()
    db.refresh(db_cred)
    
    # Decrypt for response
    response_fields = []
    for field in db_cred.fields:
        f_data = field.copy()
        if f_data.get("is_sensitive"):
            f_data["value"] = decrypt_value(f_data["value"])
        response_fields.append(CredentialField(**f_data))
        
    return {
        "id": db_cred.id,
        "name": db_cred.name,
        "type": db_cred.type,
        "tags": db_cred.tags,
        "fields": response_fields,
        "notes": db_cred.notes,
        "created_at": db_cred.created_at,
        "updated_at": db_cred.updated_at
    }

@router.delete("/{cred_id}")
def delete_credential(cred_id: int, db: Session = Depends(get_db)):
    check_vault_status()
    db_cred = db.query(Credential).filter(Credential.id == cred_id).first()
    if not db_cred:
        raise HTTPException(status_code=404, detail="Credential not found")
    
    db_cred.is_deleted = True # Soft delete
    db.commit()
    return {"ok": True}

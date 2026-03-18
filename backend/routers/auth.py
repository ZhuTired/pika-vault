from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import SystemConfig
from backend.schemas import MasterPassword, VaultStatus
from backend.crypto import initialize_vault, unlock_vault, clear_encryption_key, is_vault_unlocked
from backend.init_data import populate_example_data

router = APIRouter(
    prefix="/api/vault",
    tags=["vault"],
)

@router.get("/status", response_model=VaultStatus)
def get_vault_status(db: Session = Depends(get_db)):
    # Check if initialized
    salt_entry = db.query(SystemConfig).filter(SystemConfig.key == "master_salt").first()
    is_initialized = salt_entry is not None
    return {
        "is_initialized": is_initialized,
        "is_unlocked": is_vault_unlocked()
    }

@router.post("/init")
def init_vault(data: MasterPassword, db: Session = Depends(get_db)):
    # Check if already initialized
    salt_entry = db.query(SystemConfig).filter(SystemConfig.key == "master_salt").first()
    if salt_entry:
        raise HTTPException(status_code=400, detail="Vault already initialized")
    
    initialize_vault(db, data.password)
    
    # Initialize example data after vault is initialized and key is available
    populate_example_data(db)
    
    return {"ok": True}

@router.post("/unlock")
def unlock(data: MasterPassword, db: Session = Depends(get_db)):
    success = unlock_vault(db, data.password)
    if not success:
        raise HTTPException(status_code=401, detail="Invalid password")
    return {"ok": True}

@router.post("/lock")
def lock():
    clear_encryption_key()
    return {"ok": True}

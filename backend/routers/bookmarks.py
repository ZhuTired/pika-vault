from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import requests
from urllib.parse import urlparse
from bs4 import BeautifulSoup

from backend.database import get_db
from backend.models import Bookmark
from backend.schemas import BookmarkCreate, BookmarkUpdate, BookmarkResponse, SortUpdate

router = APIRouter(
    prefix="/api/bookmarks",
    tags=["bookmarks"],
    responses={404: {"description": "Not found"}},
)

def fetch_metadata(url: str):
    try:
        if not url.startswith("http"):
            url = "https://" + url
        response = requests.get(url, timeout=5)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Title
        title = soup.title.string if soup.title else url
        
        # Favicon
        # Using Google s2 service as fallback or primary is easier
        domain = urlparse(url).netloc
        favicon_url = f"https://www.google.com/s2/favicons?domain={domain}&sz=64"
        
        return title.strip(), favicon_url
    except Exception:
        # Fallback
        return url, None

@router.get("/", response_model=List[BookmarkResponse])
def read_bookmarks(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    bookmarks = db.query(Bookmark).order_by(Bookmark.sort_order.desc(), Bookmark.created_at.desc()).offset(skip).limit(limit).all()
    return bookmarks

@router.post("/", response_model=BookmarkResponse)
def create_bookmark(bookmark: BookmarkCreate, db: Session = Depends(get_db)):
    title = bookmark.title
    favicon_url = bookmark.favicon_url
    
    # Auto-fetch if title is empty or favicon is needed (though Google S2 is URL based)
    # The requirement says: "Input URL (auto get Favicon and page Title)"
    # If frontend sends empty title, we fetch it.
    if not title or title == "New Bookmark":
        fetched_title, fetched_favicon = fetch_metadata(bookmark.url)
        if not title or title == "New Bookmark":
            title = fetched_title
        if not favicon_url:
            favicon_url = fetched_favicon
    
    if not favicon_url:
         domain = urlparse(bookmark.url if bookmark.url.startswith("http") else "https://" + bookmark.url).netloc
         favicon_url = f"https://www.google.com/s2/favicons?domain={domain}&sz=64"

    db_bookmark = Bookmark(
        title=title,
        url=bookmark.url,
        favicon_url=favicon_url,
        category=bookmark.category,
        description=bookmark.description,
        sort_order=bookmark.sort_order
    )
    db.add(db_bookmark)
    db.commit()
    db.refresh(db_bookmark)
    return db_bookmark

@router.put("/{bookmark_id}", response_model=BookmarkResponse)
def update_bookmark(bookmark_id: int, bookmark: BookmarkUpdate, db: Session = Depends(get_db)):
    db_bookmark = db.query(Bookmark).filter(Bookmark.id == bookmark_id).first()
    if not db_bookmark:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    
    update_data = bookmark.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_bookmark, key, value)
    
    db.commit()
    db.refresh(db_bookmark)
    return db_bookmark

@router.delete("/{bookmark_id}")
def delete_bookmark(bookmark_id: int, db: Session = Depends(get_db)):
    db_bookmark = db.query(Bookmark).filter(Bookmark.id == bookmark_id).first()
    if not db_bookmark:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    
    db.delete(db_bookmark)
    db.commit()
    return {"ok": True}

@router.post("/batch-sort")
def batch_update_sort(updates: List[SortUpdate], db: Session = Depends(get_db)):
    for update in updates:
        db.query(Bookmark).filter(Bookmark.id == update.id).update({"sort_order": update.sort_order})
    db.commit()
    return {"ok": True}

@router.post("/{bookmark_id}/fetch-favicon")
def fetch_bookmark_favicon(bookmark_id: int, db: Session = Depends(get_db)):
    db_bookmark = db.query(Bookmark).filter(Bookmark.id == bookmark_id).first()
    if not db_bookmark:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    
    _, fetched_favicon = fetch_metadata(db_bookmark.url)
    if fetched_favicon:
        db_bookmark.favicon_url = fetched_favicon
        db.commit()
        db.refresh(db_bookmark)
    return {"favicon_url": db_bookmark.favicon_url}

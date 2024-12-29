from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from typing import List, Optional
from models import Base, Author, Thesis, University, Institute, Language, Keyword, SubjectTopic, Supervisor, ThesisKeyword, ThesisSupervisor, ThesisTopic
from DTO import *
from sqlalchemy.exc import IntegrityError
from config import Config

app = FastAPI(title="Thesis API")

DATABASE_URL = Config.SQLALCHEMY_DATABASE_URI

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/authors/", response_model=AuthorResponse)
def create_author(author: AuthorCreate, db: Session = Depends(get_db)):
    db_author = Author(first_name=author.first_name, last_name=author.last_name)
    db.add(db_author)
    db.commit()
    db.refresh(db_author)
    return db_author

@app.get("/authors/", response_model=List[AuthorResponse])
def read_authors(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    authors = db.query(Author).offset(skip).limit(limit).all()
    return authors

@app.get("/authors/{author_id}", response_model=AuthorResponse)
def read_author(author_id: int, db: Session = Depends(get_db)):
    db_author = db.query(Author).filter(Author.author_id == author_id).first()
    if db_author is None:
        raise HTTPException(status_code=404, detail="Author not found")
    return db_author

@app.put("/authors/{author_id}", response_model=AuthorResponse)
def update_author(author_id: int, author: AuthorUpdate, db: Session = Depends(get_db)):
    db_author = db.query(Author).filter(Author.author_id == author_id).first()
    if db_author is None:
        raise HTTPException(status_code=404, detail="Author not found")
    
    if author.first_name is not None:
        db_author.first_name = author.first_name
    if author.last_name is not None:
        db_author.last_name = author.last_name
    
    db.commit()
    db.refresh(db_author)
    return db_author

@app.delete("/authors/{author_id}")
def delete_author(author_id: int, db: Session = Depends(get_db)):
    db_author = db.query(Author).filter(Author.author_id == author_id).first()
    if db_author is None:
        raise HTTPException(status_code=404, detail="Author not found")
    
    db.delete(db_author)
    db.commit()
    return {"message": "Author deleted successfully"}

@app.post("/institutes/", response_model=InstituteResponse)
def create_institute(institute: InstituteCreate, db: Session = Depends(get_db)):
    try:
        db_institute = Institute(
            name=institute.name,
            university_id=institute.university_id
        )
        db.add(db_institute)
        db.commit()
        db.refresh(db_institute)
        return db_institute
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Bu üniversite ID'si geçerli değil veya enstitü adı zaten mevcut"
        )

@app.get("/institutes/", response_model=List[InstituteResponse])
def get_institutes(
    skip: int = 0,
    limit: int = 100,
    name: Optional[str] = None,
    university_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Institute)
    
    if name:
        query = query.filter(Institute.name.ilike(f"%{name}%"))
    if university_id:
        query = query.filter(Institute.university_id == university_id)
    
    return query.offset(skip).limit(limit).all()

@app.get("/institutes/{institute_id}", response_model=InstituteResponse)
def get_institute(institute_id: int, db: Session = Depends(get_db)):
    institute = db.query(Institute).filter(Institute.institute_id == institute_id).first()
    if institute is None:
        raise HTTPException(status_code=404, detail="Enstitü bulunamadı")
    return institute

@app.put("/institutes/{institute_id}", response_model=InstituteResponse)
def update_institute(
    institute_id: int,
    institute_update: InstituteUpdate,
    db: Session = Depends(get_db)
):
    db_institute = db.query(Institute).filter(Institute.institute_id == institute_id).first()
    if db_institute is None:
        raise HTTPException(status_code=404, detail="Enstitü bulunamadı")

    try:
        update_data = institute_update.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_institute, key, value)
        
        db.commit()
        db.refresh(db_institute)
        return db_institute
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Güncelleme yapılamıyor. Üniversite ID'si geçerli değil veya enstitü adı zaten mevcut"
        )

@app.delete("/institutes/{institute_id}")
def delete_institute(institute_id: int, db: Session = Depends(get_db)):
    db_institute = db.query(Institute).filter(Institute.institute_id == institute_id).first()
    if db_institute is None:
        raise HTTPException(status_code=404, detail="Enstitü bulunamadı")
    
    try:
        db.delete(db_institute)
        db.commit()
        return {"message": f"{db_institute.name} enstitüsü başarıyla silindi"}
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Bu enstitü başka kayıtlarla ilişkili olduğu için silinemiyor"
        )

@app.get("/institutes/university/{university_id}", response_model=List[InstituteResponse])
def get_institutes_by_university(university_id: int, db: Session = Depends(get_db)):
    institutes = db.query(Institute).filter(Institute.university_id == university_id).all()
    if not institutes:
        raise HTTPException(
            status_code=404,
            detail=f"Bu üniversite ID'sine ({university_id}) ait enstitü bulunamadı"
        )
    return institutes

def init_db():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init_db()
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
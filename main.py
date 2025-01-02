from fastapi import FastAPI, HTTPException, Depends, Query
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from typing import List, Optional
from models import Base, Author, Thesis, University, Institute, Language, Keyword, SubjectTopic, Supervisor, ThesisKeyword, ThesisSupervisor, ThesisTopic
from DTO import *
from sqlalchemy.exc import IntegrityError
from config import Config
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Thesis API")

# CORS Middleware'i ekleyin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # İzin verilen origin'leri buraya yazabilirsiniz. Tüm origin'lere izin vermek için ["*"] kullanın.
    allow_credentials=True,
    allow_methods=["*"],  # İzin verilen HTTP metodları. Tüm metodlara izin vermek için ["*"] kullanın.
    allow_headers=["*"],  # İzin verilen başlıklar. Tüm başlıklara izin vermek için ["*"] kullanın.
)

DATABASE_URL = Config.SQLALCHEMY_DATABASE_URI

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
@app.get("/")
def read_root():
    return {"message": "Welcome to the Thesis API"}
        
@app.get("/theses/", response_model=List[ThesisResponseWithRelations])
def search_theses(
    thesis_no: Optional[int] = Query(None, description="Search by thesis ID"),
    title: Optional[str] = Query(None, description="Search by thesis title"),
    author_name: Optional[str] = Query(None, description="Search by author name"),
    keyword: Optional[str] = Query(None, description="Search by keyword"),
    topic: Optional[str] = Query(None, description="Search by topic"),
    year: Optional[int] = Query(None, description="Search by year"),
    type: Optional[str] = Query(None, description="Search by thesis type"),
    language: Optional[str] = Query(None, description="Search by thesis language"),
    university: Optional[str] = Query(None, description="Search by university name"),
    institute: Optional[str] = Query(None, description="Search by institute name"),
    db: Session = Depends(get_db),
):
    query = db.query(Thesis).join(Author).join(Language).join(Institute).join(University)
    query = query.outerjoin(Thesis.keywords).outerjoin(Thesis.topics)

    if title:
        query = query.filter(Thesis.title.ilike(f"%{title}%"))
    if author_name:
        query = query.filter(
            (Author.first_name.ilike(f"%{author_name}%")) | (Author.last_name.ilike(f"%{author_name}%"))
        )
    if keyword:
        query = query.filter(Keyword.keyword_name.ilike(f"%{keyword}%"))
    if topic:
        query = query.filter(SubjectTopic.topic_name.ilike(f"%{topic}%"))
    if year:
        query = query.filter(Thesis.year == year)
    if type:
        query = query.filter(Thesis.type.ilike(f"%{type}%"))
    if language:
        query = query.filter(Language.language_name.ilike(f"%{language}%"))
    if university:
        query = query.filter(University.name.ilike(f"%{university}%"))
    if institute:
        query = query.filter(Institute.name.ilike(f"%{institute}%"))
    if thesis_no:
        query = query.filter(Thesis.thesis_no == thesis_no)

    results = query.all()

    if not results:
        raise HTTPException(status_code=404, detail="No theses found matching the criteria")

    return results

@app.put("/update_thesis/{thesis_no}", response_model=ThesisResponseWithRelations) #veritabanında güncelleme olmuyor ama 200 dönüyor.
def update_thesis(thesis_no: int, thesis: ThesisUpdate, db: Session = Depends(get_db)):
    db_thesis = db.query(Thesis).filter(Thesis.thesis_no == thesis_no).first()

    if db_thesis is None:
        raise HTTPException(status_code=404, detail="Thesis not found")
    
    try:
        update_data = thesis.dict(exclude_unset=False)
        for key, value in update_data.items():
            if value is not None:
                setattr(db_thesis, key, value)
        db.commit()
        db.refresh(db_thesis)
        return db_thesis
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"Update failed. Please check the provided data. Error: {str(e)}"
        )

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
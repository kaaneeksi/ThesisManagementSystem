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

    results = query.order_by(Thesis.thesis_no).all()

    if not results:
        raise HTTPException(status_code=404, detail="No theses found matching the criteria")

    return results


@app.put("/update_thesis/{thesis_no}")
def update_thesis(thesis_no: int, thesis: ThesisUpdate, db: Session = Depends(get_db)):
    db_thesis = db.query(Thesis).filter(Thesis.thesis_no == thesis_no).first()
    if not db_thesis:
        raise HTTPException(status_code=404, detail="Thesis not found")

    try:
        update_data = thesis.dict(exclude_unset=True)
        
        if 'author' in update_data:
            author_data = update_data.pop('author')
            db.query(Author).filter(
                Author.author_id == db_thesis.author_id
            ).update(author_data)
        if 'language' in update_data:
            language_data = update_data.pop('language')
            db.query(Language).filter(
                Language.language_id == db_thesis.language_id
            ).update(language_data)
        if 'university' in update_data:
            university_data = update_data.pop('university')
            db.query(University).filter(
                University.university_id == db_thesis.university_id
            ).update(university_data)
        if 'institute' in update_data:
            institute_data = update_data.pop('institute')
            db.query(Institute).filter(
                Institute.institute_id == db_thesis.institute_id
            ).update(institute_data)
            
        for key, value in update_data.items():
            if value is not None:
                setattr(db_thesis, key, value)
        db.commit()
        db.refresh(db_thesis)
        return db_thesis

    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

#-----------------CRUD OPERATIONS-----------------#

@app.post("/theses/", response_model=ThesisResponse)
def create_new_thesis(thesis_data: ThesisCreate, db: Session = Depends(get_db)):
    thesis = Thesis(**thesis_data.dict())
    db.add(thesis)
    db.commit()
    db.refresh(thesis)
    return thesis

@app.put("/theses/{thesis_id}", response_model=ThesisResponse)
def update_thesis_endpoint(thesis_id: int, thesis_data: ThesisUpdate, db: Session = Depends(get_db)):
    thesis = db.query(Thesis).filter(Thesis.thesis_no == thesis_id).first()
    if not thesis:
        raise HTTPException(status_code=404, detail="Thesis not found")
    for key, value in thesis_data.dict(exclude_unset=True).items():
        setattr(thesis, key, value)
    db.commit()
    db.refresh(thesis)
    return thesis

@app.delete("/theses/{thesis_id}")
def delete_thesis_endpoint(thesis_id: int, db: Session = Depends(get_db)):
    thesis = db.query(Thesis).filter(Thesis.thesis_no == thesis_id).first()
    if not thesis:
        raise HTTPException(status_code=404, detail="Thesis not found")
    db.delete(thesis)
    db.commit()
    return {"message": "Thesis deleted successfully"}

# --- Üniversite Endpoint'leri ---
@app.get("/universities/", response_model=List[UniversityResponse])
def list_all_universities(db: Session = Depends(get_db)):
    return db.query(University).all()

@app.delete("/universities/{university_id}", response_model=UniversityResponse)
def delete_university(university_id: int, db: Session = Depends(get_db)):
    university = db.query(University).filter(University.university_id == university_id).first()
    if not university:
        raise HTTPException(status_code=404, detail="University not found")
    db.delete(university)
    db.commit()
    return {"message": "University deleted successfully"}

@app.post("/universities/", response_model=UniversityResponse)
def create_university(university: UniversityCreate, db: Session = Depends(get_db)):
    db_university = University(**university.dict())
    db.add(db_university)
    db.commit()
    db.refresh(db_university)
    return db_university

@app.put("/universities/{university_id}", response_model=UniversityResponse)
def update_university(university_id: int, university: UniversityUpdate, db: Session = Depends(get_db)):
    db_university = db.query(University).filter(University.university_id == university_id).first()
    if not db_university:
        raise HTTPException(status_code=404, detail="University not found")
    for key, value in university.dict(exclude_unset=True).items():
        setattr(db_university, key, value)
    db.commit()
    db.refresh(db_university)
    return db_university

# --- Enstitü Endpoint'leri ---
@app.get("/institutes/", response_model=List[InstituteResponse])
def list_all_institutes(db: Session = Depends(get_db)):
    return db.query(Institute).all()

@app.delete("/institutes/{institute_id}", response_model=InstituteResponse)
def delete_institute(institute_id: int, db: Session = Depends(get_db)):
    institute = db.query(Institute).filter(Institute.institute_id == institute_id).first()
    if not institute:
        raise HTTPException(status_code=404, detail="Institute not found")
    db.delete(institute)
    db.commit()
    return {"message": "Institute deleted successfully"}

@app.post("/institutes/", response_model=InstituteResponse)
def create_institute(institute: InstituteCreate, db: Session = Depends(get_db)):
    db_institute = Institute(**institute.dict())
    db.add(db_institute)
    db.commit()
    db.refresh(db_institute)
    return db_institute

@app.put("/institutes/{institute_id}", response_model=InstituteResponse)
def update_institute(institute_id: int, institute: InstituteUpdate, db: Session = Depends(get_db)):
    db_institute = db.query(Institute).filter(Institute.institute_id == institute_id).first()
    if not db_institute:
        raise HTTPException(status_code=404, detail="Institute not found")
    for key, value in institute.dict(exclude_unset=True).items():
        setattr(db_institute, key, value)
    db.commit()
    db.refresh(db_institute)
    return db_institute

# --- Dil Endpoint'leri ---
@app.get("/languages/", response_model=List[LanguageResponse])
def list_all_languages(db: Session = Depends(get_db)):
    return db.query(Language).all()

@app.delete("/languages/{language_id}", response_model=LanguageResponse)
def delete_language(language_id: int, db: Session = Depends(get_db)):
    language = db.query(Language).filter(Language.language_id == language_id).first()
    if not language:
        raise HTTPException(status_code=404, detail="Language not found")
    db.delete(language)
    db.commit()
    return {"message": "Language deleted successfully"}

@app.post("/languages/", response_model=LanguageResponse)
def create_language(language: LanguageBase, db: Session = Depends(get_db)):
    db_language = Language(**language.dict())
    db.add(db_language)
    db.commit()
    db.refresh(db_language)
    return db_language

@app.put("/languages/{language_id}", response_model=LanguageResponse)
def update_language(language_id: int, language: LanguageBase, db: Session = Depends(get_db)):
    db_language = db.query(Language).filter(Language.language_id == language_id).first()
    if not db_language:
        raise HTTPException(status_code=404, detail="Language not found")
    for key, value in language.dict(exclude_unset=True).items():
        setattr(db_language, key, value)
    db.commit()
    db.refresh(db_language)
    return db_language

# --- Anahtar Kelime Endpoint'leri ---
@app.get("/keywords/", response_model=List[KeywordResponse])
def list_all_keywords(db: Session = Depends(get_db)):
    return db.query(Keyword).all()

@app.delete("/keywords/{keyword_id}", response_model=KeywordResponse)
def delete_keyword(keyword_id: int, db: Session = Depends(get_db)):
    keyword = db.query(Keyword).filter(Keyword.keyword_id == keyword_id).first()
    if not keyword:
        raise HTTPException(status_code=404, detail="Keyword not found")
    db.delete(keyword)
    db.commit()
    return {"message": "Keyword deleted successfully"}

@app.post("/keywords/", response_model=KeywordResponse)
def create_keyword(keyword: KeywordBase, db: Session = Depends(get_db)):
    db_keyword = Keyword(**keyword.dict())
    db.add(db_keyword)
    db.commit()
    db.refresh(db_keyword)
    return db_keyword

@app.put("/keywords/{keyword_id}", response_model=KeywordResponse)
def update_keyword(keyword_id: int, keyword: KeywordBase, db: Session = Depends(get_db)):
    db_keyword = db.query(Keyword).filter(Keyword.keyword_id == keyword_id).first()
    if not db_keyword:
        raise HTTPException(status_code=404, detail="Keyword not found")
    for key, value in keyword.dict(exclude_unset=True).items():
        setattr(db_keyword, key, value)
    db.commit()
    db.refresh(db_keyword)
    return db_keyword

# --- Konu Başlığı Endpoint'leri ---
@app.get("/subject-topics/", response_model=List[SubjectTopicResponse])
def list_all_subject_topics(db: Session = Depends(get_db)):
    return db.query(SubjectTopic).all()

@app.delete("/subject-topics/{topic_id}", response_model=SubjectTopicResponse)
def delete_subject_topic(topic_id: int, db: Session = Depends(get_db)):
    topic = db.query(SubjectTopic).filter(SubjectTopic.topic_id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Subject topic not found")
    db.delete(topic)
    db.commit()
    return {"message": "Subject topic deleted successfully"}

@app.post("/subject-topics/", response_model=SubjectTopicResponse)
def create_subject_topic(topic: SubjectTopicBase, db: Session = Depends(get_db)):
    db_topic = SubjectTopic(**topic.dict())
    db.add(db_topic)
    db.commit()
    db.refresh(db_topic)
    return db_topic

@app.put("/subject-topics/{topic_id}", response_model=SubjectTopicResponse)
def update_subject_topic(topic_id: int, topic: SubjectTopicBase, db: Session = Depends(get_db)):
    db_topic = db.query(SubjectTopic).filter(SubjectTopic.topic_id == topic_id).first()
    if not db_topic:
        raise HTTPException(status_code=404, detail="Subject topic not found")
    for key, value in topic.dict(exclude_unset=True).items():
        setattr(db_topic, key, value)
    db.commit()
    db.refresh(db_topic)
    return db_topic

#Author Endpoint'leri
@app.get("/authors/", response_model=List[AuthorResponse])
def list_all_authors(db: Session = Depends(get_db)):
    return db.query(Author).all()

@app.delete("/authors/{author_id}", response_model=AuthorResponse)
def delete_author(author_id: int, db: Session = Depends(get_db)):
    author = db.query(Author).filter(Author.author_id == author_id).first()
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")
    db.delete(author)
    db.commit()
    return {"message": "Author deleted successfully"}

@app.post("/authors/", response_model=AuthorResponse)
def create_author(author: AuthorBase, db: Session = Depends(get_db)):
    db_author = Author(**author.dict())
    db.add(db_author)
    db.commit()
    db.refresh(db_author)
    return db_author

@app.put("/authors/{author_id}", response_model=AuthorResponse)
def update_author(author_id: int, author: AuthorBase, db: Session = Depends(get_db)):
    db_author = db.query(Author).filter(Author.author_id == author_id).first()
    if not db_author:
        raise HTTPException(status_code=404, detail="Author not found")
    for key, value in author.dict(exclude_unset=True).items():
        setattr(db_author, key, value)
    db.commit()
    db.refresh(db_author)
    return db_author

#Supervisor Endpoint'leri
@app.get("/supervisors/", response_model=List[SupervisorResponse])
def list_all_supervisors(db: Session = Depends(get_db)):
    return db.query(Supervisor).all()

@app.delete("/supervisors/{supervisor_id}", response_model=SupervisorResponse)
def delete_supervisor(supervisor_id: int, db: Session = Depends(get_db)):
    supervisor = db.query(Supervisor).filter(Supervisor.institute_id == supervisor_id).first()
    if not supervisor:
        raise HTTPException(status_code=404, detail="Supervisor not found")
    db.delete(supervisor)
    db.commit()
    return {"message": "Supervisor deleted successfully"}

@app.post("/supervisors/", response_model=SupervisorResponse)
def create_supervisor(supervisor: SupervisorBase, db: Session = Depends(get_db)):
    db_supervisor = Supervisor(**supervisor.dict())
    db.add(db_supervisor)
    db.commit()
    db.refresh(db_supervisor)
    return db_supervisor

@app.put("/supervisors/{supervisor_id}", response_model=SupervisorResponse)
def update_supervisor(supervisor_id: int, supervisor: SupervisorBase, db: Session = Depends(get_db)):
    db_supervisor = db.query(Supervisor).filter(Supervisor.institute_id == supervisor_id).first()
    if not db_supervisor:
        raise HTTPException(status_code=404, detail="Supervisor not found")
    for key, value in supervisor.dict(exclude_unset=True).items():
        setattr(db_supervisor, key, value)
    db.commit()
    db.refresh(db_supervisor)
    return db_supervisor



def init_db():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init_db()
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
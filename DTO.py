from pydantic import BaseModel
from typing import Optional, List
from datetime import date

# Author schemas
class AuthorBase(BaseModel):
    first_name: str
    last_name: str

class AuthorCreate(AuthorBase):
    pass

class AuthorResponse(AuthorBase):
    author_id: int
    
    class Config:
        from_attributes = True

class AuthorUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None

# University schemas
class UniversityBase(BaseModel):
    name: str

class UniversityCreate(UniversityBase):
    pass

class UniversityResponse(UniversityBase):
    university_id: int

    class Config:
        from_attributes = True

class UniversityUpdate(BaseModel):
    name: Optional[str] = None

# Institute schemas
class InstituteBase(BaseModel):
    name: str
    university_id: int

class InstituteCreate(InstituteBase):
    pass

class InstituteResponse(InstituteBase):
    institute_id: int

    class Config:
        from_attributes = True

class InstituteUpdate(BaseModel):
    name: Optional[str] = None
    university_id: Optional[int] = None

# Language schemas
class LanguageBase(BaseModel):
    language_name: str

class LanguageCreate(LanguageBase):
    pass

class LanguageResponse(LanguageBase):
    language_id: int

    class Config:
        from_attributes = True

class LanguageUpdate(BaseModel):
    language_name: Optional[str] = None

# Keyword schemas
class KeywordBase(BaseModel):
    keyword_name: str

class KeywordCreate(KeywordBase):
    pass

class KeywordResponse(KeywordBase):
    keyword_id: int

    class Config:
        from_attributes = True

class KeywordUpdate(BaseModel):
    keyword_name: Optional[str] = None

# SubjectTopic schemas
class SubjectTopicBase(BaseModel):
    topic_name: str

class SubjectTopicCreate(SubjectTopicBase):
    pass

class SubjectTopicResponse(SubjectTopicBase):
    topic_id: int

    class Config:
        from_attributes = True

class SubjectTopicUpdate(BaseModel):
    topic_name: Optional[str] = None

# Supervisor schemas
class SupervisorBase(BaseModel):
    first_name: str
    last_name: str
    title: Optional[str] = None

class SupervisorCreate(SupervisorBase):
    pass

class SupervisorResponse(SupervisorBase):
    institute_id: int

    class Config:
        from_attributes = True

class SupervisorUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    title: Optional[str] = None

# Thesis schemas
class ThesisBase(BaseModel):
    title: str
    abstract: str
    author_id: int
    year: int
    type: str
    university_id: int
    institute_id: int
    number_of_pages: int
    submission_date: date
    language_id: int

class ThesisCreate(ThesisBase):
    pass

class ThesisResponse(ThesisBase):
    thesis_no: int

    class Config:
        from_attributes = True

class ThesisUpdate(BaseModel):
    title: Optional[str] = None
    abstract: Optional[str] = None
    author_id: Optional[int] = None
    year: Optional[int] = None
    type: Optional[str] = None
    university_id: Optional[int] = None
    institute_id: Optional[int] = None
    number_of_pages: Optional[int] = None
    submission_date: Optional[date] = None
    language_id: Optional[int] = None

# ThesisKeyword schemas
class ThesisKeywordBase(BaseModel):
    thesis_no: int
    keyword_id: int

class ThesisKeywordCreate(ThesisKeywordBase):
    pass

class ThesisKeywordResponse(ThesisKeywordBase):
    class Config:
        from_attributes = True

# ThesisSupervisor schemas
class ThesisSupervisorBase(BaseModel):
    thesis_no: int
    supervisor_id: int
    is_co_supervisor: Optional[bool] = False

class ThesisSupervisorCreate(ThesisSupervisorBase):
    pass

class ThesisSupervisorResponse(ThesisSupervisorBase):
    class Config:
        from_attributes = True

class ThesisSupervisorUpdate(BaseModel):
    is_co_supervisor: Optional[bool] = None

# ThesisTopic schemas
class ThesisTopicBase(BaseModel):
    thesis_no: int
    topic_id: int

class ThesisTopicCreate(ThesisTopicBase):
    pass

class ThesisTopicResponse(ThesisTopicBase):
    class Config:
        from_attributes = True

# Enhanced Response Models with Relationships
class ThesisResponseWithRelations(ThesisResponse):
    author: AuthorResponse
    university: UniversityResponse
    institute: InstituteResponse
    language: LanguageResponse
    keywords: List[KeywordResponse] = []
    supervisors: List[SupervisorResponse] = []
    topics: List[SubjectTopicResponse] = []

    class Config:
        from_attributes = True
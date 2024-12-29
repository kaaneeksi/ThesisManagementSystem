from sqlalchemy import Column, Integer, String, ForeignKey, Date, Text, Boolean, CheckConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class University(Base):
    __tablename__ = 'university'
    
    university_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    
    institutes = relationship("Institute", back_populates="university", cascade="all, delete")
    theses = relationship("Thesis", back_populates="university", cascade="all, delete")

class Institute(Base):
    __tablename__ = 'institute'
    
    institute_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    university_id = Column(Integer, ForeignKey('university.university_id', onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    
    university = relationship("University", back_populates="institutes")
    theses = relationship("Thesis", back_populates="institute", cascade="all, delete")

class Author(Base):
    __tablename__ = 'author'
    
    author_id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    
    theses = relationship("Thesis", back_populates="author", cascade="all, delete")

class Language(Base):
    __tablename__ = 'language'
    
    language_id = Column(Integer, primary_key=True, autoincrement=True)
    language_name = Column(String(50), nullable=False, unique=True)
    
    theses = relationship("Thesis", back_populates="language")

class Keyword(Base):
    __tablename__ = 'keyword'
    
    keyword_id = Column(Integer, primary_key=True, autoincrement=True)
    keyword_name = Column(String(100), nullable=False)
    
    theses = relationship("Thesis", secondary="thesis_keyword", back_populates="keywords")

class SubjectTopic(Base):
    __tablename__ = 'subject_topic'
    
    topic_id = Column(Integer, primary_key=True, autoincrement=True)
    topic_name = Column(String(100), nullable=False)
    
    theses = relationship("Thesis", secondary="thesis_topic", back_populates="topics")

class Supervisor(Base):
    __tablename__ = 'supervisor'
    
    institute_id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    title = Column(String)
    
    theses = relationship("Thesis", secondary="thesis_supervisor", back_populates="supervisors")

class Thesis(Base):
    __tablename__ = 'thesis'
    
    thesis_no = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(500), nullable=False)
    abstract = Column(Text, nullable=False)
    author_id = Column(Integer, ForeignKey('author.author_id', onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    year = Column(Integer, nullable=False)
    type = Column(String(50), nullable=False)
    university_id = Column(Integer, ForeignKey('university.university_id', onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    institute_id = Column(Integer, ForeignKey('institute.institute_id', onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    number_of_pages = Column(Integer, nullable=False)
    submission_date = Column(Date, nullable=False)
    language_id = Column(Integer, ForeignKey('language.language_id'), nullable=False)
    
    __table_args__ = (
        CheckConstraint(
            type.in_(['Master', 'Doctorate', 'Specialization in Medicine', 'Proficiency in Art']),
            name='thesis_type_check'
        ),
    )
    
    author = relationship("Author", back_populates="theses")
    university = relationship("University", back_populates="theses")
    institute = relationship("Institute", back_populates="theses")
    language = relationship("Language", back_populates="theses")
    keywords = relationship("Keyword", secondary="thesis_keyword", back_populates="theses")
    supervisors = relationship("Supervisor", secondary="thesis_supervisor", back_populates="theses")
    topics = relationship("SubjectTopic", secondary="thesis_topic", back_populates="theses")

class ThesisKeyword(Base):
    __tablename__ = 'thesis_keyword'
    
    thesis_no = Column(Integer, ForeignKey('thesis.thesis_no', onupdate="CASCADE", ondelete="CASCADE"), primary_key=True)
    keyword_id = Column(Integer, ForeignKey('keyword.keyword_id', onupdate="CASCADE", ondelete="CASCADE"), primary_key=True)

class ThesisSupervisor(Base):
    __tablename__ = 'thesis_supervisor'
    
    thesis_no = Column(Integer, ForeignKey('thesis.thesis_no', onupdate="CASCADE", ondelete="CASCADE"), primary_key=True)
    supervisor_id = Column(Integer, ForeignKey('supervisor.institute_id', onupdate="CASCADE", ondelete="CASCADE"), primary_key=True)
    is_co_supervisor = Column(Boolean, default=False)

class ThesisTopic(Base):
    __tablename__ = 'thesis_topic'
    
    thesis_no = Column(Integer, ForeignKey('thesis.thesis_no', onupdate="CASCADE", ondelete="CASCADE"), primary_key=True)
    topic_id = Column(Integer, ForeignKey('subject_topic.topic_id', onupdate="CASCADE", ondelete="CASCADE"), primary_key=True)
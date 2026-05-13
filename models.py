"""
Database Models for EduSence AI
PostgreSQL schema using SQLAlchemy ORM
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Student(Base):
    """Registered students with cloud-stored embeddings"""
    __tablename__ = 'students'
    
    id = Column(Integer, primary_key=True)
    student_id = Column(String(50), unique=True, nullable=False, index=True)
    student_name = Column(String(200), nullable=False)
    cloudinary_folder = Column(String(500))  # Cloudinary folder path
    embeddings_metadata = Column(JSON)  # Metadata about embeddings
    num_embeddings = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    images = relationship('StudentImage', back_populates='student', cascade='all, delete-orphan')
    analytics = relationship('Analytics', back_populates='student', cascade='all, delete-orphan')
    recognition_logs = relationship('RecognitionLog', back_populates='student', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<Student(id={self.id}, student_id='{self.student_id}', name='{self.student_name}')>"


class StudentImage(Base):
    """Cloud-stored student registration images"""
    __tablename__ = 'student_images'
    
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey('students.id'), nullable=False, index=True)
    image_url = Column(String(500), nullable=False)  # Cloudinary secure URL
    public_id = Column(String(500), nullable=False)  # Cloudinary public ID
    thumbnail_url = Column(String(500))  # Cloudinary thumbnail URL
    embedding_vector = Column(Text)  # Serialized embedding (base64 or JSON)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    student = relationship('Student', back_populates='images')
    
    def __repr__(self):
        return f"<StudentImage(id={self.id}, student_id={self.student_id}, public_id='{self.public_id}')>"


class Session(Base):
    """Processing sessions (webcam or video)"""
    __tablename__ = 'sessions'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String(100), unique=True, nullable=False, index=True)
    session_name = Column(String(200))
    session_type = Column(String(20), nullable=False)  # 'webcam' or 'video'
    cloudinary_folder = Column(String(500))  # Session folder in Cloudinary
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime)
    total_frames = Column(Integer, default=0)
    total_students = Column(Integer, default=0)
    status = Column(String(20), default='active')  # 'active', 'completed', 'failed'
    
    # Relationships
    analytics = relationship('Analytics', back_populates='session', cascade='all, delete-orphan')
    recognition_logs = relationship('RecognitionLog', back_populates='session', cascade='all, delete-orphan')
    uploaded_videos = relationship('UploadedVideo', back_populates='session', cascade='all, delete-orphan')
    session_images = relationship('SessionImage', back_populates='session', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<Session(id={self.id}, session_id='{self.session_id}', type='{self.session_type}')>"


class SessionImage(Base):
    """Cloud-stored face crops from sessions"""
    __tablename__ = 'session_images'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey('sessions.id'), nullable=False, index=True)
    student_db_id = Column(Integer, ForeignKey('students.id'), index=True)  # NULL for unknown persons
    track_id = Column(Integer)
    frame_number = Column(Integer)
    image_url = Column(String(500), nullable=False)  # Cloudinary secure URL
    public_id = Column(String(500), nullable=False)  # Cloudinary public ID
    thumbnail_url = Column(String(500))
    confidence = Column(Float)
    is_registered = Column(Boolean, default=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    session = relationship('Session', back_populates='session_images')
    student = relationship('Student')
    
    def __repr__(self):
        return f"<SessionImage(id={self.id}, session_id={self.session_id}, frame={self.frame_number})>"


class Analytics(Base):
    """Engagement analytics per student per session"""
    __tablename__ = 'analytics'
    
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey('students.id'), nullable=False, index=True)
    session_id = Column(Integer, ForeignKey('sessions.id'), nullable=False, index=True)
    
    # Engagement metrics
    engagement_score = Column(Float)
    total_frames = Column(Integer, default=0)
    focused_frames = Column(Integer, default=0)
    moderately_focused_frames = Column(Integer, default=0)
    unfocused_frames = Column(Integer, default=0)
    
    # Head pose statistics
    avg_yaw = Column(Float)
    avg_pitch = Column(Float)
    avg_roll = Column(Float)
    
    # Sample images (Cloudinary URLs)
    sample_image_urls = Column(JSON)  # List of Cloudinary URLs
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    student = relationship('Student', back_populates='analytics')
    session = relationship('Session', back_populates='analytics')
    
    def __repr__(self):
        return f"<Analytics(id={self.id}, student_id={self.student_id}, engagement={self.engagement_score})>"


class RecognitionLog(Base):
    """Recognition events log"""
    __tablename__ = 'recognition_logs'
    
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey('students.id'), nullable=False, index=True)
    session_id = Column(Integer, ForeignKey('sessions.id'), nullable=False, index=True)
    track_id = Column(Integer)
    frame_number = Column(Integer)
    confidence = Column(Float)
    recognition_time_ms = Column(Float)  # Time taken for recognition
    recognized_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    student = relationship('Student', back_populates='recognition_logs')
    session = relationship('Session', back_populates='recognition_logs')
    
    def __repr__(self):
        return f"<RecognitionLog(id={self.id}, student_id={self.student_id}, confidence={self.confidence})>"


class UploadedVideo(Base):
    """Cloud-stored uploaded videos"""
    __tablename__ = 'uploaded_videos'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey('sessions.id'), nullable=False, index=True)
    original_filename = Column(String(500))
    video_url = Column(String(500), nullable=False)  # Cloudinary secure URL
    public_id = Column(String(500), nullable=False)  # Cloudinary public ID
    thumbnail_url = Column(String(500))
    duration_seconds = Column(Float)
    file_size_bytes = Column(Integer)
    format = Column(String(20))
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    session = relationship('Session', back_populates='uploaded_videos')
    
    def __repr__(self):
        return f"<UploadedVideo(id={self.id}, filename='{self.original_filename}')>"


class SystemConfig(Base):
    """System configuration and metadata"""
    __tablename__ = 'system_config'
    
    id = Column(Integer, primary_key=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(Text)
    description = Column(Text)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<SystemConfig(key='{self.key}', value='{self.value}')>"

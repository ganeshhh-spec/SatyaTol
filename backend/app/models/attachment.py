from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.db.session import Base


class Attachment(Base):
    __tablename__ = "attachments"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    media_type = Column(String(100), nullable=False)
    storage_key = Column(String(255), nullable=False)
    uploader_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    application = relationship("Application", back_populates="attachments")
    uploader = relationship("User", back_populates="attachments")


from app.models.application import Application
from app.models.user import User

Application.attachments = relationship("Attachment", back_populates="application", lazy="dynamic")
User.attachments = relationship("Attachment", back_populates="uploader", lazy="dynamic")
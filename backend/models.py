from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class Project(Base):
    __tablename__ = 'projects'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(String(300))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    variables = relationship('Variable', back_populates='project', cascade='all, delete-orphan')


class Variable(Base):
    __tablename__ = 'variables'

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False)
    key = Column(String(200), nullable=False)
    value_encrypted = Column(Text, nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    project = relationship('Project', back_populates='variables')
    history = relationship('VariableHistory', back_populates='variable', cascade='all, delete-orphan')


class VariableHistory(Base):
    __tablename__ = 'variable_history'

    id = Column(Integer, primary_key=True)
    variable_id = Column(Integer, ForeignKey('variables.id'), nullable=False)
    old_value_encrypted = Column(Text)
    new_value_encrypted = Column(Text, nullable=False)
    changed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    variable = relationship('Variable', back_populates='history')

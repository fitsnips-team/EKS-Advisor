"""
Database configuration and setup for EKS Advisor
Supports SQLite (default) and PostgreSQL with environment-based configuration
"""

import os
from typing import Generator
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# Database URL configuration with fallback to SQLite
DATABASE_URL = os.getenv(
    'DATABASE_URL', 
    'sqlite:///./eks_advisor_history.db'
)

# SQLAlchemy engine configuration
engine_kwargs = {}

if DATABASE_URL.startswith('sqlite'):
    # SQLite-specific configuration
    engine_kwargs.update({
        'poolclass': StaticPool,
        'connect_args': {
            'check_same_thread': False,  # Allow multiple threads
            'timeout': 20  # 20 second timeout
        },
        'echo': False  # Set to True for SQL debugging
    })
else:
    # PostgreSQL/MySQL configuration
    engine_kwargs.update({
        'pool_pre_ping': True,  # Verify connections before use
        'pool_recycle': 300,    # Recycle connections every 5 minutes
        'pool_size': 5,         # Connection pool size
        'max_overflow': 10,     # Additional connections beyond pool_size
        'echo': False           # Set to True for SQL debugging
    })

# Create engine
engine = create_engine(DATABASE_URL, **engine_kwargs)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create declarative base for models
Base = declarative_base()

# Metadata for migrations
metadata = MetaData()

def get_database_session() -> Generator[Session, None, None]:
    """
    Get database session with automatic cleanup
    
    Usage:
        with get_database_session() as db:
            # Use db session
            pass
    """
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def get_database_info() -> dict:
    """Get information about the current database configuration"""
    
    db_type = "sqlite" if DATABASE_URL.startswith('sqlite') else "postgresql"
    db_file = None
    
    if db_type == "sqlite":
        # Extract filename from SQLite URL
        db_file = DATABASE_URL.replace('sqlite:///', '')
        if not db_file.startswith('/'):
            db_file = os.path.abspath(db_file)
    
    return {
        'type': db_type,
        'url': DATABASE_URL,
        'file': db_file,
        'engine_info': {
            'driver': engine.dialect.name,
            'pool_size': getattr(engine.pool, 'size', 'N/A'),
            'echo': engine.echo
        }
    }

def create_tables():
    """Create all tables defined in models"""
    # Import models to register them with Base
    from models.history_model import AnalysisHistory, ClusterSnapshot
    Base.metadata.create_all(bind=engine)

def drop_tables():
    """Drop all tables (use with caution!)"""
    Base.metadata.drop_all(bind=engine)

def test_connection() -> bool:
    """Test database connection"""
    try:
        from sqlalchemy import text
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"Database connection test failed: {e}")
        return False

# Export commonly used items
__all__ = [
    'Base',
    'engine', 
    'SessionLocal',
    'get_database_session',
    'get_database_info',
    'create_tables',
    'drop_tables',
    'test_connection'
]
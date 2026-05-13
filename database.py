"""
Database Configuration and Session Management
PostgreSQL connection using SQLAlchemy with connection pooling
PRODUCTION-READY with proper pool management and health checks
"""

import os
import logging
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import OperationalError, DisconnectionError
from dotenv import load_dotenv
from models import Base
import time

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Production-grade database manager with connection pooling
    - Optimized pool settings
    - Automatic reconnection
    - Health checks
    - Performance monitoring
    """
    
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL')
        self.engine = None
        self.SessionLocal = None
        self.initialized = False
        
        # Pool statistics
        self.total_connections = 0
        self.failed_connections = 0
        self.reconnection_attempts = 0
        
        if not self.database_url:
            logger.warning("⚠️  DATABASE_URL not set. Database features disabled.")
            logger.warning("   Set DATABASE_URL in .env file to enable cloud storage.")
            return
        
        self._initialize_engine()
    
    def _initialize_engine(self):
        """Initialize database engine with optimized connection pooling"""
        try:
            logger.info("🔄 Initializing database connection pool...")
            
            # Production-grade pool settings
            pool_size = int(os.getenv('DB_POOL_SIZE', '10'))
            max_overflow = int(os.getenv('DB_MAX_OVERFLOW', '20'))
            pool_timeout = int(os.getenv('DB_POOL_TIMEOUT', '30'))
            pool_recycle = int(os.getenv('DB_POOL_RECYCLE', '3600'))
            
            # Create engine with optimized pooling
            self.engine = create_engine(
                self.database_url,
                poolclass=QueuePool,
                pool_size=pool_size,
                max_overflow=max_overflow,
                pool_timeout=pool_timeout,
                pool_pre_ping=True,  # Verify connections before using
                pool_recycle=pool_recycle,  # Recycle connections after 1 hour
                echo=False,  # Set to True for SQL debugging
                connect_args={
                    'connect_timeout': 10,
                    'application_name': 'edusence_ai'
                }
            )
            
            # Add connection event listeners for monitoring
            @event.listens_for(self.engine, "connect")
            def receive_connect(dbapi_conn, connection_record):
                self.total_connections += 1
                logger.debug(f"📊 New DB connection (total: {self.total_connections})")
            
            @event.listens_for(self.engine, "checkout")
            def receive_checkout(dbapi_conn, connection_record, connection_proxy):
                # Test connection on checkout
                try:
                    cursor = dbapi_conn.cursor()
                    cursor.execute("SELECT 1")
                    cursor.close()
                except Exception as e:
                    logger.warning(f"⚠️  Stale connection detected, invalidating...")
                    connection_record.invalidate()
                    raise DisconnectionError()
            
            # Test connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            # Create session factory with scoped sessions (thread-safe)
            session_factory = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            self.SessionLocal = scoped_session(session_factory)
            
            self.initialized = True
            
            logger.info("=" * 60)
            logger.info("✅ Database Connection Pool Initialized")
            logger.info("=" * 60)
            logger.info(f"   Pool size: {pool_size}")
            logger.info(f"   Max overflow: {max_overflow}")
            logger.info(f"   Pool timeout: {pool_timeout}s")
            logger.info(f"   Pool recycle: {pool_recycle}s")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            logger.warning("   Application will run in local-only mode")
            self.initialized = False
            self.failed_connections += 1
    
    def create_tables(self):
        """Create all database tables"""
        if not self.initialized:
            logger.warning("⚠️  Database not initialized. Skipping table creation.")
            return False
        
        try:
            logger.info("🔄 Creating database tables...")
            Base.metadata.create_all(bind=self.engine)
            logger.info("✅ Database tables created successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to create tables: {e}")
            return False
    
    def drop_tables(self):
        """Drop all database tables (use with caution!)"""
        if not self.initialized:
            return False
        
        try:
            logger.warning("⚠️  Dropping all database tables...")
            Base.metadata.drop_all(bind=self.engine)
            logger.info("✅ Database tables dropped")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to drop tables: {e}")
            return False
    
    def get_session(self):
        """
        Get a new database session
        PRODUCTION: Uses scoped sessions for thread safety
        """
        if not self.initialized:
            return None
        
        try:
            return self.SessionLocal()
        except Exception as e:
            logger.error(f"❌ Failed to create session: {e}")
            self.failed_connections += 1
            return None
    
    def close_session(self, session):
        """Close a database session"""
        if session:
            try:
                session.close()
            except Exception as e:
                logger.error(f"❌ Error closing session: {e}")
    
    def commit_session(self, session):
        """Commit a database session"""
        if session:
            try:
                session.commit()
                return True
            except Exception as e:
                logger.error(f"❌ Error committing session: {e}")
                session.rollback()
                return False
    
    def rollback_session(self, session):
        """Rollback a database session"""
        if session:
            try:
                session.rollback()
            except Exception as e:
                logger.error(f"❌ Error rolling back session: {e}")
    
    def is_available(self):
        """Check if database is available"""
        return self.initialized
    
    def test_connection(self):
        """Test database connection with retry"""
        if not self.initialized:
            return False
        
        max_retries = 3
        retry_delay = 1.0
        
        for attempt in range(max_retries):
            try:
                with self.engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                return True
            except Exception as e:
                logger.warning(f"⚠️  Connection test failed (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
        
        logger.error("❌ Database connection test failed after all retries")
        return False
    
    def get_pool_status(self):
        """Get connection pool status"""
        if not self.initialized or not self.engine:
            return None
        
        try:
            pool = self.engine.pool
            return {
                'size': pool.size(),
                'checked_in': pool.checkedin(),
                'checked_out': pool.checkedout(),
                'overflow': pool.overflow(),
                'total_connections': self.total_connections,
                'failed_connections': self.failed_connections
            }
        except Exception as e:
            logger.error(f"❌ Failed to get pool status: {e}")
            return None
    
    def get_stats(self):
        """Get database statistics"""
        if not self.initialized:
            return None
        
        try:
            session = self.get_session()
            
            from models import Student, Session, Analytics, RecognitionLog
            
            stats = {
                'total_students': session.query(Student).count(),
                'total_sessions': session.query(Session).count(),
                'total_analytics': session.query(Analytics).count(),
                'total_recognition_logs': session.query(RecognitionLog).count(),
                'pool_status': self.get_pool_status()
            }
            
            self.close_session(session)
            return stats
            
        except Exception as e:
            logger.error(f"❌ Failed to get database stats: {e}")
            return None
    
    def health_check(self):
        """Comprehensive health check"""
        if not self.initialized:
            return {
                'healthy': False,
                'error': 'Database not initialized'
            }
        
        try:
            # Test connection
            connection_ok = self.test_connection()
            
            # Get pool status
            pool_status = self.get_pool_status()
            
            # Check if pool is exhausted
            pool_exhausted = False
            if pool_status:
                pool_exhausted = (pool_status['checked_out'] >= pool_status['size'] + pool_status['overflow'])
            
            return {
                'healthy': connection_ok and not pool_exhausted,
                'connection_ok': connection_ok,
                'pool_status': pool_status,
                'pool_exhausted': pool_exhausted,
                'total_connections': self.total_connections,
                'failed_connections': self.failed_connections
            }
            
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e)
            }


# Global database manager instance
db_manager = DatabaseManager()


def get_db_session():
    """Get a database session (for use in routes)"""
    return db_manager.get_session()


def init_database():
    """Initialize database and create tables"""
    if db_manager.is_available():
        return db_manager.create_tables()
    return False


def test_database_connection():
    """Test database connection"""
    return db_manager.test_connection()


def get_db_health():
    """Get database health status"""
    return db_manager.health_check()

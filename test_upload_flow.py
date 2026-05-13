#!/usr/bin/env python3
"""
Test Upload Flow
Verifies that images are being uploaded to Cloudinary and saved to PostgreSQL
"""

import os
import sys
import time
import logging
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_database_connection():
    """Test PostgreSQL connection"""
    logger.info("=" * 60)
    logger.info("1. Testing Database Connection")
    logger.info("=" * 60)
    
    try:
        from database import db_manager, get_db_session
        
        if not db_manager.is_available():
            logger.error("❌ Database not available")
            return False
        
        # Test connection
        session = get_db_session()
        if not session:
            logger.error("❌ Failed to get database session")
            return False
        
        # Query sessions
        from models import Session, SessionImage, Student
        
        total_sessions = session.query(Session).count()
        total_images = session.query(SessionImage).count()
        total_students = session.query(Student).count()
        
        logger.info(f"✅ Database connected")
        logger.info(f"   Total sessions: {total_sessions}")
        logger.info(f"   Total images: {total_images}")
        logger.info(f"   Total students: {total_students}")
        
        session.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Database test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_cloudinary_connection():
    """Test Cloudinary connection"""
    logger.info("\n" + "=" * 60)
    logger.info("2. Testing Cloudinary Connection")
    logger.info("=" * 60)
    
    try:
        from cloudinary_manager import cloudinary_manager
        
        if not cloudinary_manager.is_available():
            logger.error("❌ Cloudinary not available")
            return False
        
        logger.info(f"✅ Cloudinary connected")
        logger.info(f"   Cloud name: {cloudinary_manager.cloud_name}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Cloudinary test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_latest_session():
    """Test latest session data"""
    logger.info("\n" + "=" * 60)
    logger.info("3. Checking Latest Session")
    logger.info("=" * 60)
    
    try:
        from database import get_db_session
        from models import Session, SessionImage, Student
        
        session = get_db_session()
        if not session:
            logger.error("❌ Failed to get database session")
            return False
        
        try:
            # Get latest session
            latest_session = session.query(Session).order_by(Session.started_at.desc()).first()
            
            if not latest_session:
                logger.warning("⚠️  No sessions found in database")
                return False
            
            logger.info(f"✅ Latest session: {latest_session.session_id}")
            logger.info(f"   Type: {latest_session.session_type}")
            logger.info(f"   Started: {latest_session.started_at}")
            logger.info(f"   Status: {latest_session.status}")
            
            # Get session images
            images = session.query(SessionImage).filter_by(session_id=latest_session.id).all()
            
            logger.info(f"   Total images: {len(images)}")
            
            if len(images) == 0:
                logger.warning("⚠️  No images found for this session")
                logger.info("   This is expected if:")
                logger.info("   - Camera was just stopped (uploads still pending)")
                logger.info("   - No faces were detected during session")
                logger.info("   - Upload worker failed")
                return False
            
            # Group by student
            students_count = {}
            for img in images:
                if img.student_db_id:
                    student = session.query(Student).filter_by(id=img.student_db_id).first()
                    student_key = student.student_id if student else f"unknown_{img.track_id}"
                else:
                    student_key = f"unknown_{img.track_id}"
                
                students_count[student_key] = students_count.get(student_key, 0) + 1
            
            logger.info(f"   Unique students: {len(students_count)}")
            for student_id, count in students_count.items():
                logger.info(f"      - {student_id}: {count} images")
            
            # Show sample image URLs
            if len(images) > 0:
                logger.info(f"\n   Sample image URLs:")
                for i, img in enumerate(images[:3]):
                    logger.info(f"      {i+1}. {img.image_url}")
            
            return True
            
        finally:
            session.close()
        
    except Exception as e:
        logger.error(f"❌ Latest session test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_upload_worker_status():
    """Test upload worker status"""
    logger.info("\n" + "=" * 60)
    logger.info("4. Checking Upload Worker Status")
    logger.info("=" * 60)
    
    try:
        from upload_worker import get_upload_worker
        
        worker = get_upload_worker()
        
        if not worker:
            logger.warning("⚠️  Upload worker not initialized")
            return False
        
        stats = worker.get_statistics()
        
        logger.info(f"✅ Upload worker status:")
        logger.info(f"   Running: {stats['running']}")
        logger.info(f"   Queue size: {stats['queue_size']}/{stats['max_queue_size']}")
        logger.info(f"   Total queued: {stats['total_queued']}")
        logger.info(f"   Total uploaded: {stats['total_uploaded']}")
        logger.info(f"   Total failed: {stats['total_failed']}")
        logger.info(f"   Total dropped: {stats['total_dropped']}")
        logger.info(f"   Success rate: {stats['success_rate']}")
        logger.info(f"   Avg upload time: {stats['avg_upload_time_ms']}ms")
        
        if stats['queue_size'] > 0:
            logger.warning(f"⚠️  {stats['queue_size']} uploads still pending")
            logger.info("   Wait a moment and run this script again")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Upload worker test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    logger.info("\n" + "=" * 60)
    logger.info("🧪 EduSence Upload Flow Test")
    logger.info("=" * 60)
    
    results = {
        'database': test_database_connection(),
        'cloudinary': test_cloudinary_connection(),
        'latest_session': test_latest_session(),
        'upload_worker': test_upload_worker_status()
    }
    
    logger.info("\n" + "=" * 60)
    logger.info("📊 Test Results Summary")
    logger.info("=" * 60)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"{status} - {test_name}")
    
    all_passed = all(results.values())
    
    if all_passed:
        logger.info("\n✅ All tests passed! System is working correctly.")
        logger.info("\nIf analytics still shows 'No images found':")
        logger.info("1. Wait 30-60 seconds after stopping camera")
        logger.info("2. Check upload worker queue is empty")
        logger.info("3. Verify images are in database (run this script again)")
    else:
        logger.info("\n❌ Some tests failed. Check the errors above.")
    
    logger.info("=" * 60)
    
    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())

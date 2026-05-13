"""
Test Cloud Setup
Verify PostgreSQL and Cloudinary connections
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_database():
    """Test PostgreSQL connection"""
    print("=" * 60)
    print("Testing PostgreSQL (Neon) Connection")
    print("=" * 60)
    
    try:
        from database import db_manager, test_database_connection
        
        if db_manager.is_available():
            print("✅ Database manager initialized")
            
            if test_database_connection():
                print("✅ Database connection successful")
                
                # Get stats
                stats = db_manager.get_stats()
                if stats:
                    print(f"✅ Database stats retrieved:")
                    print(f"   - Students: {stats['total_students']}")
                    print(f"   - Sessions: {stats['total_sessions']}")
                    print(f"   - Analytics: {stats['total_analytics']}")
                    print(f"   - Recognition Logs: {stats['total_recognition_logs']}")
                
                return True
            else:
                print("❌ Database connection failed")
                return False
        else:
            print("❌ Database manager not initialized")
            print("   Check DATABASE_URL in .env file")
            return False
            
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False


def test_cloudinary():
    """Test Cloudinary connection"""
    print()
    print("=" * 60)
    print("Testing Cloudinary Connection")
    print("=" * 60)
    
    try:
        from cloudinary_manager import cloudinary_manager
        
        if cloudinary_manager.is_available():
            print("✅ Cloudinary manager initialized")
            print(f"   Cloud Name: {cloudinary_manager.cloud_name}")
            
            # Get usage stats
            usage = cloudinary_manager.get_usage_stats()
            if usage:
                print(f"✅ Cloudinary usage stats retrieved:")
                print(f"   - Storage: {usage['storage_used_mb']:.2f} MB")
                print(f"   - Bandwidth: {usage['bandwidth_used_mb']:.2f} MB")
                print(f"   - Credits: {usage['credits_used']}/{usage['credits_limit']}")
            
            return True
        else:
            print("❌ Cloudinary manager not initialized")
            print("   Check CLOUDINARY_* variables in .env file")
            return False
            
    except Exception as e:
        print(f"❌ Cloudinary test failed: {e}")
        return False


def test_storage_manager():
    """Test storage manager"""
    print()
    print("=" * 60)
    print("Testing Storage Manager")
    print("=" * 60)
    
    try:
        from storage_manager import storage_manager
        
        if storage_manager.is_cloud_enabled():
            print("✅ Storage Manager: Cloud mode enabled")
            print("   All data will be stored in PostgreSQL + Cloudinary")
            return True
        else:
            print("⚠️  Storage Manager: Local mode")
            print("   Data will be stored locally (cloud not configured)")
            return False
            
    except Exception as e:
        print(f"❌ Storage manager test failed: {e}")
        return False


def test_environment_variables():
    """Test environment variables"""
    print()
    print("=" * 60)
    print("Testing Environment Variables")
    print("=" * 60)
    
    required_vars = [
        'DATABASE_URL',
        'CLOUDINARY_CLOUD_NAME',
        'CLOUDINARY_API_KEY',
        'CLOUDINARY_API_SECRET'
    ]
    
    all_present = True
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            if 'SECRET' in var or 'PASSWORD' in var or 'KEY' in var:
                display_value = value[:10] + '...' if len(value) > 10 else '***'
            else:
                display_value = value[:50] + '...' if len(value) > 50 else value
            
            print(f"✅ {var}: {display_value}")
        else:
            print(f"❌ {var}: NOT SET")
            all_present = False
    
    return all_present


def main():
    """Run all tests"""
    print()
    print("🧪 EduSence AI - Cloud Setup Test")
    print()
    
    # Test environment variables
    env_ok = test_environment_variables()
    
    # Test database
    db_ok = test_database()
    
    # Test Cloudinary
    cloud_ok = test_cloudinary()
    
    # Test storage manager
    storage_ok = test_storage_manager()
    
    # Summary
    print()
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    tests = [
        ("Environment Variables", env_ok),
        ("PostgreSQL Database", db_ok),
        ("Cloudinary Storage", cloud_ok),
        ("Storage Manager", storage_ok)
    ]
    
    passed = sum(1 for _, ok in tests if ok)
    total = len(tests)
    
    for name, ok in tests:
        status = "✅ PASS" if ok else "❌ FAIL"
        print(f"{status} - {name}")
    
    print()
    print(f"Result: {passed}/{total} tests passed")
    
    if passed == total:
        print()
        print("🎉 All tests passed! Cloud storage is ready.")
        print()
        print("Next steps:")
        print("1. Integrate storage_manager into existing code")
        print("2. Test student registration with cloud storage")
        print("3. Test webcam session with cloud storage")
        print("4. Deploy to production")
        return 0
    else:
        print()
        print("⚠️  Some tests failed. Please fix the issues above.")
        print()
        print("Common fixes:")
        print("- Check .env file exists and has correct credentials")
        print("- Verify DATABASE_URL format")
        print("- Verify Cloudinary credentials")
        print("- Run: pip install -r requirements.txt")
        return 1


if __name__ == '__main__':
    sys.exit(main())

"""
Migrate Existing Local Data to Cloud
Uploads registered students from local storage to PostgreSQL + Cloudinary
"""

import os
import sys
import json
import pickle
import cv2
import numpy as np
import base64
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from database import get_db_session
from cloudinary_manager import cloudinary_manager
from models import Student, StudentImage

def migrate_registered_students():
    """Migrate registered students from local to cloud"""
    
    print("=" * 60)
    print("🔄 Migrating Registered Students to Cloud")
    print("=" * 60)
    
    local_registry_dir = 'registered_students'
    
    if not os.path.exists(local_registry_dir):
        print("❌ No local registry found")
        return
    
    session = get_db_session()
    if not session:
        print("❌ Database connection failed")
        return
    
    try:
        migrated_count = 0
        skipped_count = 0
        
        # Get list of student directories
        student_dirs = [d for d in os.listdir(local_registry_dir) 
                       if os.path.isdir(os.path.join(local_registry_dir, d))]
        
        print(f"📁 Found {len(student_dirs)} students in local storage")
        print()
        
        for student_id in student_dirs:
            student_dir = os.path.join(local_registry_dir, student_id)
            
            try:
                # Load metadata
                metadata_path = os.path.join(student_dir, 'metadata.json')
                if not os.path.exists(metadata_path):
                    print(f"⚠️  Skipping {student_id}: No metadata found")
                    skipped_count += 1
                    continue
                
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                
                student_name = metadata['student_name']
                
                # Check if already exists in database
                existing = session.query(Student).filter_by(student_id=student_id).first()
                if existing:
                    print(f"⏭️  Skipping {student_name} ({student_id}): Already in database")
                    skipped_count += 1
                    continue
                
                print(f"🔄 Migrating: {student_name} ({student_id})")
                
                # Load embeddings
                embeddings_path = os.path.join(student_dir, 'embeddings.pkl')
                if not os.path.exists(embeddings_path):
                    print(f"   ❌ No embeddings found")
                    skipped_count += 1
                    continue
                
                with open(embeddings_path, 'rb') as f:
                    embeddings = pickle.load(f)
                
                print(f"   ✅ Loaded {len(embeddings)} embeddings")
                
                # Create student record in database
                cloudinary_folder = cloudinary_manager.get_folder_path('registered_students', student_id)
                
                student = Student(
                    student_id=student_id,
                    student_name=student_name,
                    cloudinary_folder=cloudinary_folder,
                    num_embeddings=len(embeddings),
                    embeddings_metadata={'embedding_size': embeddings[0].shape[0] if embeddings else 0}
                )
                
                session.add(student)
                session.flush()  # Get student.id
                
                print(f"   ✅ Created database record (ID: {student.id})")
                
                # Upload images to Cloudinary
                images_dir = os.path.join(student_dir, 'images')
                if os.path.exists(images_dir):
                    image_files = [f for f in os.listdir(images_dir) if f.endswith('.jpg')]
                    
                    for idx, (image_file, embedding) in enumerate(zip(image_files, embeddings)):
                        image_path = os.path.join(images_dir, image_file)
                        
                        # Upload to Cloudinary
                        upload_result = cloudinary_manager.upload_image(
                            file_path=image_path,
                            folder=cloudinary_folder,
                            public_id=f"face_{idx}",
                            tags=['registration', student_id, 'migrated'],
                            context={'student_id': student_id, 'student_name': student_name}
                        )
                        
                        if upload_result:
                            # Save image record with embedding
                            student_image = StudentImage(
                                student_id=student.id,
                                image_url=upload_result['secure_url'],
                                public_id=upload_result['public_id'],
                                thumbnail_url=upload_result['thumbnail_url'],
                                embedding_vector=base64.b64encode(embedding.tobytes()).decode('utf-8')
                            )
                            session.add(student_image)
                            print(f"   ✅ Uploaded image {idx+1}/{len(image_files)} to Cloudinary")
                        else:
                            print(f"   ⚠️  Failed to upload image {idx+1}")
                
                # Commit transaction
                session.commit()
                
                print(f"   ✅ Migration complete for {student_name}")
                print()
                migrated_count += 1
                
            except Exception as e:
                print(f"   ❌ Failed to migrate {student_id}: {e}")
                session.rollback()
                skipped_count += 1
                import traceback
                traceback.print_exc()
                print()
        
        print("=" * 60)
        print("📊 Migration Summary")
        print("=" * 60)
        print(f"✅ Migrated: {migrated_count} students")
        print(f"⏭️  Skipped: {skipped_count} students")
        print(f"📁 Total: {len(student_dirs)} students")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()


def verify_migration():
    """Verify data was migrated successfully"""
    
    print()
    print("=" * 60)
    print("🔍 Verifying Migration")
    print("=" * 60)
    
    session = get_db_session()
    if not session:
        print("❌ Database connection failed")
        return
    
    try:
        # Count students
        student_count = session.query(Student).count()
        print(f"📊 Students in database: {student_count}")
        
        # List students
        students = session.query(Student).all()
        for student in students:
            image_count = session.query(StudentImage).filter_by(student_id=student.id).count()
            print(f"   - {student.student_name} ({student.student_id}): {image_count} images")
        
        print("=" * 60)
        print("✅ Verification complete")
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
    finally:
        session.close()


def main():
    """Main migration function"""
    
    print()
    print("🚀 EduSence AI - Data Migration to Cloud")
    print()
    
    # Check cloud availability
    from storage_manager import storage_manager
    
    if not storage_manager.is_cloud_enabled():
        print("❌ Cloud storage not available")
        print("   Please check your .env file and ensure:")
        print("   - DATABASE_URL is set")
        print("   - CLOUDINARY_* variables are set")
        print("   - Run: python3 test_cloud_setup.py")
        return 1
    
    print("✅ Cloud storage available")
    print()
    
    # Confirm migration
    response = input("⚠️  This will upload local data to cloud. Continue? (yes/no): ")
    if response.lower() != 'yes':
        print("❌ Migration cancelled")
        return 0
    
    print()
    
    # Migrate students
    migrate_registered_students()
    
    # Verify migration
    verify_migration()
    
    print()
    print("🎉 Migration complete!")
    print()
    print("Next steps:")
    print("1. Check Neon dashboard to see student data")
    print("2. Check Cloudinary dashboard to see uploaded images")
    print("3. Test student recognition: python3 integrated_server.py")
    print()
    
    return 0


if __name__ == '__main__':
    sys.exit(main())

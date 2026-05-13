"""
Cloudinary Manager for Cloud Storage
Handles image and video uploads to Cloudinary
"""

import os
import logging
import cloudinary
import cloudinary.uploader
import cloudinary.api
from dotenv import load_dotenv
from typing import Optional, Dict, List
import time

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class CloudinaryManager:
    """Manages Cloudinary uploads and operations"""
    
    def __init__(self):
        self.cloud_name = os.getenv('CLOUDINARY_CLOUD_NAME')
        self.api_key = os.getenv('CLOUDINARY_API_KEY')
        self.api_secret = os.getenv('CLOUDINARY_API_SECRET')
        
        self.initialized = False
        
        # Folder structure
        self.registered_students_folder = os.getenv('CLOUDINARY_REGISTERED_STUDENTS_FOLDER', 'edusence/registered_students')
        self.sessions_folder = os.getenv('CLOUDINARY_SESSIONS_FOLDER', 'edusence/sessions')
        self.uploads_folder = os.getenv('CLOUDINARY_UPLOADS_FOLDER', 'edusence/uploads')
        self.analytics_folder = os.getenv('CLOUDINARY_ANALYTICS_FOLDER', 'edusence/analytics')
        
        if not all([self.cloud_name, self.api_key, self.api_secret]):
            logger.warning("⚠️  Cloudinary credentials not set. Cloud storage disabled.")
            logger.warning("   Set CLOUDINARY_* variables in .env file to enable cloud storage.")
            return
        
        self._initialize_cloudinary()
    
    def _initialize_cloudinary(self):
        """Initialize Cloudinary configuration"""
        try:
            cloudinary.config(
                cloud_name=self.cloud_name,
                api_key=self.api_key,
                api_secret=self.api_secret,
                secure=True
            )
            
            # Test connection
            cloudinary.api.ping()
            
            self.initialized = True
            logger.info("✅ Cloudinary initialized successfully")
            logger.info(f"   Cloud Name: {self.cloud_name}")
            
        except Exception as e:
            logger.error(f"❌ Cloudinary initialization failed: {e}")
            logger.warning("   Application will run in local-only mode")
            self.initialized = False
    
    def is_available(self):
        """Check if Cloudinary is available"""
        return self.initialized
    
    def upload_image(
        self,
        file_path: str,
        folder: str,
        public_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        context: Optional[Dict] = None,
        transformation: Optional[Dict] = None
    ) -> Optional[Dict]:
        """
        Upload image to Cloudinary
        
        Args:
            file_path: Local file path
            folder: Cloudinary folder path
            public_id: Optional custom public ID
            tags: Optional list of tags
            context: Optional metadata context
            transformation: Optional transformation parameters
            
        Returns:
            Dict with upload result or None if failed
        """
        if not self.initialized:
            logger.error("❌ Cloudinary not initialized")
            return None
        
        try:
            start_time = time.time()
            
            upload_params = {
                'folder': folder,
                'resource_type': 'image',
                'overwrite': False,
                'unique_filename': True if not public_id else False,
            }
            
            if public_id:
                upload_params['public_id'] = public_id
            
            if tags:
                upload_params['tags'] = tags
            
            if context:
                upload_params['context'] = context
            
            if transformation:
                upload_params['transformation'] = transformation
            
            # Upload to Cloudinary
            result = cloudinary.uploader.upload(file_path, **upload_params)
            
            upload_time = (time.time() - start_time) * 1000
            
            logger.debug(f"✅ Image uploaded: {result['public_id']} ({upload_time:.1f}ms)")
            
            return {
                'public_id': result['public_id'],
                'secure_url': result['secure_url'],
                'url': result['url'],
                'format': result['format'],
                'width': result['width'],
                'height': result['height'],
                'bytes': result['bytes'],
                'created_at': result['created_at'],
                'thumbnail_url': self._generate_thumbnail_url(result['public_id']),
                'upload_time_ms': upload_time
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to upload image: {e}")
            return None
    
    def upload_video(
        self,
        file_path: str,
        folder: str,
        public_id: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Optional[Dict]:
        """
        Upload video to Cloudinary
        
        Args:
            file_path: Local file path
            folder: Cloudinary folder path
            public_id: Optional custom public ID
            tags: Optional list of tags
            
        Returns:
            Dict with upload result or None if failed
        """
        if not self.initialized:
            logger.error("❌ Cloudinary not initialized")
            return None
        
        try:
            start_time = time.time()
            
            upload_params = {
                'folder': folder,
                'resource_type': 'video',
                'overwrite': False,
                'unique_filename': True if not public_id else False,
            }
            
            if public_id:
                upload_params['public_id'] = public_id
            
            if tags:
                upload_params['tags'] = tags
            
            # Upload to Cloudinary
            result = cloudinary.uploader.upload(file_path, **upload_params)
            
            upload_time = (time.time() - start_time) * 1000
            
            logger.info(f"✅ Video uploaded: {result['public_id']} ({upload_time:.1f}ms)")
            
            return {
                'public_id': result['public_id'],
                'secure_url': result['secure_url'],
                'url': result['url'],
                'format': result['format'],
                'duration': result.get('duration'),
                'width': result.get('width'),
                'height': result.get('height'),
                'bytes': result['bytes'],
                'created_at': result['created_at'],
                'thumbnail_url': self._generate_video_thumbnail_url(result['public_id']),
                'upload_time_ms': upload_time
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to upload video: {e}")
            return None
    
    def delete_resource(self, public_id: str, resource_type: str = 'image') -> bool:
        """
        Delete resource from Cloudinary
        
        Args:
            public_id: Cloudinary public ID
            resource_type: 'image' or 'video'
            
        Returns:
            True if successful, False otherwise
        """
        if not self.initialized:
            return False
        
        try:
            result = cloudinary.uploader.destroy(public_id, resource_type=resource_type)
            
            if result.get('result') == 'ok':
                logger.debug(f"✅ Resource deleted: {public_id}")
                return True
            else:
                logger.warning(f"⚠️  Failed to delete resource: {public_id}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error deleting resource: {e}")
            return False
    
    def delete_folder(self, folder_path: str) -> bool:
        """
        Delete entire folder from Cloudinary
        
        Args:
            folder_path: Cloudinary folder path
            
        Returns:
            True if successful, False otherwise
        """
        if not self.initialized:
            return False
        
        try:
            # Delete all resources in folder
            cloudinary.api.delete_resources_by_prefix(folder_path)
            
            # Delete folder
            cloudinary.api.delete_folder(folder_path)
            
            logger.info(f"✅ Folder deleted: {folder_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error deleting folder: {e}")
            return False
    
    def _generate_thumbnail_url(self, public_id: str, width: int = 200, height: int = 200) -> str:
        """Generate thumbnail URL for image"""
        return cloudinary.CloudinaryImage(public_id).build_url(
            width=width,
            height=height,
            crop='fill',
            quality='auto',
            fetch_format='auto'
        )
    
    def _generate_video_thumbnail_url(self, public_id: str, width: int = 200, height: int = 200) -> str:
        """Generate thumbnail URL for video"""
        return cloudinary.CloudinaryVideo(public_id).build_url(
            width=width,
            height=height,
            crop='fill',
            quality='auto',
            format='jpg',
            start_offset='0'
        )
    
    def get_folder_path(self, folder_type: str, *args) -> str:
        """
        Get Cloudinary folder path
        
        Args:
            folder_type: 'registered_students', 'sessions', 'uploads', 'analytics'
            *args: Additional path components
            
        Returns:
            Full folder path
        """
        base_folders = {
            'registered_students': self.registered_students_folder,
            'sessions': self.sessions_folder,
            'uploads': self.uploads_folder,
            'analytics': self.analytics_folder
        }
        
        base = base_folders.get(folder_type, 'edusence')
        
        if args:
            return f"{base}/{'/'.join(str(arg) for arg in args)}"
        
        return base
    
    def list_resources(self, folder: str, resource_type: str = 'image', max_results: int = 100) -> List[Dict]:
        """
        List resources in a folder
        
        Args:
            folder: Cloudinary folder path
            resource_type: 'image' or 'video'
            max_results: Maximum number of results
            
        Returns:
            List of resource dictionaries
        """
        if not self.initialized:
            return []
        
        try:
            result = cloudinary.api.resources(
                type='upload',
                resource_type=resource_type,
                prefix=folder,
                max_results=max_results
            )
            
            return result.get('resources', [])
            
        except Exception as e:
            logger.error(f"❌ Error listing resources: {e}")
            return []
    
    def get_usage_stats(self) -> Optional[Dict]:
        """Get Cloudinary usage statistics"""
        if not self.initialized:
            return None
        
        try:
            result = cloudinary.api.usage()
            return {
                'credits_used': result.get('credits', {}).get('used', 0),
                'credits_limit': result.get('credits', {}).get('limit', 0),
                'storage_used_mb': result.get('storage', {}).get('used', 0) / (1024 * 1024),
                'bandwidth_used_mb': result.get('bandwidth', {}).get('used', 0) / (1024 * 1024),
            }
        except Exception as e:
            logger.error(f"❌ Error getting usage stats: {e}")
            return None


# Global Cloudinary manager instance
cloudinary_manager = CloudinaryManager()


def get_cloudinary_manager() -> CloudinaryManager:
    """Get Cloudinary manager instance"""
    return cloudinary_manager

"""
Main application for classroom face detection and tracking system
Phase 1: Detection, Tracking, and Image Saving
"""

import cv2
import sys
import argparse
from pathlib import Path
import time

from face_detector import FaceDetector
from image_manager import ImageManager
from video_processor import VideoProcessor
from face_reid import FaceReID
import config


class ClassroomTrackingSystem:
    """
    Main system for classroom face detection and tracking
    """
    
    def __init__(self, video_source=0, output_dir=None):
        """
        Initialize the tracking system
        
        Args:
            video_source: Video source (0 for webcam, or path to video file)
            output_dir: Directory for saving student images
        """
        self.video_source = video_source
        self.output_dir = output_dir or config.OUTPUT_DIR
        
        # Initialize components
        print("=" * 60)
        print("🎓 CLASSROOM FACE DETECTION AND TRACKING SYSTEM")
        print("=" * 60)
        
        self.detector = None
        self.image_manager = None
        self.video_processor = None
        self.reid_system = None
        
        # Frame counter for tracking
        self.frame_number = 0
        
        # Track active track IDs
        self.active_tracks = set()
        
        self._initialize_components()
    
    def _initialize_components(self):
        """
        Initialize all system components including ReID
        """
        try:
            # Initialize face detector
            print("\n📦 Initializing components...")
            self.detector = FaceDetector()
            
            # Initialize image manager
            self.image_manager = ImageManager(self.output_dir)
            
            # Initialize video processor
            self.video_processor = VideoProcessor(self.video_source)
            
            # Initialize ReID system if enabled
            if config.ENABLE_REID:
                print("\n🔄 Initializing Face Re-Identification system...")
                self.reid_system = FaceReID(
                    similarity_threshold=config.REID_SIMILARITY_THRESHOLD,
                    embedding_size=512
                )
            else:
                print("\n⚠️  Face ReID disabled in config")
                self.reid_system = None
            
            print("✅ All components initialized successfully\n")
            
        except Exception as e:
            print(f"❌ Initialization failed: {str(e)}")
            sys.exit(1)
    
    def process_frame(self, frame):
        """
        Process a single frame: detect, track, ReID, and save faces
        With strict validation for face-only detection and stable IDs
        
        Args:
            frame: Input frame
            
        Returns:
            Annotated frame
        """
        self.frame_number += 1
        current_time = time.time()
        
        # Enable debug for first 50 frames to catch initial detections
        debug = self.frame_number <= 50
        
        if debug:
            print(f"\n{'='*60}")
            print(f"🔍 DEBUG FRAME {self.frame_number}")
            print(f"{'='*60}")
        
        # Track faces with ByteTrack
        detections = self.detector.track_faces(frame, self.frame_number, debug=debug)
        
        if debug:
            print(f"🔍 DEBUG: Detections from tracker: {len(detections)}")
        
        # Track current frame's track IDs
        current_tracks = set()
        
        # Process each detection with ReID
        reid_detections = []
        validation_failed = 0
        crop_failed = 0
        
        for detection in detections:
            x1, y1, x2, y2, track_id, confidence, track_age = detection
            current_tracks.add(track_id)
            
            # Validate detection
            bbox = (x1, y1, x2, y2)
            if not self.detector.is_valid_face_detection(bbox, confidence):
                validation_failed += 1
                if debug:
                    print(f"   ❌ Validation failed for Track {track_id}")
                continue
            
            # Crop face for ReID
            face_crop = self.image_manager.crop_face(frame, bbox)
            
            if face_crop is None:
                crop_failed += 1
                if debug:
                    print(f"   ❌ Crop failed for Track {track_id}")
                continue
            
            # Apply ReID if enabled
            if self.reid_system and config.ENABLE_REID:
                # Determine if we should extract embedding
                should_extract = self.reid_system.should_extract_embedding(
                    track_id, track_age, confidence
                )
                
                # Register or match face
                student_id, is_new, similarity = self.reid_system.register_or_match_face(
                    track_id, face_crop, current_time, force_extract=should_extract
                )
                
                # Log ReID events
                if is_new and track_age == 0:
                    print(f"✨ New student: Student {student_id} (Track {track_id})")
                elif similarity > 0 and similarity < 1.0:
                    print(f"🔄 ReID match: Track {track_id} → Student {student_id} (sim: {similarity:.3f})")
            else:
                # No ReID, use track ID as student ID
                student_id = track_id
            
            # Save face crop with student ID
            saved = self.image_manager.save_face_image(
                frame, bbox, student_id, confidence
            )
            
            if saved and debug:
                print(f"💾 Saved: Student {student_id} (Track {track_id}, conf: {confidence:.2f})")
            
            # Store detection with student ID for display
            reid_detections.append((x1, y1, x2, y2, student_id, confidence))
            
            if debug:
                print(f"   ✅ Added to display list: Student {student_id}, Track {track_id}, bbox:({x1},{y1},{x2},{y2}), conf:{confidence:.2f}")
        
        if debug:
            print(f"🔍 DEBUG: Final detections for display: {len(reid_detections)}")
            print(f"   Validation failed: {validation_failed}")
            print(f"   Crop failed: {crop_failed}")
        
        # Handle lost tracks
        if self.reid_system and config.ENABLE_REID:
            lost_tracks = self.active_tracks - current_tracks
            for lost_track in lost_tracks:
                self.reid_system.handle_track_lost(lost_track)
            
            # Cleanup old tracks periodically
            if self.frame_number % 100 == 0:
                self.reid_system.cleanup_old_tracks(current_time, timeout=30.0)
        
        self.active_tracks = current_tracks
        
        # Draw detections with student IDs
        if debug:
            print(f"🔍 DEBUG: Drawing {len(reid_detections)} detections on frame")
        
        annotated_frame = self.video_processor.draw_detections(frame, reid_detections)
        
        # Draw debug overlay
        if debug or self.frame_number % 30 == 0:  # Show debug info periodically
            annotated_frame = self._draw_debug_overlay(
                annotated_frame, 
                len(detections), 
                len(reid_detections),
                len(current_tracks)
            )
        
        # Draw FPS
        annotated_frame = self.video_processor.draw_fps(annotated_frame)
        
        # Draw info
        stats = self.image_manager.get_statistics()
        annotated_frame = self.video_processor.draw_info(
            annotated_frame,
            stats['total_students'],
            stats['total_images']
        )
        
        return annotated_frame
    
    def _draw_debug_overlay(self, frame, yolo_count, reid_count, track_count):
        """
        Draw debug information overlay on frame
        
        Args:
            frame: Input frame
            yolo_count: Number of YOLO detections
            reid_count: Number of ReID detections
            track_count: Number of active tracks
            
        Returns:
            Frame with debug overlay
        """
        import cv2
        
        # Draw semi-transparent background
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 90), (350, 200), (0, 0, 0), -1)
        frame = cv2.addWeighted(overlay, 0.3, frame, 0.7, 0)
        
        # Draw debug text
        y_pos = 110
        cv2.putText(frame, f"YOLO Detections: {yolo_count}", (15, y_pos), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        y_pos += 25
        cv2.putText(frame, f"Tracker Output: {yolo_count}", (15, y_pos), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        
        y_pos += 25
        cv2.putText(frame, f"Active Tracks: {track_count}", (15, y_pos), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        
        y_pos += 25
        cv2.putText(frame, f"ReID Matches: {reid_count}", (15, y_pos), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 255), 2)
        
        return frame
    
    def run(self):
        """
        Main processing loop
        """
        print("🚀 Starting face detection and tracking...")
        print("📹 Press 'q' to quit, 's' to show statistics\n")
        
        try:
            while True:
                # Read frame
                ret, frame = self.video_processor.read_frame()
                
                if not ret:
                    print("⚠️  End of video or failed to read frame")
                    break
                
                # Process frame
                annotated_frame = self.process_frame(frame)
                
                # Display frame
                self.video_processor.display_frame(annotated_frame)
                
                # Handle keyboard input
                key = cv2.waitKey(1) & 0xFF
                
                if key == ord('q'):
                    print("\n🛑 Stopping system...")
                    break
                elif key == ord('s'):
                    self._print_statistics()
        
        except KeyboardInterrupt:
            print("\n⚠️  Interrupted by user")
        
        except Exception as e:
            print(f"\n❌ Error during processing: {str(e)}")
        
        finally:
            self._cleanup()
    
    def _print_statistics(self):
        """
        Print current statistics including ReID stats
        """
        print("\n" + "=" * 60)
        print("📊 STATISTICS")
        print("=" * 60)
        
        stats = self.image_manager.get_statistics()
        
        print(f"Total Students Tracked: {stats['total_students']}")
        print(f"Total Images Saved: {stats['total_images']}")
        print(f"Current FPS: {self.video_processor.get_fps():.1f}")
        print(f"Frame Number: {self.frame_number}")
        
        if stats['students']:
            print("\nPer-Student Image Count:")
            for student_id, count in sorted(stats['students'].items(), key=lambda x: int(x[0]) if x[0].isdigit() else 0):
                print(f"  Student {student_id}: {count} images")
        
        # Print ReID statistics if enabled
        if self.reid_system and config.ENABLE_REID:
            print("\n" + "-" * 60)
            print("🔍 FACE RE-IDENTIFICATION STATISTICS")
            print("-" * 60)
            reid_stats = self.reid_system.get_statistics()
            print(f"Total Unique Students: {reid_stats['total_students']}")
            print(f"Active Tracks: {reid_stats['active_tracks']}")
            print(f"Embeddings Extracted: {reid_stats['embeddings_extracted']}")
            print(f"Successful Matches: {reid_stats['successful_matches']}")
            print(f"New Students Detected: {reid_stats['new_students_detected']}")
            print(f"Cached Embeddings: {reid_stats['cached_embeddings']}")
        
        print("=" * 60 + "\n")
    
    def _cleanup(self):
        """
        Cleanup resources
        """
        print("\n🧹 Cleaning up...")
        
        if self.video_processor:
            self.video_processor.release()
        
        # Print final statistics
        self._print_statistics()
        
        print("✅ System stopped successfully")


def parse_arguments():
    """
    Parse command line arguments
    
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Classroom Face Detection and Tracking System - Phase 1"
    )
    
    parser.add_argument(
        '--source',
        type=str,
        default='0',
        help='Video source: 0 for webcam, or path to video file (default: 0)'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default=config.OUTPUT_DIR,
        help=f'Output directory for student images (default: {config.OUTPUT_DIR})'
    )
    
    parser.add_argument(
        '--confidence',
        type=float,
        default=config.CONFIDENCE_THRESHOLD,
        help=f'Confidence threshold for detection (default: {config.CONFIDENCE_THRESHOLD})'
    )
    
    parser.add_argument(
        '--device',
        type=str,
        default=config.DEVICE,
        help=f'Device for inference: cuda:0 or cpu (default: {config.DEVICE})'
    )
    
    return parser.parse_args()


def main():
    """
    Main entry point
    """
    # Parse arguments
    args = parse_arguments()
    
    # Update config with command line arguments
    config.CONFIDENCE_THRESHOLD = args.confidence
    config.DEVICE = args.device
    
    # Convert source to int if it's a digit
    video_source = int(args.source) if args.source.isdigit() else args.source
    
    # Validate video file if not webcam
    if not isinstance(video_source, int):
        if not Path(video_source).exists():
            print(f"❌ Error: Video file not found: {video_source}")
            sys.exit(1)
    
    # Create and run system
    system = ClassroomTrackingSystem(
        video_source=video_source,
        output_dir=args.output
    )
    
    system.run()


if __name__ == "__main__":
    main()

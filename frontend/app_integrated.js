// API Configuration
const API_BASE_URL = window.location.origin;

/**
 * Get or create browser-specific session ID
 */
function getBrowserSessionId() {
    let sessionId = localStorage.getItem('browser_session_id');
    if (!sessionId) {
        sessionId = crypto.randomUUID();
        localStorage.setItem('browser_session_id', sessionId);
        console.log('🆔 Generated new browser session ID:', sessionId);
    }
    return sessionId;
}

// Initialize browser session ID
const BROWSER_SESSION_ID = getBrowserSessionId();
console.log('🆔 Browser Session ID:', BROWSER_SESSION_ID);

/**
 * Helper function to safely parse JSON responses
 * Checks content-type and provides clear error messages
 */
async function safeJsonResponse(response) {
    const contentType = response.headers.get('content-type');
    
    if (!contentType || !contentType.includes('application/json')) {
        const text = await response.text();
        console.error('Non-JSON response:', text.substring(0, 500));
        throw new Error('Server returned HTML instead of JSON. Check if the server is running correctly.');
    }
    
    return await response.json();
}

/**
 * Enhanced fetch with session ID header
 */
async function fetchWithSession(url, options = {}) {
    options.headers = options.headers || {};
    options.headers['X-Session-ID'] = BROWSER_SESSION_ID;
    options.headers['X-Browser-Session'] = BROWSER_SESSION_ID;
    return fetch(url, options);
}

// DOM Elements
const startCameraBtn = document.getElementById('startCameraBtn');
const stopCameraBtn = document.getElementById('stopCameraBtn');
const uploadVideoBtn = document.getElementById('uploadVideoBtn');
const analyzeBtn = document.getElementById('analyzeBtn');
const videoFeed = document.getElementById('videoFeed'); // Video element for client-side webcam
const videoFeedImg = document.getElementById('videoFeedImg'); // Img element for server-side stream
const videoCanvas = document.getElementById('videoCanvas'); // Canvas for drawing detections
const videoPlaceholder = document.getElementById('videoPlaceholder');
const videoStats = document.getElementById('videoStats');
const videoProgress = document.getElementById('videoProgress');
const videoSectionTitle = document.getElementById('videoSectionTitle');
const loadingState = document.getElementById('loadingState');
const emptyState = document.getElementById('emptyState');
const dashboardContent = document.getElementById('dashboardContent');
const studentGrid = document.getElementById('studentGrid');
const progressFill = document.getElementById('progressFill');
const progressText = document.getElementById('progressText');

// Upload Modal Elements
const uploadModal = document.getElementById('uploadModal');
const closeModalBtn = document.getElementById('closeModalBtn');
const uploadArea = document.getElementById('uploadArea');
const videoFileInput = document.getElementById('videoFileInput');
const browseBtn = document.getElementById('browseBtn');
const uploadProgress = document.getElementById('uploadProgress');
const uploadSuccess = document.getElementById('uploadSuccess');
const startProcessingBtn = document.getElementById('startProcessingBtn');
const uploadProgressFill = document.getElementById('uploadProgressFill');
const uploadProgressText = document.getElementById('uploadProgressText');
const uploadFileName = document.getElementById('uploadFileName');
const uploadFileSize = document.getElementById('uploadFileSize');

// State
let cameraRunning = false;
let videoProcessing = false;
let statsInterval = null;
let isAnalyzing = false;
let currentSessionId = null;
let uploadedVideoPath = null;
let sourceType = null; // 'webcam' or 'video'
let localStream = null; // MediaStream for client-side webcam
let frameProcessingInterval = null; // Interval for sending frames to server
let videoElement = null; // Video element reference
let canvasElement = null; // Canvas element reference
let canvasContext = null; // Canvas 2D context

// MODE FIX: detection overlay state
let lastDetections = []; // most recent detections from server, redrawn every rAF tick
let overlayAnimationId = null; // requestAnimationFrame handle for continuous overlay

// Debug function - can be called from browser console
window.debugUploadState = function() {
    console.log('═══════════════════════════════════════════════════════');
    console.log('DEBUG: UPLOAD STATE');
    console.log('═══════════════════════════════════════════════════════');
    console.log('uploadedVideoPath:', uploadedVideoPath);
    console.log('Type:', typeof uploadedVideoPath);
    console.log('Value:', uploadedVideoPath);
    console.log('Is null?', uploadedVideoPath === null);
    console.log('Is undefined?', uploadedVideoPath === undefined);
    console.log('Truthy?', !!uploadedVideoPath);
    console.log('═══════════════════════════════════════════════════════');
    return uploadedVideoPath;
};

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    // Set up event listeners
    startCameraBtn.addEventListener('click', startCamera);
    stopCameraBtn.addEventListener('click', stopCamera);
    uploadVideoBtn.addEventListener('click', openUploadModal);
    analyzeBtn.addEventListener('click', analyzeClassroom);
    
    // Upload modal listeners
    closeModalBtn.addEventListener('click', closeUploadModal);
    browseBtn.addEventListener('click', () => videoFileInput.click());
    videoFileInput.addEventListener('change', handleFileSelect);
    startProcessingBtn.addEventListener('click', startVideoProcessing);
    
    // Drag and drop
    uploadArea.addEventListener('dragover', handleDragOver);
    uploadArea.addEventListener('dragleave', handleDragLeave);
    uploadArea.addEventListener('drop', handleDrop);
    uploadArea.addEventListener('click', () => videoFileInput.click());
    
    // Close modal on outside click
    uploadModal.addEventListener('click', (e) => {
        if (e.target === uploadModal) {
            closeUploadModal();
        }
    });
    
    // Check initial camera status
    checkCameraStatus();
    
    // Show empty state initially
    emptyState.style.display = 'block';
});

/**
 * Reset dashboard for new session
 */
function resetDashboard() {
    console.log('🔄 Resetting dashboard for new session');
    
    // Hide analytics dashboard
    dashboardContent.style.display = 'none';
    
    // Show empty state
    emptyState.style.display = 'block';
    
    // Clear student grid
    studentGrid.innerHTML = '';
    
    // Reset summary cards
    document.getElementById('totalStudents').textContent = '0';
    document.getElementById('focusedStudents').textContent = '0';
    document.getElementById('distractedStudents').textContent = '0';
    document.getElementById('avgEngagement').textContent = '0%';
    
    // Reset distribution bars
    document.getElementById('focusedBar').style.width = '0%';
    document.getElementById('focusedPercent').textContent = '0%';
    document.getElementById('neutralBar').style.width = '0%';
    document.getElementById('neutralPercent').textContent = '0%';
    document.getElementById('distractedBar').style.width = '0%';
    document.getElementById('distractedPercent').textContent = '0%';
    
    console.log('✅ Dashboard reset complete');
}

/**
 * Start camera - Client-side webcam access
 */
async function startCamera() {
    try {
        console.log('═══════════════════════════════════════════════════════');
        console.log('🎥 STARTING CLIENT-SIDE WEBCAM');
        console.log('═══════════════════════════════════════════════════════');
        
        startCameraBtn.disabled = true;
        
        // Reset dashboard for new session
        resetDashboard();
        
        // Request webcam access from browser
        console.log('📹 Requesting webcam access...');
        localStream = await navigator.mediaDevices.getUserMedia({ 
            video: { 
                width: { ideal: 1280 },
                height: { ideal: 720 }
            } 
        });
        
        console.log('✅ Webcam access granted');
        console.log('Stream tracks:', localStream.getTracks().length);
        
        // Create session on server
        const response = await fetchWithSession('/api/camera/start', {
            method: 'POST'
        });
        
        const data = await safeJsonResponse(response);
        
        if (!data.success) {
            throw new Error(data.message || 'Failed to create session');
        }
        
        console.log('✅ Server session created:', data.session_id);
        
        cameraRunning = true;
        currentSessionId = data.session_id;
        sourceType = 'webcam';
        
        // Setup video element
        videoElement = videoFeed;
        videoElement.srcObject = localStream;
        
        console.log('📺 Video srcObject set');
        
        // Setup canvas for drawing detections
        canvasElement = videoCanvas;
        canvasContext = canvasElement.getContext('2d');
        
        // Wait for video to be ready and play it
        await new Promise((resolve, reject) => {
            videoElement.onloadedmetadata = async () => {
                try {
                    console.log('📺 Video metadata loaded');
                    console.log(`📺 Video dimensions: ${videoElement.videoWidth}x${videoElement.videoHeight}`);
                    
                    // Play the video
                    await videoElement.play();
                    console.log('▶️  Video playing');
                    
                    // Set canvas size to match video
                    canvasElement.width = videoElement.videoWidth;
                    canvasElement.height = videoElement.videoHeight;
                    console.log(`🎨 Canvas size: ${canvasElement.width}x${canvasElement.height}`);
                    
                    resolve();
                } catch (err) {
                    reject(err);
                }
            };
            
            videoElement.onerror = (err) => {
                reject(new Error('Video element error: ' + err));
            };
        });
        
        // Update UI
        startCameraBtn.style.display = 'none';
        stopCameraBtn.style.display = 'inline-flex';
        videoPlaceholder.style.display = 'none';
        videoElement.style.display = 'block';
        canvasElement.style.display = 'block';
        videoStats.style.display = 'flex';

        // MODE FIX: hide and reset the video-progress bar — it belongs to video mode only
        if (videoProgress) {
            videoProgress.style.display = 'none';
            document.getElementById('progressFrames').textContent = 'Frame 0 / 0';
            document.getElementById('progressPercent').textContent = '0%';
            document.getElementById('videoProgressFill').style.width = '0%';
        }

        console.log('✅ UI updated');

        // MODE FIX: start continuous rAF overlay loop before frame processing
        startDetectionOverlay();

        // Start frame processing
        startFrameProcessing();

        // Start stats polling
        startStatsPolling();
        
        console.log('✅ Local webcam started successfully');
        showNotification(`Webcam started: ${data.session_id}`, 'success');
        
    } catch (error) {
        console.error('═══════════════════════════════════════════════════════');
        console.error('❌ START CAMERA ERROR');
        console.error('═══════════════════════════════════════════════════════');
        console.error('Error:', error);
        console.error('═══════════════════════════════════════════════════════');
        
        // Cleanup on error
        if (localStream) {
            localStream.getTracks().forEach(track => track.stop());
            localStream = null;
        }
        
        alert(`Failed to start camera: ${error.message}`);
    } finally {
        startCameraBtn.disabled = false;
    }
}

/**
 * Start processing frames from client-side webcam.
 * MODE FIX: uses a hidden offscreen canvas to capture frames so the visible
 * canvasElement stays as a pure transparent detection overlay.
 */
function startFrameProcessing() {
    if (frameProcessingInterval) {
        clearInterval(frameProcessingInterval);
    }

    // Hidden canvas used only to serialise the video frame for the server.
    // Never inserted into the DOM — keeps the display canvas transparent.
    const captureCanvas = document.createElement('canvas');
    const captureCtx = captureCanvas.getContext('2d');

    let frameCount = 0;

    frameProcessingInterval = setInterval(async () => {
        if (!cameraRunning || !videoElement || !canvasElement) return;

        if (videoElement.videoWidth === 0 || videoElement.videoHeight === 0) return;

        try {
            frameCount++;

            // Sync capture canvas size to video (only when dimensions change)
            if (captureCanvas.width !== videoElement.videoWidth) {
                captureCanvas.width  = videoElement.videoWidth;
                captureCanvas.height = videoElement.videoHeight;
            }

            // Draw current frame into the HIDDEN capture canvas
            captureCtx.drawImage(videoElement, 0, 0, captureCanvas.width, captureCanvas.height);

            const blob = await new Promise(resolve =>
                captureCanvas.toBlob(resolve, 'image/jpeg', 0.8)
            );

            if (!blob) return;

            if (frameCount % 10 === 0) {
                console.log(`📤 Frame ${frameCount} (${(blob.size / 1024).toFixed(1)} KB)`);
            }

            const formData = new FormData();
            formData.append('frame', blob, 'frame.jpg');
            formData.append('session_id', currentSessionId);

            const response = await fetchWithSession('/api/process_frame', {
                method: 'POST',
                body: formData
            });

            const data = await safeJsonResponse(response);

            if (data.success && data.detections) {
                // MODE FIX: store detections so the rAF overlay loop can redraw them
                lastDetections = data.detections;
                // Update face counter immediately from the live detection result
                document.getElementById('statFaces').textContent = data.detections.length;
            } else {
                lastDetections = [];
                document.getElementById('statFaces').textContent = '0';
            }

        } catch (error) {
            console.error('❌ Frame processing error:', error);
        }
    }, 400);

    console.log('✅ Frame processing started (400ms interval, offscreen capture canvas)');
}

/**
 * Draw detection boxes and labels on the transparent overlay canvas.
 * MODE FIX: does NOT draw the video frame — the <video> element shows through
 * underneath.  Removing the video redraw eliminates the stale-frame flicker
 * and keeps the live feed visible between 400 ms detection updates.
 */
function drawDetections(detections) {
    if (!canvasContext || !canvasElement) return;

    // Clear to fully transparent — live video shows through beneath
    canvasContext.clearRect(0, 0, canvasElement.width, canvasElement.height);

    detections.forEach(detection => {
        const { bbox, name, confidence, is_registered } = detection;
        const [x, y, w, h] = bbox;

        const color = is_registered ? '#00ff00' : '#ff9800';

        // Bounding box
        canvasContext.strokeStyle = color;
        canvasContext.lineWidth = 3;
        canvasContext.strokeRect(x, y, w, h);

        // Label
        const label = is_registered
            ? `${name} (${(confidence * 100).toFixed(0)}%)`
            : 'Unknown';
        canvasContext.font = 'bold 15px Arial';
        const textWidth = canvasContext.measureText(label).width;

        canvasContext.fillStyle = color;
        canvasContext.fillRect(x, y - 26, textWidth + 10, 26);

        canvasContext.fillStyle = '#000000';
        canvasContext.fillText(label, x + 5, y - 7);
    });
}

/**
 * MODE FIX: requestAnimationFrame loop that redraws lastDetections at display
 * refresh rate.  Detections stay visible continuously between 400 ms server
 * updates instead of vanishing as soon as the canvas is cleared.
 */
function startDetectionOverlay() {
    stopDetectionOverlay(); // cancel any previous loop

    function renderFrame() {
        if (!cameraRunning) return; // exit loop when camera stops
        drawDetections(lastDetections);
        overlayAnimationId = requestAnimationFrame(renderFrame);
    }

    overlayAnimationId = requestAnimationFrame(renderFrame);
    console.log('✅ Detection overlay loop started');
}

function stopDetectionOverlay() {
    if (overlayAnimationId !== null) {
        cancelAnimationFrame(overlayAnimationId);
        overlayAnimationId = null;
    }
    lastDetections = [];
    if (canvasContext && canvasElement) {
        canvasContext.clearRect(0, 0, canvasElement.width, canvasElement.height);
    }
}

/**
 * Stop camera
 */
async function stopCamera() {
    try {
        console.log('🛑 Stopping camera...');
        stopCameraBtn.disabled = true;
        
        // Stop frame processing
        if (frameProcessingInterval) {
            clearInterval(frameProcessingInterval);
            frameProcessingInterval = null;
        }

        // MODE FIX: stop rAF overlay loop and clear detections
        stopDetectionOverlay();

        // Stop local webcam stream
        if (localStream) {
            localStream.getTracks().forEach(track => track.stop());
            localStream = null;
        }
        
        // Notify server with session_id
        const response = await fetchWithSession('/api/camera/stop', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                session_id: currentSessionId
            })
        });
        
        const data = await safeJsonResponse(response);
        
        if (data.success) {
            console.log('✅ Camera stopped');
            cameraRunning = false;
            currentSessionId = null;
            
            // Update UI
            startCameraBtn.style.display = 'inline-flex';
            stopCameraBtn.style.display = 'none';
            videoPlaceholder.style.display = 'flex';
            videoFeed.style.display = 'none';
            videoCanvas.style.display = 'none';
            videoStats.style.display = 'none';
            
            // Clear canvas
            if (canvasContext) {
                canvasContext.clearRect(0, 0, canvasElement.width, canvasElement.height);
            }
            
            // Stop stats polling
            stopStatsPolling();
            
            // Reset stats display
            document.getElementById('statFps').textContent = '0';
            document.getElementById('statFaces').textContent = '0';
            document.getElementById('statStudents').textContent = '0';
            document.getElementById('statImages').textContent = '0';
            
            // Show success message
            showNotification('Camera stopped - session data preserved', 'info');
        }
        
    } catch (error) {
        console.error('❌ Stop camera error:', error);
        alert(`Failed to stop camera: ${error.message}`);
    } finally {
        stopCameraBtn.disabled = false;
    }
}

/**
 * Check camera status
 */
async function checkCameraStatus() {
    try {
        const response = await fetch('/api/camera/status');
        const data = await response.json();
        
        if (data.success && data.status.running) {
            // Camera is already running (server-side video processing)
            // Only restore UI for video file processing, NOT for client-side webcam
            if (data.status.is_video_file) {
                cameraRunning = true;
                videoProcessing = true;
                sourceType = 'video';
                startCameraBtn.style.display = 'none';
                stopCameraBtn.style.display = 'inline-flex';
                videoPlaceholder.style.display = 'none';
                videoFeedImg.style.display = 'block';
                videoStats.style.display = 'flex';
                // Use relative path for video feed (server-side only)
                videoFeedImg.src = `/api/video_feed?t=${Date.now()}`;
                startStatsPolling();
            }
            // If it's webcam mode, user needs to start their own webcam
        }
    } catch (error) {
        console.log('Camera status check failed:', error);
    }
}

/**
 * Start polling camera stats.
 * MODE FIX: uses stats.mode to decide what to display.
 * - 'video'  → show frame progress bar, hide it only when done
 * - 'camera' → hide progress bar; face count comes from frame processing directly
 * - 'idle'   → hide progress bar
 */
function startStatsPolling() {
    if (statsInterval) {
        clearInterval(statsInterval);
    }

    statsInterval = setInterval(async () => {
        try {
            const response = await fetch('/api/camera/status');
            const data = await safeJsonResponse(response);

            if (!data.success || !data.status) return;
            const stats = data.status;

            if (stats.mode === 'video') {
                // ── Video processing mode ─────────────────────────────────
                document.getElementById('statFps').textContent =
                    (stats.fps || 0).toFixed(1);
                document.getElementById('statFaces').textContent =
                    stats.active_tracks || 0;
                document.getElementById('statStudents').textContent =
                    stats.total_students || 0;
                document.getElementById('statImages').textContent =
                    stats.total_images || 0;

                // Show and update the frame progress bar
                if (videoProgress) {
                    videoProgress.style.display = 'block';
                    document.getElementById('progressFrames').textContent =
                        `Frame ${stats.current_frame} / ${stats.total_frames}`;
                    document.getElementById('progressPercent').textContent =
                        `${Math.round(stats.progress)}%`;
                    document.getElementById('videoProgressFill').style.width =
                        `${stats.progress}%`;
                }

                if (stats.processing_complete) {
                    showNotification('Video processing complete!', 'success');
                    stopStatsPolling();
                    videoProcessing = false;
                    stopCameraBtn.style.display = 'none';
                    analyzeBtn.disabled = false;
                }

            } else if (stats.mode === 'camera') {
                // ── Live webcam mode ──────────────────────────────────────
                // Hide the progress bar — it belongs to video mode only.
                if (videoProgress) videoProgress.style.display = 'none';

                // WEBCAM RECOGNITION FIX: server now returns aggregated
                // students / images_saved counts from SessionProcessor.get_stats().
                // Face count is still updated directly from frame responses (faster).
                document.getElementById('statStudents').textContent =
                    stats.students || 0;
                document.getElementById('statImages').textContent =
                    stats.images_saved || 0;

            } else {
                // ── Idle mode ─────────────────────────────────────────────
                if (videoProgress) videoProgress.style.display = 'none';
            }

        } catch (error) {
            console.error('Stats polling error:', error);
        }
    }, 1000);
}

/**
 * Stop polling camera stats
 */
function stopStatsPolling() {
    if (statsInterval) {
        clearInterval(statsInterval);
        statsInterval = null;
    }
}

/**
 * Analyze classroom engagement
 */
async function analyzeClassroom() {
    if (isAnalyzing) return;
    
    isAnalyzing = true;
    analyzeBtn.disabled = true;
    
    // Show loading state
    emptyState.style.display = 'none';
    dashboardContent.style.display = 'none';
    loadingState.style.display = 'block';
    
    // Simulate progress
    simulateProgress();
    
    try {
        console.log('🔍 Starting analysis...');
        
        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        console.log('Response status:', response.status);
        
        if (!response.ok) {
            const errorData = await safeJsonResponse(response);
            console.error('API Error:', errorData);
            throw new Error(errorData.message || errorData.error || 'Analysis failed');
        }
        
        const data = await safeJsonResponse(response);
        console.log('Analysis result:', data);
        
        if (data.success) {
            // Complete progress
            updateProgress(100);
            
            // Wait a bit for visual effect
            await new Promise(resolve => setTimeout(resolve, 500));
            
            // Display results
            displayResults(data);
            
            showNotification('Analysis complete!', 'success');
        } else {
            throw new Error(data.error || 'Analysis failed');
        }
        
    } catch (error) {
        console.error('Analysis error:', error);
        
        let errorMessage = 'Failed to analyze classroom. ';
        
        if (error.message.includes('Failed to fetch')) {
            errorMessage += 'Cannot connect to server.';
        } else if (error.message.includes('No student folders')) {
            errorMessage += 'No student data found. Start the camera first to collect data.';
        } else {
            errorMessage += error.message;
        }
        
        alert(errorMessage);
        
        // Show empty state again
        loadingState.style.display = 'none';
        emptyState.style.display = 'block';
    } finally {
        isAnalyzing = false;
        analyzeBtn.disabled = false;
    }
}

/**
 * Simulate progress bar
 */
function simulateProgress() {
    let progress = 0;
    const interval = setInterval(() => {
        progress += Math.random() * 15;
        if (progress >= 90) {
            progress = 90;
            clearInterval(interval);
        }
        updateProgress(progress);
    }, 500);
}

/**
 * Update progress bar
 */
function updateProgress(percent) {
    progressFill.style.width = `${percent}%`;
    progressText.textContent = `${Math.round(percent)}%`;
}

/**
 * Display analysis results
 */
function displayResults(data) {
    const { summary, students } = data;
    
    // Hide loading, show dashboard
    loadingState.style.display = 'none';
    dashboardContent.style.display = 'block';
    
    // Update summary cards
    updateSummaryCards(summary);
    
    // Update distribution chart
    updateDistributionChart(summary);
    
    // Display student cards
    displayStudentCards(students);
}

/**
 * Update summary cards
 */
function updateSummaryCards(summary) {
    document.getElementById('totalStudents').textContent = summary.total_students;
    document.getElementById('focusedStudents').textContent = summary.focused_students;
    document.getElementById('distractedStudents').textContent = summary.unfocused_students;
    document.getElementById('avgEngagement').textContent = `${summary.average_engagement}%`;
}

/**
 * Update distribution chart
 */
function updateDistributionChart(summary) {
    const total = summary.total_students;
    
    if (total === 0) return;
    
    const focusedPercent = (summary.focused_students / total) * 100;
    const moderatePercent = (summary.moderately_focused_students / total) * 100;
    const unfocusedPercent = (summary.unfocused_students / total) * 100;
    
    // Animate bars
    setTimeout(() => {
        document.getElementById('focusedBar').style.width = `${focusedPercent}%`;
        document.getElementById('focusedPercent').textContent = `${Math.round(focusedPercent)}%`;
        
        document.getElementById('neutralBar').style.width = `${moderatePercent}%`;
        document.getElementById('neutralPercent').textContent = `${Math.round(moderatePercent)}%`;
        
        document.getElementById('distractedBar').style.width = `${unfocusedPercent}%`;
        document.getElementById('distractedPercent').textContent = `${Math.round(unfocusedPercent)}%`;
    }, 100);
}

/**
 * Display student cards
 */
function displayStudentCards(students) {
    studentGrid.innerHTML = '';
    
    // Sort by engagement percentage (descending)
    students.sort((a, b) => {
        const scoreA = a.engagement_percentage || a.engagement_score || 0;
        const scoreB = b.engagement_percentage || b.engagement_score || 0;
        return scoreB - scoreA;
    });
    
    students.forEach((student, index) => {
        const card = createStudentCard(student);
        studentGrid.appendChild(card);
        
        // Stagger animation
        card.style.animationDelay = `${index * 0.05}s`;
    });
}

/**
 * Create student card element
 */
function createStudentCard(student) {
    const card = document.createElement('div');
    card.className = 'student-card';
    
    const engagementScore = student.engagement_percentage || student.engagement_score || 0;
    
    let scoreClass = 'low';
    if (engagementScore >= 75) scoreClass = 'high';
    else if (engagementScore >= 40) scoreClass = 'medium';
    
    let statusClass = student.status.toLowerCase().replace(/\s+/g, '-');
    
    // Handle both session-based and legacy image paths
    let imageUrl = 'placeholder.jpg';
    if (student.sample_image) {
        // Check if it's already a session path
        if (student.sample_image.startsWith('sessions/')) {
            imageUrl = `/api/images/${student.sample_image}`;
        } else {
            // Legacy path - remove 'students/' prefix
            imageUrl = `/api/images/${student.sample_image.replace('students/', '')}`;
        }
    }
    
    const breakdown = Object.entries(student.prediction_breakdown)
        .sort((a, b) => b[1].count - a[1].count)
        .slice(0, 3);
    
    // Build pose debug info if available
    let poseDebugHtml = '';
    if (student.head_pose_stats && student.head_pose_stats.avg_yaw !== null) {
        const pose = student.head_pose_stats;
        const method = student.method_breakdown;
        const fallbackUsed = method.fallback_count > 0;
        const poseReliability = (method.pose_reliability * 100).toFixed(0);
        
        poseDebugHtml = `
            <div class="pose-debug">
                <div class="pose-debug-title">🎯 Head Pose Detection</div>
                <div class="pose-angles">
                    <div class="pose-angle">
                        <span class="pose-label">Yaw:</span>
                        <span class="pose-value ${Math.abs(pose.avg_yaw) > 30 ? 'pose-bad' : 'pose-good'}">${pose.avg_yaw}°</span>
                    </div>
                    <div class="pose-angle">
                        <span class="pose-label">Pitch:</span>
                        <span class="pose-value ${Math.abs(pose.avg_pitch) > 30 ? 'pose-bad' : 'pose-good'}">${pose.avg_pitch}°</span>
                    </div>
                    <div class="pose-angle">
                        <span class="pose-label">Roll:</span>
                        <span class="pose-value ${Math.abs(pose.avg_roll) > 35 ? 'pose-bad' : 'pose-good'}">${pose.avg_roll}°</span>
                    </div>
                </div>
                <div class="pose-meta">
                    <span class="pose-reliability">Pose Reliability: ${poseReliability}%</span>
                    <span class="pose-fallback ${fallbackUsed ? 'fallback-yes' : 'fallback-no'}">
                        Fallback: ${fallbackUsed ? 'Yes (' + method.fallback_count + ' frames)' : 'No'}
                    </span>
                </div>
            </div>
        `;
    }
    
    card.innerHTML = `
        <img src="${imageUrl}" alt="${student.student_id}" class="student-image" 
             onerror="this.src='data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22320%22 height=%22200%22%3E%3Crect fill=%22%23e5e7eb%22 width=%22320%22 height=%22200%22/%3E%3Ctext x=%2250%25%22 y=%2250%25%22 dominant-baseline=%22middle%22 text-anchor=%22middle%22 font-family=%22sans-serif%22 font-size=%2218%22 fill=%22%239ca3af%22%3ENo Image%3C/text%3E%3C/svg%3E'">
        
        <div class="student-info">
            <div class="student-header">
                <div class="student-id">${formatStudentId(student.student_id)}</div>
                <span class="status-badge ${statusClass}">${student.status}</span>
            </div>
            
            <div class="engagement-score">
                <div class="score-label">Engagement Score</div>
                <div class="score-bar">
                    <div class="score-fill ${scoreClass}" style="width: ${engagementScore}%">
                        ${Math.round(engagementScore)}%
                    </div>
                </div>
            </div>
            
            ${poseDebugHtml}
            
            <div class="student-stats">
                <div class="stat-item">
                    <div class="stat-value">${student.images_analyzed}</div>
                    <div class="stat-label">Images</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${student.most_common_state}</div>
                    <div class="stat-label">Most Common</div>
                </div>
            </div>
            
            <ul class="breakdown-list">
                ${breakdown.map(([state, data]) => `
                    <li class="breakdown-item">
                        <span class="breakdown-label">${state}</span>
                        <span class="breakdown-value">${data.count} (${data.percentage}%)</span>
                    </li>
                `).join('')}
            </ul>
        </div>
    `;
    
    return card;
}

/**
 * Format student ID for display
 */
function formatStudentId(id) {
    return id.replace('student_', 'Student ');
}

/**
 * Show notification
 */
function showNotification(message, type = 'info') {
    console.log(`[${type.toUpperCase()}] ${message}`);
    // Could add toast notifications here
}


// ============================================================================
// VIDEO UPLOAD FUNCTIONS
// ============================================================================

/**
 * Open upload modal
 */
function openUploadModal() {
    uploadModal.style.display = 'flex';
    resetUploadModal();
}

/**
 * Close upload modal
 */
function closeUploadModal() {
    uploadModal.style.display = 'none';
    resetUploadModal();
}

/**
 * Reset upload modal to initial state
 */
function resetUploadModal() {
    console.log('🔄 Resetting upload modal UI');
    uploadArea.style.display = 'block';
    uploadProgress.style.display = 'none';
    uploadSuccess.style.display = 'none';
    videoFileInput.value = '';
    // DO NOT reset uploadedVideoPath here - it needs to persist!
    console.log('📁 uploadedVideoPath preserved:', uploadedVideoPath);
}

/**
 * Handle drag over
 */
function handleDragOver(e) {
    e.preventDefault();
    e.stopPropagation();
    uploadArea.classList.add('drag-over');
}

/**
 * Handle drag leave
 */
function handleDragLeave(e) {
    e.preventDefault();
    e.stopPropagation();
    uploadArea.classList.remove('drag-over');
}

/**
 * Handle drop
 */
async function handleDrop(e) {
    e.preventDefault();
    e.stopPropagation();
    uploadArea.classList.remove('drag-over');
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        console.log('📁 File dropped:', files[0].name);
        await handleFile(files[0]);
    }
}

/**
 * Handle file select
 */
async function handleFileSelect(e) {
    const files = e.target.files;
    if (files.length > 0) {
        console.log('📁 File selected from input:', files[0].name);
        await handleFile(files[0]);
    }
}

/**
 * Handle file upload
 */
async function handleFile(file) {
    console.log('═══════════════════════════════════════════════════════');
    console.log('📤 STARTING FILE UPLOAD');
    console.log('═══════════════════════════════════════════════════════');
    console.log('📁 File name:', file.name);
    console.log('📊 File size:', (file.size / (1024 * 1024)).toFixed(2), 'MB');
    console.log('📝 File type:', file.type);
    console.log('📁 uploadedVideoPath BEFORE upload:', uploadedVideoPath);
    
    // Validate file type
    const validTypes = ['video/mp4', 'video/avi', 'video/quicktime', 'video/x-matroska', 
                       'video/x-flv', 'video/x-ms-wmv', 'video/webm'];
    if (!validTypes.includes(file.type) && !file.name.match(/\.(mp4|avi|mov|mkv|flv|wmv|webm)$/i)) {
        alert('Invalid file type. Please upload a video file (MP4, AVI, MOV, MKV, FLV, WMV, WEBM)');
        return;
    }
    
    // Validate file size (500MB max)
    const maxSize = 500 * 1024 * 1024;
    if (file.size > maxSize) {
        alert('File too large. Maximum size is 500MB');
        return;
    }
    
    // Show upload progress
    uploadArea.style.display = 'none';
    uploadProgress.style.display = 'block';
    uploadFileName.textContent = file.name;
    uploadFileSize.textContent = `${(file.size / (1024 * 1024)).toFixed(2)} MB`;
    
    // Create form data
    const formData = new FormData();
    formData.append('video', file);
    
    console.log('📤 Sending upload request...');
    
    // Upload with progress tracking using Promise wrapper
    try {
        const result = await new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest();
            
            xhr.upload.addEventListener('progress', (e) => {
                if (e.lengthComputable) {
                    const percent = (e.loaded / e.total) * 100;
                    uploadProgressFill.style.width = `${percent}%`;
                    uploadProgressText.textContent = `Uploading... ${Math.round(percent)}%`;
                    if (percent % 25 === 0) {
                        console.log(`📤 Upload progress: ${Math.round(percent)}%`);
                    }
                }
            });
            
            xhr.addEventListener('load', () => {
                console.log('📥 Upload response received');
                console.log('   Status:', xhr.status);
                console.log('   Response text:', xhr.responseText);
                
                if (xhr.status === 200) {
                    try {
                        const data = JSON.parse(xhr.responseText);
                        console.log('📥 Parsed response:', data);
                        console.log('   Keys:', Object.keys(data));
                        console.log('   data.success:', data.success);
                        console.log('   data.filepath:', data.filepath);
                        
                        if (data.success) {
                            resolve(data);
                        } else {
                            reject(new Error(data.error || 'Upload failed'));
                        }
                    } catch (e) {
                        console.error('❌ Failed to parse response:', e);
                        reject(new Error('Failed to parse upload response: ' + e.message));
                    }
                } else {
                    console.error('❌ Upload failed with status:', xhr.status);
                    reject(new Error(`Upload failed with status ${xhr.status}`));
                }
            });
            
            xhr.addEventListener('error', () => {
                console.error('❌ Upload network error');
                reject(new Error('Upload failed - network error'));
            });
            
            xhr.addEventListener('abort', () => {
                console.error('❌ Upload aborted');
                reject(new Error('Upload aborted'));
            });
            
            console.log('📤 Opening XHR connection to:', '/api/video/upload');
            xhr.open('POST', '/api/video/upload');
            xhr.send(formData);
        });
        
        // Upload completed successfully
        console.log('═══════════════════════════════════════════════════════');
        console.log('✅ UPLOAD COMPLETED SUCCESSFULLY');
        console.log('═══════════════════════════════════════════════════════');
        console.log('📁 Received filepath:', result.filepath);
        console.log('📝 Filename:', result.filename);
        console.log('📊 Size:', result.size_mb, 'MB');
        
        // CRITICAL: Set global variable
        console.log('📁 Setting uploadedVideoPath to:', result.filepath);
        uploadedVideoPath = result.filepath;
        console.log('📁 uploadedVideoPath is now:', uploadedVideoPath);
        console.log('📁 Type:', typeof uploadedVideoPath);
        console.log('📁 Length:', uploadedVideoPath ? uploadedVideoPath.length : 'NULL');
        console.log('═══════════════════════════════════════════════════════');
        
        // Update UI - show success state
        uploadProgress.style.display = 'none';
        uploadSuccess.style.display = 'block';
        
        console.log('✅ UI updated - Start Processing button should now be visible');
        
        return result;
        
    } catch (error) {
        console.error('═══════════════════════════════════════════════════════');
        console.error('❌ UPLOAD FAILED');
        console.error('═══════════════════════════════════════════════════════');
        console.error('Error:', error.message);
        console.error('Stack:', error.stack);
        alert(`Upload failed: ${error.message}`);
        resetUploadModal();
        throw error;
    }
}

/**
 * Start video processing
 */
async function startVideoProcessing() {
    console.log('═══════════════════════════════════════════════════════');
    console.log('🎬 START PROCESSING BUTTON CLICKED');
    console.log('═══════════════════════════════════════════════════════');
    console.log('📁 CHECKING uploadedVideoPath:');
    console.log('   Value:', uploadedVideoPath);
    console.log('   Type:', typeof uploadedVideoPath);
    console.log('   Is null?', uploadedVideoPath === null);
    console.log('   Is undefined?', uploadedVideoPath === undefined);
    console.log('   Is empty string?', uploadedVideoPath === '');
    console.log('   Truthy?', !!uploadedVideoPath);
    
    if (!uploadedVideoPath) {
        console.error('❌ VALIDATION FAILED: uploadedVideoPath is falsy');
        console.error('   Actual value:', uploadedVideoPath);
        alert('No video file uploaded. Please upload a video first.');
        return;
    }
    
    // Additional validation
    if (typeof uploadedVideoPath !== 'string') {
        console.error('❌ VALIDATION FAILED: uploadedVideoPath is not a string');
        console.error('   Type:', typeof uploadedVideoPath);
        console.error('   Value:', uploadedVideoPath);
        alert('Invalid video path type. Please upload the video again.');
        uploadedVideoPath = null;
        resetUploadModal();
        return;
    }
    
    if (uploadedVideoPath.trim() === '') {
        console.error('❌ VALIDATION FAILED: uploadedVideoPath is empty string');
        alert('Invalid video path. Please upload the video again.');
        uploadedVideoPath = null;
        resetUploadModal();
        return;
    }
    
    console.log('✅ VALIDATION PASSED');
    console.log('═══════════════════════════════════════════════════════');
    
    try {
        console.log('🎬 Starting video processing...');
        console.log('📁 Using filepath:', uploadedVideoPath);
        
        // Close modal
        closeUploadModal();
        
        // Reset dashboard
        resetDashboard();
        
        // Stop any existing processing
        if (cameraRunning || videoProcessing) {
            console.log('🛑 Stopping existing processing...');
            await stopCamera();
            await new Promise(resolve => setTimeout(resolve, 500));
        }
        
        // Prepare request
        const requestBody = {
            filepath: uploadedVideoPath
        };
        
        console.log('═══════════════════════════════════════════════════════');
        console.log('📤 SENDING PROCESSING REQUEST');
        console.log('═══════════════════════════════════════════════════════');
        console.log('   URL:', '/api/video/process');
        console.log('   Method: POST');
        console.log('   Body:', JSON.stringify(requestBody, null, 2));
        console.log('   Body.filepath:', requestBody.filepath);
        console.log('═══════════════════════════════════════════════════════');
        
        const response = await fetch('/api/video/process', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
        });
        
        console.log('═══════════════════════════════════════════════════════');
        console.log('📥 PROCESSING RESPONSE RECEIVED');
        console.log('═══════════════════════════════════════════════════════');
        console.log('   Status:', response.status);
        console.log('   Status Text:', response.statusText);
        
        const data = await safeJsonResponse(response);
        console.log('   Response data:', JSON.stringify(data, null, 2));
        console.log('═══════════════════════════════════════════════════════');
        
        if (data.success) {
            console.log('✅ Video processing started');
            console.log('📁 Session ID:', data.session_id);
            console.log('🎞️  Total frames:', data.total_frames);
            
            videoProcessing = true;
            sourceType = 'video';
            currentSessionId = data.session_id;
            
            // Update UI
            videoSectionTitle.textContent = 'Video Processing';
            startCameraBtn.style.display = 'none';
            uploadVideoBtn.style.display = 'none';
            stopCameraBtn.style.display = 'inline-flex';
            stopCameraBtn.innerHTML = '<i class="fas fa-stop"></i> Stop Processing';
            videoPlaceholder.style.display = 'none';
            videoFeedImg.style.display = 'block';  // Use img element for server stream
            videoStats.style.display = 'flex';
            videoProgress.style.display = 'block';
            
            // Start video stream (server-side for uploaded video)
            videoFeedImg.src = `/api/video_feed?t=${Date.now()}`;
            
            // Start stats polling
            startStatsPolling();
            
            // Show success message
            showNotification(`Video processing started: ${data.total_frames} frames`, 'success');
        } else {
            throw new Error(data.error || 'Failed to start video processing');
        }
        
    } catch (error) {
        console.error('❌ Video processing error:', error);
        alert(`Failed to start video processing: ${error.message}`);
    }
}

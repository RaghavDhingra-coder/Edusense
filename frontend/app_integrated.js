// API Configuration
const API_BASE_URL = 'http://localhost:8080/api';

// DOM Elements
const startCameraBtn = document.getElementById('startCameraBtn');
const stopCameraBtn = document.getElementById('stopCameraBtn');
const analyzeBtn = document.getElementById('analyzeBtn');
const videoFeed = document.getElementById('videoFeed');
const videoPlaceholder = document.getElementById('videoPlaceholder');
const videoStats = document.getElementById('videoStats');
const loadingState = document.getElementById('loadingState');
const emptyState = document.getElementById('emptyState');
const dashboardContent = document.getElementById('dashboardContent');
const studentGrid = document.getElementById('studentGrid');
const progressFill = document.getElementById('progressFill');
const progressText = document.getElementById('progressText');

// State
let cameraRunning = false;
let statsInterval = null;
let isAnalyzing = false;
let currentSessionId = null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    // Set up event listeners
    startCameraBtn.addEventListener('click', startCamera);
    stopCameraBtn.addEventListener('click', stopCamera);
    analyzeBtn.addEventListener('click', analyzeClassroom);
    
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
 * Start camera
 */
async function startCamera() {
    try {
        console.log('🎥 Starting new camera session...');
        startCameraBtn.disabled = true;
        
        // Reset dashboard for new session
        resetDashboard();
        
        const response = await fetch(`${API_BASE_URL}/camera/start`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            console.log('✅ Camera started');
            console.log('📁 Session ID:', data.session_id);
            console.log('📁 Session Dir:', data.session_dir);
            
            cameraRunning = true;
            currentSessionId = data.session_id;
            
            // Update UI
            startCameraBtn.style.display = 'none';
            stopCameraBtn.style.display = 'inline-flex';
            videoPlaceholder.style.display = 'none';
            videoFeed.style.display = 'block';
            videoStats.style.display = 'flex';
            
            // Start video stream
            videoFeed.src = `${API_BASE_URL}/video_feed?t=${Date.now()}`;
            
            // Start stats polling
            startStatsPolling();
            
            // Show success message
            showNotification(`New session started: ${data.session_id}`, 'success');
        } else {
            throw new Error(data.error || 'Failed to start camera');
        }
        
    } catch (error) {
        console.error('❌ Start camera error:', error);
        alert(`Failed to start camera: ${error.message}`);
    } finally {
        startCameraBtn.disabled = false;
    }
}

/**
 * Stop camera
 */
async function stopCamera() {
    try {
        console.log('🛑 Stopping camera...');
        stopCameraBtn.disabled = true;
        
        const response = await fetch(`${API_BASE_URL}/camera/stop`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            console.log('✅ Camera stopped');
            cameraRunning = false;
            currentSessionId = null;
            
            // Update UI
            startCameraBtn.style.display = 'inline-flex';
            stopCameraBtn.style.display = 'none';
            videoPlaceholder.style.display = 'flex';
            videoFeed.style.display = 'none';
            videoStats.style.display = 'none';
            videoFeed.src = '';
            
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
        const response = await fetch(`${API_BASE_URL}/camera/status`);
        const data = await response.json();
        
        if (data.success && data.status.running) {
            // Camera is already running
            cameraRunning = true;
            startCameraBtn.style.display = 'none';
            stopCameraBtn.style.display = 'inline-flex';
            videoPlaceholder.style.display = 'none';
            videoFeed.style.display = 'block';
            videoStats.style.display = 'flex';
            videoFeed.src = `${API_BASE_URL}/video_feed?t=${Date.now()}`;
            startStatsPolling();
        }
    } catch (error) {
        console.log('Camera status check failed:', error);
    }
}

/**
 * Start polling camera stats
 */
function startStatsPolling() {
    if (statsInterval) {
        clearInterval(statsInterval);
    }
    
    statsInterval = setInterval(async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/camera/status`);
            const data = await response.json();
            
            if (data.success && data.status) {
                const stats = data.status;
                document.getElementById('statFps').textContent = stats.fps.toFixed(1);
                document.getElementById('statFaces').textContent = stats.active_tracks || 0;
                document.getElementById('statStudents').textContent = stats.total_students || 0;
                document.getElementById('statImages').textContent = stats.total_images || 0;
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
        
        const response = await fetch(`${API_BASE_URL}/analyze`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        console.log('Response status:', response.status);
        
        if (!response.ok) {
            const errorData = await response.json();
            console.error('API Error:', errorData);
            throw new Error(errorData.error || 'Analysis failed');
        }
        
        const data = await response.json();
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
            imageUrl = `${API_BASE_URL}/images/${student.sample_image}`;
        } else {
            // Legacy path - remove 'students/' prefix
            imageUrl = `${API_BASE_URL}/images/${student.sample_image.replace('students/', '')}`;
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

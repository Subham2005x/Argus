let registrationStream = null;
let attendanceStream = null;
let attendanceInterval = null;
let isClassRunning = false;

document.addEventListener("DOMContentLoaded", function () {
    setTimeout(() => {
        document.getElementById("loadingScreen").style.display = "none";
        document.getElementById("loadingScreen").style.display = "none";
        document.body.style.overflow = "auto";
    }, 800); // Customizable loading duration
});

// Get the toggle switch and body element
const themeToggle = document.getElementById('theme-toggle-switch');
const body = document.body;

// Check localStorage for theme preference
const savedTheme = localStorage.getItem('theme');
if (savedTheme === 'dark') {
    body.classList.add('dark-theme');
    themeToggle.checked = true;
}

// Add event listener to toggle switch
themeToggle.addEventListener('change', () => {
    if (themeToggle.checked) {
        body.classList.add('dark-theme');
        localStorage.setItem('theme', 'dark'); // Save preference to localStorage
    } else {
        body.classList.remove('dark-theme');
        localStorage.setItem('theme', 'light'); // Save preference to localStorage
    }
});
async function startRegistration() {
    const studentName = document.getElementById('studentName').value.trim();
    if (!studentName) {
        showAlert('registrationAlert', 'Please enter student name', 'error');
        return;
    }

    try {
        registrationStream = await navigator.mediaDevices.getUserMedia({
            video: { width: 640, height: 480, facingMode: 'user' }
        });
        
        const video = document.getElementById('registrationVideo');
        video.srcObject = registrationStream;
        await video.play();
        
        // Show the capture button
        document.querySelector('button[onclick="captureRegistration()"]').hidden = false;
    } catch (error) {
        console.error('Camera error:', error);
        showAlert('registrationAlert', 'Camera access denied: ' + error.message, 'error');
    }
}

async function captureRegistration() {
    const studentName = document.getElementById('studentName').value.trim();
    if (!studentName) {
        showAlert('registrationAlert', 'Please enter student name', 'error');
        return;
    }

    const video = document.getElementById('registrationVideo');
    const canvas = document.createElement('canvas');
    
    try {
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        canvas.getContext('2d').drawImage(video, 0, 0);
        
        const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/jpeg'));
        const formData = new FormData();
        formData.append('name', studentName);
        formData.append('image', blob, `${studentName}.jpg`);

        const response = await fetch('/rajrup/register-student', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(errorText || `HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        if (result.success) {
            showAlert('registrationAlert', 'Registration successful!', 'success');
            stopRegistration();
        } else {
            throw new Error(result.message || 'Registration failed');
        }
    } catch (error) {
        console.error('Registration error:', error);
        showAlert('registrationAlert', error.message, 'error');
    }
}

function stopRegistration() {
    if (registrationStream) {
        registrationStream.getTracks().forEach(track => track.stop());
        registrationStream = null;
    }
    const video = document.getElementById('registrationVideo');
    video.srcObject = null;
    document.getElementById('studentName').value = '';
    document.querySelector('button[onclick="captureRegistration()"]').hidden = true;
}

async function startClass() {
    try {
        const video = document.getElementById('attendanceVideo');
        attendanceStream = await navigator.mediaDevices.getUserMedia({
            video: { width: 640, height: 480, facingMode: 'user' }
        });
        
        video.srcObject = attendanceStream;
        await video.play();
        
        // Start periodic attendance capture
        attendanceInterval = setInterval(captureAttendanceFrame, 5000); // every 5 seconds
        
        showAlert('attendanceAlert', 'Attendance tracking started', 'success');
    } catch (error) {
        console.error('Camera error:', error);
        showAlert('attendanceAlert', 'Failed to start camera: ' + error.message, 'error');
    }
}

async function captureAttendanceFrame() {
    const video = document.getElementById('attendanceVideo');
    const canvas = document.createElement('canvas');
    
    try {
        // Capture frame
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        canvas.getContext('2d').drawImage(video, 0, 0);
        
        // Convert to blob
        const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/jpeg'));
        const formData = new FormData();
        formData.append('image', blob, 'frame.jpg');

        // Send for processing
        const response = await fetch('/rajrup/mark-attendance', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.message || `Server error: ${response.status}`);
        }

        const result = await response.json();
        
        if (result.success) {
            if (result.present.length > 0) {
                showAlert('attendanceAlert', 
                    `Present: ${result.present.join(', ')}`, 
                    'success');
                updateAttendanceDisplay(result.present);
            }
        } else {
            throw new Error(result.message || 'Failed to process attendance');
        }
    } catch (error) {
        console.error('Error capturing frame:', error);
        showAlert('attendanceAlert', error.message, 'error');
    }
}

function updateAttendanceDisplay(presentStudents) {
    const container = document.getElementById('attendanceRecords');
    if (!container) return;

    container.innerHTML = `
        <div class="attendance-current">
            <h3>Currently Present:</h3>
            <ul>
                ${presentStudents.map(name => `<li>${name}</li>`).join('')}
            </ul>
            <p>Total Present: ${presentStudents.length}</p>
        </div>
    `;
}

function endClass() {
    if (attendanceInterval) {
        clearInterval(attendanceInterval);
        attendanceInterval = null;
    }
    
    if (attendanceStream) {
        attendanceStream.getTracks().forEach(track => track.stop());
        attendanceStream = null;
    }
    
    const video = document.getElementById('attendanceVideo');
    video.srcObject = null;
    
    showAlert('attendanceAlert', 'Attendance tracking stopped', 'info');
}
let selectedDate = null; // Global variable to store the selected date

// Initialize Flatpickr
flatpickr("#attendanceDate", {
    dateFormat: "Y-m-d", // Format the date as YYYY-MM-DD
    onChange: function(selectedDates, dateStr, instance) {
        selectedDate = dateStr; // Store the selected date
        viewAttendance(); // Load attendance records for the selected date
    },
});
// Initialize Flatpickr for Start and End Date fields
flatpickr("#startDate", {
    dateFormat: "Y-m-d"
});

flatpickr("#endDate", {
    dateFormat: "Y-m-d"
});

// Function to fetch and display attendance records
function viewAttendance() {
    if (!selectedDate ) {
        alert("Please select a date.");
        return;
    }

    // Show loading spinner
    document.getElementById("loadingSpinner").style.display = "block";

    // Fetch attendance records for the selected date
    fetch(`/get_attendance?date=${selectedDate}`)
        .then(response => response.json())
        .then(data => {
            // Hide loading spinner
            document.getElementById("loadingSpinner").style.display = "none";

            // Display attendance records
            displayAttendanceRecords(data);
        })
        .catch(error => {
            console.error("Error fetching attendance records:", error);
            document.getElementById("loadingSpinner").style.display = "none";
            alert("Failed to fetch attendance records.");
        });
}

// Function to refresh attendance records
function refreshAttendance() {
    if (selectedDate && isClassRunning ) {
        viewAttendance(); // Reload attendance records for the selected date
    }
}

// Function to display attendance records in a table
function displayAttendanceRecords(records) {
    const recordsContainer = document.getElementById("attendanceRecords");
    recordsContainer.innerHTML = "";

    if (records.length === 0) {
        recordsContainer.innerHTML = "<p>No records found for the selected date.</p>";
        return;
    }

    const table = document.createElement("table");
    table.className = "attendance-table";

    // Create table header
    const headerRow = document.createElement("tr");
    headerRow.innerHTML = `
        <th>Name</th>
        <th>Time</th>
        <th>Status</th>
    `;
    table.appendChild(headerRow);

    // Add records to the table
    records.forEach(record => {
        const row = document.createElement("tr");
        row.innerHTML = `
            <td>${record.student_name}</td>
            <td>${record.time}</td>
            <td>${record.status}</td>
        `;
        table.appendChild(row);
    });

    recordsContainer.appendChild(table);
}

// Polling: Refresh attendance records every 5 seconds
setInterval(refreshAttendance, 5000);
document.addEventListener("DOMContentLoaded", function () {
    document.getElementById("fetchPercentage").addEventListener("click", fetchAttendancePercentage);
});

function fetchAttendancePercentage() {
    let startDate = document.getElementById("startDate").value;
    let endDate = document.getElementById("endDate").value;

    if (!startDate || !endDate) {
        alert("Please select a start and end date.");
        return;
    }

    fetch(`/get_attendance_percentage?start=${startDate}&end=${endDate}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                data.data.sort((a, b) => b.percentage - a.percentage);
                displayAttendancePercentage(data.data);
            } else {
                alert(data.message);
            }
        })
        .catch(error => {
            console.error("Error fetching attendance percentage:", error);
            alert("Failed to fetch attendance percentage.");
        });
}

function displayAttendancePercentage(records) {
    const container = document.getElementById("attendancePercentageRecords");
    container.innerHTML = "";

    if (records.length === 0) {
        container.innerHTML = "<p>No records found for the selected date range.</p>";
        return;
    }

    const table = document.createElement("table");
    table.className = "attendance-table";

    const headerRow = document.createElement("tr");
    headerRow.innerHTML = `<th>Name</th><th>Percentage</th>`;
    table.appendChild(headerRow);

    records.forEach(record => {
        const row = document.createElement("tr");
        row.innerHTML = `<td>${record.name}</td><td>${record.percentage}%</td>`;
        table.appendChild(row);
    });

    container.appendChild(table);
}
function downloadAttendancePDF() {
    const date = document.getElementById("attendanceDate").value;
    if (!date) {
        alert("Please select a date.");
        return;
    }
    window.location.href = `/download_attendance_pdf?date=${date}`;
}

// Utility functions
function showAlert(containerId, message, type) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type}`;
    alertDiv.textContent = message;

    const container = document.getElementById(containerId);
    container.innerHTML = '';
    container.appendChild(alertDiv);
}

function showLoading(show) {
    const spinner = document.querySelector('.loading-spinner');
    spinner.style.display = show ? 'inline-block' : 'none';
}

// Handle window resize
window.addEventListener('resize', () => {
    if (isClassRunning) {
        const video = document.getElementById('attendanceVideo');
        video.style.width = '100%';
        video.style.height = 'auto';
    }
});

async function startAttendance() {
    try {
        const video = document.getElementById('attendanceVideo');
        const stream = await navigator.mediaDevices.getUserMedia({
            video: { width: 640, height: 480, facingMode: 'user' }
        });
        
        video.srcObject = stream;
        await video.play();
        
        // Start periodic attendance capture
        attendanceInterval = setInterval(captureAttendance, 5000); // every 5 seconds
        
        document.getElementById('startAttendance').style.display = 'none';
        document.getElementById('stopAttendance').style.display = 'block';
    } catch (error) {
        console.error('Camera error:', error);
        showAlert('attendanceAlert', 'Failed to start camera: ' + error.message, 'error');
    }
}

async function captureAttendance() {
    const video = document.getElementById('attendanceVideo');
    const canvas = document.createElement('canvas');
    
    try {
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        canvas.getContext('2d').drawImage(video, 0, 0);
        
        const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/jpeg'));
        const formData = new FormData();
        formData.append('image', blob);

        const response = await fetch('/rajrup/mark-attendance', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        
        if (result.success) {
            if (result.present.length > 0) {
                showAlert('attendanceAlert', 
                    `Attendance marked for: ${result.present.join(', ')}`, 
                    'success');
                updateAttendanceList(result.present);
            }
        } else {
            throw new Error(result.message || 'Failed to mark attendance');
        }
    } catch (error) {
        console.error('Error capturing frame:', error);
        showAlert('attendanceAlert', error.message, 'error');
    }
}

function stopAttendance() {
    if (attendanceInterval) {
        clearInterval(attendanceInterval);
        attendanceInterval = null;
    }
    
    const video = document.getElementById('attendanceVideo');
    if (video.srcObject) {
        video.srcObject.getTracks().forEach(track => track.stop());
        video.srcObject = null;
    }
    
    document.getElementById('startAttendance').style.display = 'block';
    document.getElementById('stopAttendance').style.display = 'none';
}

function updateAttendanceList(presentStudents) {
    const listContainer = document.getElementById('attendanceRecords');
    if (!listContainer) return;
    
    let html = `
        <div class="attendance-current">
            <h3>Currently Present:</h3>
            <ul>
                ${presentStudents.map(name => `<li>${name}</li>`).join('')}
            </ul>
            <p>Total Present: ${presentStudents.length}</p>
        </div>
    `;
    
    listContainer.innerHTML = html;
}

async function downloadAttendanceReport() {
    try {
        const startDate = document.getElementById('startDate').value;
        const endDate = document.getElementById('endDate').value;

        if (!startDate || !endDate) {
            showAlert('attendanceAlert', 'Please select both start and end dates', 'error');
            return;
        }

        showLoading(true);

        const response = await fetch('/rajrup/download-attendance', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/pdf'
            },
            body: JSON.stringify({
                startDate: startDate,
                endDate: endDate
            })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.message || 'Failed to generate report');
        }

        // Get the filename from the Content-Disposition header if available
        const contentDisposition = response.headers.get('Content-Disposition');
        let filename = 'attendance_report.pdf';
        if (contentDisposition) {
            const filenameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
            if (filenameMatch && filenameMatch[1]) {
                filename = filenameMatch[1].replace(/['"]/g, '');
            }
        }

        // Create blob and download
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

        showAlert('attendanceAlert', 'Report downloaded successfully', 'success');
    } catch (error) {
        console.error('Download error:', error);
        showAlert('attendanceAlert', error.message, 'error');
    } finally {
        showLoading(false);
    }
}


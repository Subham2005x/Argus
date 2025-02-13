document.addEventListener("DOMContentLoaded", function () {
    const darkModeToggle = document.getElementById("darkModeToggle");
    const body = document.body;
    const accountDropdown = document.getElementById("accountDropdown");

    // Dark Mode Toggle
    darkModeToggle.addEventListener("change", function () {
        if (this.checked) {
            body.classList.add("dark-mode");
            body.classList.remove("light-mode");
        } else {
            body.classList.add("light-mode");
            body.classList.remove("dark-mode");
        }
    });

    // Toggle Account Dropdown
    window.toggleAccountMenu = function () {
        accountDropdown.style.display = 
            accountDropdown.style.display === "block" ? "none" : "block";
    };

    // Close dropdown when clicking outside
    document.addEventListener("click", function (event) {
        if (!event.target.closest(".account-menu")) {
            accountDropdown.style.display = "none";
        }
    });
});
let isEditing = false;
let editId = null;
const modal = document.getElementById('class-modal');
const classNameInput = document.getElementById('class-name');
const studentCountInput = document.getElementById('student-count');

// Function to open modal
function openModal() {
    modal.style.display = 'block';
    classNameInput.value = '';
    studentCountInput.value = '';
    isEditing = false;
}

// Function to close modal
function closeModal() {
    modal.style.display = 'none';
    classNameInput.value = '';
    studentCountInput.value = '';
}

// Function to save class
async function saveClass() {
    const className = classNameInput.value.trim();
    const studentCount = studentCountInput.value;

    if (!className) {
        alert('Please enter a department name');
        return;
    }
    if (!studentCount || studentCount < 1) {
        alert('Please enter a valid number of students');
        return;
    }

    try {
        let url = '/api/classes';
        let method = 'POST';
        let body = { 
            name: className,
            studentCount: parseInt(studentCount)
        };

        if (isEditing) {
            url = `/api/classes/${editId}`;
            method = 'PUT';
        }

        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(body)
        });

        if (response.ok) {
            closeModal();
            loadClasses();
        } else {
            const data = await response.json();
            alert(data.error || 'An error occurred');
        }
    } catch (error) {
        alert('An error occurred');
        console.error(error);
    }
}

// Function to edit class
function editClass(id, name, studentCount) {
    isEditing = true;
    editId = id;
    classNameInput.value = name;
    studentCountInput.value = studentCount;
    modal.style.display = 'block';
}

// Function to delete class
async function deleteClass(id) {
    if (!confirm('Are you sure you want to delete this class?')) {
        return;
    }

    try {
        const response = await fetch(`/api/classes/${id}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            loadClasses();
        } else {
            const data = await response.json();
            alert(data.error || 'An error occurred');
        }
    } catch (error) {
        alert('An error occurred');
        console.error(error);
    }
}

// Add this variable to track the currently selected department
let selectedDepartment = null;

// Update the showDepartmentStats function
function showDepartmentStats(departmentName, isClick = false) {
    // If it's just a hover and we have a selected department, don't show stats
    if (!isClick && selectedDepartment) {
        return;
    }

    // Find the department data from the table row
    const departmentRow = Array.from(document.querySelectorAll('.department-row'))
        .find(row => row.querySelector('td').textContent === departmentName);
    
    const studentCount = departmentRow ? departmentRow.dataset.studentCount : '0';

    const heroRight = document.querySelector('.hero-right');
    heroRight.innerHTML = `
        <div class="department-stats active">
            <h2>${departmentName}</h2>
            <div class="stats-container">
                <div class="stat-card">
                    <div class="stat-value">${studentCount}</div>
                    <div class="stat-label">Total Students</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">0</div>
                    <div class="stat-label">Total Classes Done</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">0%</div>
                    <div class="stat-label">Attendance Rate</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">0</div>
                    <div class="stat-label">Active Sessions</div>
                </div>
            </div>
            ${isClick ? `
                <div class="live-attendance-btn-container">
                    <button class="live-attendance-btn" onclick="goToLiveAttendance('${departmentName}')">
                        <i class="fas fa-video"></i>
                        Take Attendance for ${departmentName}
                    </button>
                </div>
            ` : ''}
        </div>
    `;

    if (isClick) {
        selectedDepartment = departmentName;
        updateSelectedDepartmentStyle();
    }
}

// Function to handle department click
function handleDepartmentClick(departmentName) {
    showDepartmentStats(departmentName, true);
}

// Function to handle mouse leave
function handleMouseLeave() {
    if (selectedDepartment) {
        showDepartmentStats(selectedDepartment, true);
    } else {
        const heroRight = document.querySelector('.hero-right');
        heroRight.innerHTML = `
            <div class="placeholder-text">
                <p>Click on a department to view its statistics</p>
            </div>
        `;
    }
}

// Function to update selected department style
function updateSelectedDepartmentStyle() {
    const rows = document.querySelectorAll('.department-row');
    rows.forEach(row => {
        const departmentName = row.querySelector('td').textContent;
        if (departmentName === selectedDepartment) {
            row.classList.add('selected');
        } else {
            row.classList.remove('selected');
        }
    });
}

// Update the loadClasses function to include data attributes
async function loadClasses() {
    try {
        const response = await fetch('/api/classes');
        const classes = await response.json();
        const tableBody = document.querySelector('#classes-table tbody');
        
        tableBody.innerHTML = classes.map(cls => `
            <tr class="department-row" 
                data-name="${cls.name}"
                data-student-count="${cls.studentCount}"
                onmouseover="showDepartmentStats('${cls.name}')"
                onmouseleave="handleMouseLeave()"
                onclick="handleDepartmentClick('${cls.name}')"
            >
                <td>${cls.name}</td>
                <td>
                    <button onclick="editClass(${cls.id}, '${cls.name}', ${cls.studentCount})" class="edit-btn">Edit</button>
                    <button onclick="deleteClass(${cls.id})" class="delete-btn">Delete</button>
                </td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Error loading classes:', error);
    }
}

// Load classes when page loads
window.addEventListener('load', loadClasses);

// Close modal when clicking outside
window.onclick = function(event) {
    if (event.target == modal) {
        closeModal();
    }
}

// Update the goToLiveAttendance function
function goToLiveAttendance(departmentName) {
    // You can encode the department name for the URL
    const encodedDepartment = encodeURIComponent(departmentName);
    window.location.href = `/live-attendance/${encodedDepartment}`;
}
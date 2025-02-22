// Auth functions
function showLogin() {
    document.getElementById('loginModal').style.display = 'flex';
    document.getElementById('registerModal').style.display = 'none';
}

function showRegister() {
    document.getElementById('registerModal').style.display = 'flex';
    document.getElementById('loginModal').style.display = 'none';
}

async function handleLogin() {
    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;

    const response = await fetch('/login', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ email, password })
    });

    if (response.ok) {
        document.getElementById('appContent').style.display = 'block';
        document.getElementById('loginModal').style.display = 'none';
        loadTeacherClasses();
    } else {
        alert('Login failed');
    }
}

async function loadTeacherClasses() {
    const response = await fetch('/api/classes');
    const classes = await response.json();
    const classList = document.getElementById('classList');

    classList.innerHTML = classes.map(cls => `
        <div class="class-item" onclick="selectClass('${cls.id}', '${cls.name}')">
            ${cls.name} - ${cls.subject}
        </div>
    `).join('');
}

function selectClass(classId, className) {
    currentClassId = classId;
    document.getElementById('currentClass').textContent = `Selected Class: ${className}`;
    // Load class-specific data
    loadAttendanceRecords();
}

// Sidebar functions
function toggleSidebar() {
    document.querySelector('.sidebar').classList.toggle('active');
}

async function createNewClass() {
    const name = document.getElementById('className').value;
    const subject = document.getElementById('classSubject').value;

    const response = await fetch('/api/classes', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ name, subject })
    });

    if (response.ok) {
        loadTeacherClasses();
        document.getElementById('addClassModal').style.display = 'none';
    }
}
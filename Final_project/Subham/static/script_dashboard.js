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

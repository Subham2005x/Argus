// Smooth Scroll to About Section
function scrollToAbout() {
    document.getElementById('about').scrollIntoView({ behavior: 'smooth' });
}

// Smooth Scroll to Team Section
function scrollToTeam() {
    document.getElementById('team').scrollIntoView({ behavior: 'smooth' });
}

// Scroll to Top Button
document.addEventListener("DOMContentLoaded", function () {
    const aboutSection = document.getElementById("about");

    function toggleVisibilityOnScroll() {
        const sectionPosition = aboutSection.getBoundingClientRect().top;
        const screenPosition = window.innerHeight / 1.3; // Adjust visibility trigger point

        if (sectionPosition < screenPosition) {
            aboutSection.classList.add("visible"); // Show when scrolled down
        } else {
            aboutSection.classList.remove("visible"); // Hide when scrolled up
        }
    }

    window.addEventListener("scroll", toggleVisibilityOnScroll);
});

document.addEventListener("DOMContentLoaded", function () {
    const introText = document.querySelector(".intro");

    function checkScroll() {
        let rect = introText.getBoundingClientRect();
        let windowHeight = window.innerHeight;

        if (rect.top < windowHeight * 0.6 && rect.bottom > 0) {
            introText.classList.add("fade-in");
            introText.classList.remove("fade-out");
        } else {
            introText.classList.add("fade-out");
            introText.classList.remove("fade-in");
        }
    }

    window.addEventListener("scroll", checkScroll);
    checkScroll(); // Run initially to check on page load
});



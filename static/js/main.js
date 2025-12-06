// MAIN.JS — General UI behavior and helpers

document.addEventListener("DOMContentLoaded", () => {
    const path = window.location.pathname;
    const navLinks = document.querySelectorAll(".nav-link");

    navLinks.forEach(link => {
        if (link.href.includes(path)) {
            link.classList.add("active");
        }
    });
});

// Add Question Page — Tab switch → set question type
const questionTabs = document.querySelectorAll('[data-bs-toggle="tab"]');
const hiddenTypeInput = document.getElementById("questionType");

if (questionTabs && hiddenTypeInput) {
    questionTabs.forEach(tab => {
        tab.addEventListener("shown.bs.tab", event => {
            const target = event.target.getAttribute("data-bs-target");

            switch (target) {
                case "#mcq": hiddenTypeInput.value = "MCQ"; break;
                case "#tf": hiddenTypeInput.value = "TF"; break;
                case "#short": hiddenTypeInput.value = "Short"; break;
                case "#fill": hiddenTypeInput.value = "Fill"; break;
                case "#match": hiddenTypeInput.value = "Match"; break;
                case "#image": hiddenTypeInput.value = "Image"; break;
            }
        });
    });
}

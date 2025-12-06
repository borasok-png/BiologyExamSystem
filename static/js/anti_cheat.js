// ANTI CHEAT — Detect tab switching, auto-submit after violations

let violationCount = 0;
const maxViolations = 3;

document.addEventListener("visibilitychange", () => {
    if (document.hidden) {
        violationCount++;

        const vInput = document.getElementById("violations");
        if (vInput) vInput.value = violationCount;

        alert(`You switched tabs! Violation ${violationCount}/${maxViolations}`);

        if (violationCount >= maxViolations) {
            alert("Too many violations. Your exam will be submitted.");
            document.getElementById("examForm").submit();
        }
    }
});

// Warning before leaving exam page
window.addEventListener("beforeunload", function(e) {
    return "Are you sure you want to leave the exam?";
});

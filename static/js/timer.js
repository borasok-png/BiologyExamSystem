// TIMER.JS — Countdown exam timer

document.addEventListener("DOMContentLoaded", () => {
    const durationElement = document.getElementById("duration");
    const timerDisplay = document.getElementById("timerText");

    if (!durationElement || !timerDisplay) return;

    let totalSeconds = parseInt(durationElement.value) * 60;

    function updateTimer() {
        let minutes = Math.floor(totalSeconds / 60);
        let seconds = totalSeconds % 60;

        timerDisplay.textContent =
            `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;

        if (totalSeconds <= 0) {
            clearInterval(timerInterval);
            alert("Time is up! Your exam will now be submitted.");
            document.getElementById("examForm").submit();
        }

        totalSeconds--;
    }

    updateTimer();
    const timerInterval = setInterval(updateTimer, 1000);
});

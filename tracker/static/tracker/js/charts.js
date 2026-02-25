document.addEventListener("DOMContentLoaded", function () {
    const expenseCanvas = document.getElementById("expenseCategoryChart");
    if (expenseCanvas && window.Chart) {
        try {
            const labels = JSON.parse(expenseCanvas.dataset.labels || "[]");
            const values = JSON.parse(expenseCanvas.dataset.values || "[]");

            new Chart(expenseCanvas.getContext("2d"), {
                type: "pie",
                data: {
                    labels: labels,
                    datasets: [
                        {
                            data: values,
                            backgroundColor: [
                                "#3b82f6",
                                "#10b981",
                                "#f97316",
                                "#ef4444",
                                "#6366f1"
                            ],
                            borderWidth: 1,
                            borderColor: "#ffffff"
                        }
                    ]
                },
                options: {
                    plugins: {
                        legend: {
                            position: "bottom"
                        }
                    }
                }
            });
        } catch (e) {
            console.error("Error initializing expense category chart", e);
        }
    }

    // Health score donut
    const healthCanvas = document.getElementById("healthScoreChart");
    if (healthCanvas && window.Chart) {
        try {
            const score = parseFloat(healthCanvas.dataset.score || "0");
            const colorKey = healthCanvas.dataset.color || "danger";
            const colorMap = {
                success: "#16a34a",
                primary: "#0ea5e9",
                warning: "#f59e0b",
                danger: "#ef4444",
            };
            const c = colorMap[colorKey] || "#ef4444";
            new Chart(healthCanvas.getContext("2d"), {
                type: "doughnut",
                data: {
                    labels: ["Score", "Remaining"],
                    datasets: [
                        {
                            data: [score, Math.max(100 - score, 0)],
                            backgroundColor: [c, "#e6edf3"],
                            hoverOffset: 6,
                            cutout: "75%",
                        },
                    ],
                },
                options: {
                    animation: { animateRotate: true, duration: 1200 },
                    plugins: { legend: { display: false } },
                },
            });
        } catch (e) {
            console.error("Error initializing health score chart", e);
        }
    }

    // Projected balance small chart
    const projectedCanvas = document.getElementById("projectedBalanceChart");
    if (projectedCanvas && window.Chart) {
        try {
            const predicted = parseFloat(projectedCanvas.dataset.predicted || "0");
            const ctx = projectedCanvas.getContext("2d");
            const gradient = ctx.createLinearGradient(0, 0, 0, 200);
            gradient.addColorStop(0, "rgba(14,165,233,0.6)");
            gradient.addColorStop(1, "rgba(14,165,233,0.05)");

            new Chart(ctx, {
                type: "line",
                data: {
                    labels: ["-2m", "-1m", "Now", "+1m"],
                    datasets: [
                        {
                            label: "Projected Balance",
                            data: [0, 0, parseFloat(document.querySelector('#projectedBalanceChart')?.dataset?.predicted || 0), predicted],
                            fill: true,
                            backgroundColor: gradient,
                            borderColor: "#0ea5e9",
                            tension: 0.35,
                            pointRadius: 0,
                        },
                    ],
                },
                options: {
                    responsive: true,
                    plugins: { legend: { display: false } },
                    scales: { y: { beginAtZero: true } },
                    animation: { duration: 900 }
                },
            });
        } catch (e) {
            console.error("Error initializing projected balance chart", e);
        }
    }

    // Dark mode toggle persistence
    const darkToggle = document.getElementById('darkModeToggle');
    if (darkToggle) {
        const applyMode = (mode) => {
            if (mode === 'dark') document.documentElement.classList.add('dark');
            else document.documentElement.classList.remove('dark');
        };
        const stored = localStorage.getItem('sb_dark_mode');
        if (stored) applyMode(stored);
        darkToggle.addEventListener('click', function () {
            const isDark = document.documentElement.classList.toggle('dark');
            localStorage.setItem('sb_dark_mode', isDark ? 'dark' : 'light');
        });
    }

    // PDF download removed

    const incomeExpenseCanvas = document.getElementById("incomeExpenseChart");
    if (incomeExpenseCanvas && window.Chart) {
        try {
            const labels = JSON.parse(incomeExpenseCanvas.dataset.labels || "[]");
            const values = JSON.parse(incomeExpenseCanvas.dataset.values || "[]");

            new Chart(incomeExpenseCanvas.getContext("2d"), {
                type: "bar",
                data: {
                    labels: labels,
                    datasets: [
                        {
                            label: "Amount",
                            data: values,
                            backgroundColor: [
                                "#16a34a",
                                "#dc2626"
                            ],
                            borderRadius: 6
                        }
                    ]
                },
                options: {
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    },
                    plugins: {
                        legend: {
                            display: false
                        }
                    }
                }
            });
        } catch (e) {
            console.error("Error initializing income vs expense chart", e);
        }
    }
});


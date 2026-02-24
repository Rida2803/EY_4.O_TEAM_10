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


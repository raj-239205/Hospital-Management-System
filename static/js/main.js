document.addEventListener('DOMContentLoaded', function() {
    
    // --- Theme System ---
    // Single bright healthcare mode is active. No switcher required.

    // --- Sidebar Toggle ---
    const menuToggle = document.getElementById('menu-toggle');
    const wrapper = document.getElementById('wrapper');
    if (menuToggle && wrapper) {
        menuToggle.addEventListener('click', function(e) {
            e.preventDefault();
            wrapper.classList.toggle('toggled');
        });
    }

    // --- Toast Notification Handler ---
    const toastElList = [].slice.call(document.querySelectorAll('.toast'));
    const toastList = toastElList.map(function(toastEl) {
        return new bootstrap.Toast(toastEl, { delay: 4000 });
    });
    toastList.forEach(toast => toast.show());

    // --- Client Form Validations ---
    const forms = document.querySelectorAll('.needs-validation');
    Array.prototype.slice.call(forms).forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });

    // --- Dynamic Specialization Selection ---
    const specializationSelect = document.getElementById('specialization-select');
    const doctorSelect = document.getElementById('doctor-select');
    
    if (specializationSelect && doctorSelect) {
        specializationSelect.addEventListener('change', function() {
            const spec = this.value;
            if (!spec) {
                doctorSelect.innerHTML = '<option value="">-- Select Doctor --</option>';
                return;
            }
            
            doctorSelect.innerHTML = '<option value="">Loading doctors...</option>';
            
            fetch(`/api/doctors/specialization/${encodeURIComponent(spec)}`)
                .then(response => response.json())
                .then(doctors => {
                    doctorSelect.innerHTML = '<option value="">-- Select Doctor --</option>';
                    doctors.forEach(doc => {
                        const option = document.createElement('option');
                        option.value = doc.id;
                        option.textContent = `Dr. ${doc.name}`;
                        doctorSelect.appendChild(option);
                    });
                })
                .catch(err => {
                    console.error("Error fetching doctors:", err);
                    doctorSelect.innerHTML = '<option value="">Error loading doctors</option>';
                });
        });
    }

    // --- Chart.js Widgets Loader (Healthcare Light Theme) ---
    function renderDashboardCharts() {
        const revenueCtx = document.getElementById('revenueChart');
        const apptCtx = document.getElementById('appointmentChart');
        const bloodCtx = document.getElementById('bloodGroupChart');

        if (!revenueCtx && !apptCtx && !bloodCtx) return;

        const getStyleVal = (varName, fallback) => {
            return getComputedStyle(document.body).getPropertyValue(varName).trim() || fallback;
        };

        const gridColor = getStyleVal('--border-color', '#E5E7EB');
        const textColor = getStyleVal('--text-muted', '#94A3B8');
        const primaryColor = getStyleVal('--primary-color', '#2563EB');
        const secondaryTextColor = getStyleVal('--text-secondary', '#6B7280');

        fetch('/api/dashboard/charts')
            .then(res => res.json())
            .then(data => {
                // 1. Revenue Line Chart
                if (revenueCtx) {
                    new Chart(revenueCtx, {
                        type: 'line',
                        data: {
                            labels: data.revenue.labels,
                            datasets: [{
                                label: 'Monthly Revenue ($)',
                                data: data.revenue.values,
                                borderColor: primaryColor,
                                backgroundColor: 'rgba(37, 99, 235, 0.06)',
                                borderWidth: 3,
                                fill: true,
                                tension: 0.35
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: { legend: { display: false } },
                            scales: {
                                y: { 
                                    beginAtZero: true, 
                                    grid: { color: gridColor },
                                    ticks: { color: textColor, font: { family: 'Inter', size: 11 } }
                                },
                                x: { 
                                    grid: { display: false },
                                    ticks: { color: textColor, font: { family: 'Inter', size: 11 } }
                                }
                            }
                        }
                    });
                }

                // 2. Appointment Doughnut Chart
                if (apptCtx) {
                    new Chart(apptCtx, {
                        type: 'doughnut',
                        data: {
                            labels: data.appointments.labels,
                            datasets: [{
                                data: data.appointments.values,
                                backgroundColor: ['#3B82F6', '#22C55E', '#EF4444'],
                                hoverOffset: 4
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {
                                legend: { 
                                    position: 'bottom', 
                                    labels: { 
                                        boxWidth: 12,
                                        color: secondaryTextColor,
                                        font: { family: 'Inter', size: 11 }
                                    } 
                                }
                            }
                        }
                    });
                }

                // 3. Patient Blood Groups Bar Chart
                if (bloodCtx) {
                    new Chart(bloodCtx, {
                        type: 'bar',
                        data: {
                            labels: data.blood_groups.labels,
                            datasets: [{
                                label: 'Patients',
                                data: data.blood_groups.values,
                                backgroundColor: primaryColor,
                                borderRadius: 6
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: { legend: { display: false } },
                            scales: {
                                y: { 
                                    beginAtZero: true, 
                                    grid: { color: gridColor },
                                    ticks: { color: textColor, font: { family: 'Inter', size: 11 } }
                                },
                                x: { 
                                    grid: { display: false },
                                    ticks: { color: textColor, font: { family: 'Inter', size: 11 } }
                                }
                            }
                        }
                    });
                }
            })
            .catch(err => console.error("Error loading charts:", err));
    }

    // Run initially
    renderDashboardCharts();
});

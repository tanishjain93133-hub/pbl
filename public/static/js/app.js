// SmartPark — Application JavaScript (PBL-I)

document.addEventListener('DOMContentLoaded', function () {
    // 1. Auto-dismiss alerts/toasts after 5 seconds
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(alert => {
        setTimeout(() => {
            try {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            } catch (e) {}
        }, 5000);
    });

    // 2. Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // 3. Client-side booking time validation
    const bookingForm = document.getElementById('slotBookingForm');
    if (bookingForm) {
        bookingForm.addEventListener('submit', function (e) {
            const startTime = document.getElementById('modalStartTime')?.value;
            const endTime = document.getElementById('modalEndTime')?.value;
            const bookingDate = document.getElementById('modalBookingDate')?.value;

            if (startTime && endTime && startTime >= endTime) {
                e.preventDefault();
                showCustomToast('End time must be strictly after start time.', 'danger');
                return false;
            }

            if (bookingDate) {
                const today = new Date().toISOString().split('T')[0];
                if (bookingDate < today) {
                    e.preventDefault();
                    showCustomToast('Booking date cannot be in the past.', 'danger');
                    return false;
                }
            }
        });
    }
});

// Password visibility toggle function
function togglePassword(inputId, toggleIconId) {
    const input = document.getElementById(inputId);
    const icon = document.getElementById(toggleIconId);
    if (!input || !icon) return;

    if (input.type === 'password') {
        input.type = 'text';
        icon.classList.remove('bi-eye');
        icon.classList.add('bi-eye-slash');
    } else {
        input.type = 'password';
        icon.classList.remove('bi-eye-slash');
        icon.classList.add('bi-eye');
    }
}

// Open booking modal and populate slot data
function openBookingModal(slotId, slotNumber, section, floor, vehicleType) {
    const modalSlotId = document.getElementById('modalSlotId');
    const modalSlotNumber = document.getElementById('modalSlotNumber');
    const modalSlotDetails = document.getElementById('modalSlotDetails');

    if (modalSlotId) modalSlotId.value = slotId;
    if (modalSlotNumber) modalSlotNumber.textContent = slotNumber;
    if (modalSlotDetails) modalSlotDetails.textContent = `${section} • ${floor} • ${vehicleType}`;

    const modalEl = document.getElementById('bookSlotModal');
    if (modalEl) {
        const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
        modal.show();
    }
}

// Dynamic toast notification generator
function showCustomToast(message, type = 'info') {
    let container = document.getElementById('toastContainer');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toastContainer';
        container.className = 'toast-container-custom';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `alert alert-${type} alert-dismissible fade show shadow-lg d-flex align-items-center gap-2 mb-0`;
    toast.role = 'alert';
    
    let iconClass = 'bi-info-circle-fill';
    if (type === 'success') iconClass = 'bi-check-circle-fill';
    if (type === 'danger') iconClass = 'bi-exclamation-triangle-fill';
    if (type === 'warning') iconClass = 'bi-exclamation-circle-fill';

    toast.innerHTML = `
        <i class="bi ${iconClass} fs-5"></i>
        <div class="flex-grow-1">${message}</div>
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 4500);
}

// ==========================================================================
// 4. SmartPark — Car Entrance Starting Point Animation Controller
// ==========================================================================

let introTimeout1, introTimeout2, introTimeout3;

function initCarIntroAnimation(force = false) {
    const overlay = document.getElementById('carIntroOverlay');
    if (!overlay) return;

    const isHomePage = (window.location.pathname === '/' || window.location.pathname === '');
    const hasPlayed = sessionStorage.getItem('smartpark_intro_played');

    if (!force && (!isHomePage || hasPlayed)) {
        overlay.style.display = 'none';
        return;
    }

    // Clear previous timeouts if replayed
    clearTimeout(introTimeout1);
    clearTimeout(introTimeout2);
    clearTimeout(introTimeout3);

    // Prepare fresh visual state
    overlay.style.display = 'flex';
    overlay.classList.remove('intro-fade-out');

    const car = document.getElementById('introCar');
    const fill = document.getElementById('introProgressFill');
    const statusBadge = document.getElementById('introHudStatus');
    const gateArm = document.getElementById('introBarrierArm');
    const gateLight = document.getElementById('introGateLight');
    const scannerBeam = document.getElementById('introScannerBeam');

    if (fill) fill.style.width = '0%';
    if (gateArm) gateArm.classList.remove('open');
    if (gateLight) gateLight.classList.remove('granted');
    if (scannerBeam) scannerBeam.classList.remove('scanning');
    
    if (statusBadge) {
        statusBadge.classList.remove('granted');
        statusBadge.innerHTML = '<span class="spinner-grow spinner-grow-sm me-1 text-info"></span> DETECTING VEHICLE APPROACH...';
    }

    // Restart car drive animation
    if (car) {
        car.style.animation = 'none';
        void car.offsetWidth; // trigger reflow
        car.style.animation = 'carEnterDrive 2.6s cubic-bezier(0.2, 0.8, 0.25, 1) forwards';
    }

    // Fill progress gauge
    setTimeout(() => {
        if (fill) fill.style.width = '100%';
    }, 60);

    // Step 1: RFID & Laser Scanning vehicle license plate
    introTimeout1 = setTimeout(() => {
        if (scannerBeam) scannerBeam.classList.add('scanning');
        if (statusBadge) {
            statusBadge.innerHTML = '<i class="bi bi-upc-scan me-1 text-warning"></i> AI SCANNING: GJ-01-SP-2026...';
        }
    }, 750);

    // Step 2: Access Granted & Boom barrier arm lifts up
    introTimeout2 = setTimeout(() => {
        if (scannerBeam) scannerBeam.classList.remove('scanning');
        if (gateArm) gateArm.classList.add('open');
        if (gateLight) gateLight.classList.add('granted');
        if (statusBadge) {
            statusBadge.classList.add('granted');
            statusBadge.innerHTML = '<i class="bi bi-check-circle-fill me-1 text-success"></i> ACCESS GRANTED • BAY A-01 ALLOCATED';
        }
    }, 1500);

    // Step 3: Smooth website open & blur fade out
    introTimeout3 = setTimeout(() => {
        closeCarIntroOverlay();
    }, 2700);
}

function closeCarIntroOverlay() {
    clearTimeout(introTimeout1);
    clearTimeout(introTimeout2);
    clearTimeout(introTimeout3);

    const overlay = document.getElementById('carIntroOverlay');
    if (!overlay) return;

    overlay.classList.add('intro-fade-out');
    sessionStorage.setItem('smartpark_intro_played', 'true');

    setTimeout(() => {
        overlay.style.display = 'none';
    }, 850);
}

function replayCarIntro() {
    initCarIntroAnimation(true);
}

// Bind initialization and keyboard skip
document.addEventListener('DOMContentLoaded', function () {
    initCarIntroAnimation(false);

    const skipBtn = document.getElementById('introSkipBtn');
    if (skipBtn) {
        skipBtn.addEventListener('click', function (e) {
            e.preventDefault();
            closeCarIntroOverlay();
        });
    }

    // ESC key skips intro instantly
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' || e.key === 'Esc') {
            const overlay = document.getElementById('carIntroOverlay');
            if (overlay && overlay.style.display !== 'none' && !overlay.classList.contains('intro-fade-out')) {
                closeCarIntroOverlay();
            }
        }
    });
});

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
// 4. SmartPark — Mercedes/BMW Autonomous Parking Intro Animation Controller
//    Phase 1: Car approaches campus parking deck from left
//    Phase 2: LiDAR activates, amber turn signals blink
//    Phase 3: Car decelerates, steers into BAY A-01 lane
//    Phase 4: Car parks, brake lights flare, sensor turns red
//    Phase 5: HUD shows PARKED & RESERVED
//    Phase 6: Overlay scales & dissolves into website
// ==========================================================================

let introTimeouts = [];

function clearIntroTimeouts() {
    introTimeouts.forEach(t => clearTimeout(t));
    introTimeouts = [];
}

function initCarIntroAnimation(force = false) {
    const overlay = document.getElementById('carIntroOverlay');
    if (!overlay) return;

    const isHomePage = (window.location.pathname === '/' || window.location.pathname === '');
    const hasPlayed = sessionStorage.getItem('smartpark_intro_played');

    if (!force && (!isHomePage || hasPlayed)) {
        overlay.style.display = 'none';
        return;
    }

    clearIntroTimeouts();

    // Prepare fresh visual state
    overlay.style.display = 'flex';
    overlay.classList.remove('intro-fade-out');

    // Gather all element refs
    const car          = document.getElementById('introCar');
    const fill         = document.getElementById('introProgressFill');
    const statusBadge  = document.getElementById('introHudStatus');
    const hudTitle     = document.getElementById('introHudTitle');
    const hudSub       = document.getElementById('introHudSub');
    const sensorOrbA01 = document.getElementById('sensorOrbA01');
    const sensorTextA01= document.getElementById('sensorTextA01');
    const stencilA01   = document.getElementById('stencilA01');
    const scannerHolo  = document.getElementById('scannerHoloA01');
    const tailLight    = document.getElementById('carTailLight');
    const gantryStatus = document.getElementById('gantryDeckStatus');
    const gantryAuto   = document.getElementById('gantryAutopilotMode');

    // ——— RESET all elements ———
    if (fill) fill.style.width = '0%';
    if (sensorOrbA01)  { sensorOrbA01.className = 'sensor-orb orb-green'; }
    if (sensorTextA01) { sensorTextA01.textContent = 'BAY A-01 [VACANT]'; }
    if (scannerHolo)   { scannerHolo.classList.remove('active'); }
    if (tailLight)     { tailLight.classList.remove('braking'); }
    if (gantryStatus)  { gantryStatus.textContent = '1 BAY VACANT'; gantryStatus.className = 'gantry-val text-success'; }
    if (gantryAuto)    { gantryAuto.textContent = 'SCANNING LOT...'; gantryAuto.className = 'gantry-val text-warning'; }

    if (statusBadge) {
        statusBadge.classList.remove('granted');
        statusBadge.innerHTML = '<span class="spinner-grow spinner-grow-sm me-1 text-info"></span> MERCEDES-BENZ / BMW AI VALET CONNECTED';
    }
    if (hudTitle) hudTitle.textContent = 'Approaching Campus Parking Deck';
    if (hudSub)   hudSub.textContent   = 'Automated LiDAR Bay Detection & Autonomous Self-Parking';

    // ——— Restart Mercedes drive animation ———
    if (car) {
        car.style.animation = 'none';
        void car.offsetWidth; // force reflow
        car.style.animation = 'mercedesDriveIn 4.5s cubic-bezier(0.15, 0.85, 0.3, 1) forwards';
    }

    // ——— Progress bar fills over the whole animation duration ———
    introTimeouts.push(setTimeout(() => {
        if (fill) fill.style.width = '100%';
    }, 80));

    // ——— PHASE 1 (t=0.8s): LiDAR activates, scanning campus deck ———
    introTimeouts.push(setTimeout(() => {
        if (gantryAuto) { gantryAuto.textContent = 'AI LIDAR ACTIVE'; gantryAuto.className = 'gantry-val text-info'; }
        if (statusBadge) {
            statusBadge.innerHTML = '<i class="bi bi-radar me-1 text-info"></i> LIDAR SCAN: DETECTING BAY A-01...';
        }
        if (hudTitle) hudTitle.textContent = 'LiDAR Sweep — Locating Free Bay';
    }, 800));

    // ——— PHASE 2 (t=1.6s): Bay A-01 detected, scanner hologram activates, amber blinker starts ———
    introTimeouts.push(setTimeout(() => {
        if (scannerHolo) scannerHolo.classList.add('active');
        if (statusBadge) {
            statusBadge.innerHTML = '<i class="bi bi-geo-alt-fill me-1 text-warning"></i> BAY A-01 IDENTIFIED — PLOTTING TRAJECTORY';
        }
        if (hudTitle) hudTitle.textContent = 'Bay A-01 Detected — Activating Turn Signals';
        if (hudSub)   hudSub.textContent   = 'Amber LED turn indicators engaged • Steering into bay lane';
        if (gantryAuto) { gantryAuto.textContent = 'TRAJECTORY MAPPED'; gantryAuto.className = 'gantry-val text-warning'; }
    }, 1600));

    // ——— PHASE 3 (t=2.5s): Deceleration, car starts turning into bay ———
    introTimeouts.push(setTimeout(() => {
        if (statusBadge) {
            statusBadge.innerHTML = '<i class="bi bi-arrow-up-right-square-fill me-1 text-warning"></i> AUTONOMOUS STEERING — ENTERING BAY A-01';
        }
        if (hudTitle) hudTitle.textContent = 'Steering into Bay A-01';
        if (hudSub)   hudSub.textContent   = 'Precision reverse-parking maneuver in progress...';
    }, 2500));

    // ——— PHASE 4 (t=3.3s): Car is parking — brake lights flare, sensor turns red/occupied ———
    introTimeouts.push(setTimeout(() => {
        if (tailLight) tailLight.classList.add('braking');
        if (sensorOrbA01) { sensorOrbA01.className = 'sensor-orb orb-red'; }
        if (sensorTextA01) { sensorTextA01.textContent = 'BAY A-01 [PARKED]'; }
        if (stencilA01)    { stencilA01.textContent = '✓ GJ-01-SP'; }
        if (gantryStatus)  { gantryStatus.textContent = '0 BAYS VACANT'; gantryStatus.className = 'gantry-val text-danger'; }
        if (gantryAuto)    { gantryAuto.textContent = 'PARKED & LOCKED'; gantryAuto.className = 'gantry-val text-success'; }
        if (statusBadge) {
            statusBadge.classList.add('granted');
            statusBadge.innerHTML = '<i class="bi bi-patch-check-fill me-1 text-success"></i> PARKED & SECURED • BAY A-01 RESERVED';
        }
        if (hudTitle) hudTitle.textContent = 'Autonomous Parking Complete ✓';
        if (hudSub)   hudSub.textContent   = 'Vehicle locked • SmartPark slot GJ-01-SP confirmed';
    }, 3300));

    // ——— PHASE 5 (t=4.0s): Final welcome HUD, website about to reveal ———
    introTimeouts.push(setTimeout(() => {
        if (statusBadge) {
            statusBadge.innerHTML = '<i class="bi bi-stars me-1"></i> WELCOME TO SMARTPARK CAMPUS GATEWAY';
        }
        if (hudTitle) hudTitle.textContent = '🏁 PARKED & RESERVED • Welcome to SmartPark';
        if (hudSub)   hudSub.textContent   = 'Campus parking managed by AI — Enter your dashboard';
    }, 4000));

    // ——— PHASE 6 (t=5.2s): Smooth scale-up & blur dissolve into homepage ———
    introTimeouts.push(setTimeout(() => {
        closeCarIntroOverlay();
    }, 5200));
}

function closeCarIntroOverlay() {
    clearIntroTimeouts();

    const overlay = document.getElementById('carIntroOverlay');
    if (!overlay) return;

    overlay.classList.add('intro-fade-out');
    sessionStorage.setItem('smartpark_intro_played', 'true');

    setTimeout(() => {
        overlay.style.display = 'none';
    }, 900);
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

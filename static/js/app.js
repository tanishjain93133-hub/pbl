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

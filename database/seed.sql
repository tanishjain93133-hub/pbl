-- SmartPark: Seed Data
-- Default Admin, Sample Users, Vehicles, Parking Slots, Bookings, and History

USE smart_parking;

-- Clear previous data in reverse dependency order
SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE parking_history;
TRUNCATE TABLE bookings;
TRUNCATE TABLE parking_slots;
TRUNCATE TABLE vehicles;
TRUNCATE TABLE users;
SET FOREIGN_KEY_CHECKS = 1;

-- 1. Insert Users (Admin + 2 Sample Users)
-- Admin Password: 'Admin@123'
-- User Password: 'User@123'
INSERT INTO users (id, name, email, phone, password_hash, role, created_at) VALUES
(1, 'System Administrator', 'admin@smartpark.com', '9876543210', 'scrypt:32768:8:1$aXPQhMxNjRD3RG7X$00731b56b2069c58c72cc5fdd11f75b918c03bd830b46a735191d9dbf74ae0ddf3ea7e65d67075679988ec0c241a4628439b64b0faf1e12eb6b35b1b178ddccb', 'admin', NOW()),
(2, 'Rahul Sharma', 'rahul.sharma@example.com', '9898012345', 'scrypt:32768:8:1$jf0o9yGCQXNKYUcq$32c8e5421848e7688a0a7ed6779fe33c06beaa821f1dac1542f5862456777244faf6862c57b5790eda6009d5c01288bcf24e81f1d9e7de04f831b1383592dca6', 'user', NOW()),
(3, 'Priya Patel', 'priya.patel@example.com', '9825098765', 'scrypt:32768:8:1$jf0o9yGCQXNKYUcq$32c8e5421848e7688a0a7ed6779fe33c06beaa821f1dac1542f5862456777244faf6862c57b5790eda6009d5c01288bcf24e81f1d9e7de04f831b1383592dca6', 'user', NOW());

-- 2. Insert Sample Vehicles
INSERT INTO vehicles (id, user_id, vehicle_number, vehicle_type, vehicle_model, created_at) VALUES
(1, 2, 'GJ01AB1234', 'Car', 'Honda City (Sedan)', NOW()),
(2, 2, 'GJ01CD5678', 'Bike', 'Royal Enfield Classic 350', NOW()),
(3, 3, 'MH02EF9012', 'Car', 'Hyundai Creta (SUV)', NOW()),
(4, 3, 'MH02GH3456', 'Scooter', 'Honda Activa 6G', NOW());

-- 3. Insert Parking Slots (14 slots across sections and floors)
INSERT INTO parking_slots (id, slot_number, section, floor, vehicle_type, status, created_at) VALUES
(1, 'A01', 'Section A - North Wing', 'Ground Floor', 'Car', 'available', NOW()),
(2, 'A02', 'Section A - North Wing', 'Ground Floor', 'Car', 'occupied', NOW()),
(3, 'A03', 'Section A - North Wing', 'Ground Floor', 'Car', 'available', NOW()),
(4, 'A04', 'Section A - North Wing', 'Ground Floor', 'Car', 'available', NOW()),
(5, 'A05', 'Section A - North Wing', 'Ground Floor', 'Bike', 'available', NOW()),
(6, 'A06', 'Section A - North Wing', 'Ground Floor', 'Bike', 'maintenance', NOW()),
(7, 'B01', 'Section B - Central Block', '1st Floor', 'Car', 'available', NOW()),
(8, 'B02', 'Section B - Central Block', '1st Floor', 'Car', 'occupied', NOW()),
(9, 'B03', 'Section B - Central Block', '1st Floor', 'Car', 'available', NOW()),
(10, 'B04', 'Section B - Central Block', '1st Floor', 'Bike', 'available', NOW()),
(11, 'B05', 'Section B - Central Block', '1st Floor', 'Scooter', 'available', NOW()),
(12, 'B06', 'Section B - Central Block', '1st Floor', 'Car', 'available', NOW()),
(13, 'C01', 'Section C - East Wing', 'Basement', 'Car', 'available', NOW()),
(14, 'C02', 'Section C - East Wing', 'Basement', 'Car', 'maintenance', NOW());

-- 4. Insert Sample Bookings
INSERT INTO bookings (id, user_id, vehicle_id, slot_id, booking_date, start_time, end_time, booking_status, created_at) VALUES
(1, 2, 1, 2, CURDATE(), '09:00:00', '18:00:00', 'active', NOW()),
(2, 3, 3, 8, CURDATE(), '10:30:00', '16:00:00', 'active', NOW()),
(3, 2, 2, 5, CURDATE() + INTERVAL 1 DAY, '11:00:00', '14:00:00', 'booked', NOW()),
(4, 3, 4, 11, CURDATE() - INTERVAL 1 DAY, '09:00:00', '13:00:00', 'completed', NOW() - INTERVAL 1 DAY);

-- 5. Insert Sample Parking History
INSERT INTO parking_history (id, booking_id, vehicle_number, slot_number, entry_time, exit_time, status, created_at) VALUES
(1, 1, 'GJ01AB1234', 'A02', CONCAT(CURDATE(), ' 09:05:00'), NULL, 'Active', NOW()),
(2, 2, 'MH02EF9012', 'B02', CONCAT(CURDATE(), ' 10:32:00'), NULL, 'Active', NOW()),
(3, 4, 'MH02GH3456', 'B05', CONCAT(CURDATE() - INTERVAL 1 DAY, ' 09:02:00'), CONCAT(CURDATE() - INTERVAL 1 DAY, ' 13:04:00'), 'Completed', NOW() - INTERVAL 1 DAY),
(4, NULL, 'GJ01CD5678', 'A05', CONCAT(CURDATE() - INTERVAL 2 DAY, ' 08:30:00'), CONCAT(CURDATE() - INTERVAL 2 DAY, ' 17:15:00'), 'Completed', NOW() - INTERVAL 2 DAY);

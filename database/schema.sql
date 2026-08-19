-- SmartPark: Smart Parking Management System (PBL-I)
-- Database Schema for MySQL

CREATE DATABASE IF NOT EXISTS smart_parking;
USE smart_parking;

-- 1. Users Table
CREATE TABLE IF NOT EXISTS users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    phone VARCHAR(15) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('user', 'admin') DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2. Vehicles Table
CREATE TABLE IF NOT EXISTS vehicles (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    vehicle_number VARCHAR(20) NOT NULL,
    vehicle_type VARCHAR(30) NOT NULL,
    vehicle_model VARCHAR(50) DEFAULT 'Standard',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_vehicles (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. Parking Slots Table
CREATE TABLE IF NOT EXISTS parking_slots (
    id INT PRIMARY KEY AUTO_INCREMENT,
    slot_number VARCHAR(20) UNIQUE NOT NULL,
    section VARCHAR(50) NOT NULL,
    floor VARCHAR(20) NOT NULL,
    vehicle_type VARCHAR(30) NOT NULL DEFAULT 'Car',
    status ENUM('available', 'occupied', 'maintenance') DEFAULT 'available',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_slot_status (status),
    INDEX idx_slot_section (section)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4. Bookings Table
CREATE TABLE IF NOT EXISTS bookings (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    vehicle_id INT NOT NULL,
    slot_id INT NOT NULL,
    booking_date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    booking_status ENUM('booked', 'active', 'completed', 'cancelled') DEFAULT 'booked',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (vehicle_id) REFERENCES vehicles(id) ON DELETE CASCADE,
    FOREIGN KEY (slot_id) REFERENCES parking_slots(id) ON DELETE RESTRICT,
    INDEX idx_booking_slot_date (slot_id, booking_date),
    INDEX idx_booking_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 5. Parking History Table
CREATE TABLE IF NOT EXISTS parking_history (
    id INT PRIMARY KEY AUTO_INCREMENT,
    booking_id INT NULL,
    vehicle_number VARCHAR(20) NOT NULL,
    slot_number VARCHAR(20) NOT NULL,
    entry_time DATETIME NULL,
    exit_time DATETIME NULL,
    status VARCHAR(30) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_history_vehicle (vehicle_number),
    INDEX idx_history_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

import unittest
import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from init_db import init_sqlite

class SmartParkTestCase(unittest.TestCase):
    def setUp(self):
        # Reset and seed database for isolated tests
        init_sqlite()
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def login_user(self, email='rahul.sharma@example.com', password='User@123'):
        return self.client.post('/login', data={
            'email': email,
            'password': password
        }, follow_redirects=True)

    def login_admin(self, email='admin@smartpark.com', password='Admin@123'):
        return self.client.post('/admin/login', data={
            'email': email,
            'password': password
        }, follow_redirects=True)

    def test_landing_page(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'SmartPark', response.data)
        self.assertIn(b'Smart Parking Management for a Smarter Campus', response.data)

    def test_future_scope_page(self):
        response = self.client.get('/future-scope')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'PBL-II', response.data)
        self.assertIn(b'Automatic Number Plate Recognition', response.data)

    def test_user_registration_and_login(self):
        # Register new user
        reg_response = self.client.post('/register', data={
            'name': 'Test Student',
            'email': 'test.student@campus.edu',
            'phone': '9876500000',
            'password': 'Password@123',
            'confirm_password': 'Password@123'
        }, follow_redirects=True)
        self.assertEqual(reg_response.status_code, 200)
        self.assertIn(b'Registration successful', reg_response.data)

        # Login with newly registered user
        login_response = self.login_user('test.student@campus.edu', 'Password@123')
        self.assertEqual(login_response.status_code, 200)
        self.assertIn(b'Hello, Test Student', login_response.data)

    def test_role_based_access_control(self):
        # Anonymous accessing admin dashboard should redirect
        res = self.client.get('/admin/dashboard', follow_redirects=True)
        self.assertIn(b'Admin Portal', res.data)

        # Regular user accessing admin dashboard should be blocked
        self.login_user('rahul.sharma@example.com', 'User@123')
        res = self.client.get('/admin/dashboard', follow_redirects=True)
        self.assertIn(b'Access denied', res.data)

    def test_vehicle_crud(self):
        self.login_user()
        
        # Add vehicle
        add_res = self.client.post('/vehicles/add', data={
            'vehicle_number': 'KA01XY9999',
            'vehicle_type': 'Car',
            'vehicle_model': 'Tata Nexon'
        }, follow_redirects=True)
        self.assertEqual(add_res.status_code, 200)
        self.assertIn(b'KA01XY9999', add_res.data)

        # Edit vehicle
        edit_res = self.client.post('/vehicles/edit/1', data={
            'vehicle_number': 'GJ01AB1234',
            'vehicle_type': 'Car',
            'vehicle_model': 'Honda City 2026 Edition'
        }, follow_redirects=True)
        self.assertEqual(edit_res.status_code, 200)
        self.assertIn(b'updated successfully', edit_res.data)

    def test_parking_slot_booking_and_overlap_prevention(self):
        self.login_user()

        # Slot 1 (A01) is available
        book_res = self.client.post('/booking/create', data={
            'slot_id': '1',
            'vehicle_id': '1',
            'booking_date': '2026-10-15',
            'start_time': '10:00',
            'end_time': '12:00'
        }, follow_redirects=True)
        self.assertEqual(book_res.status_code, 200)
        self.assertIn(b'Booking Confirmed!', book_res.data)

        # Overlap Test: Attempt to book the exact same slot on same date with overlapping time (11:00 to 13:00)
        overlap_res = self.client.post('/booking/create', data={
            'slot_id': '1',
            'vehicle_id': '1',
            'booking_date': '2026-10-15',
            'start_time': '11:00',
            'end_time': '13:00'
        }, follow_redirects=True)
        self.assertEqual(overlap_res.status_code, 200)
        self.assertIn(b'already booked on 2026-10-15', overlap_res.data)

    def test_admin_slot_management(self):
        self.login_admin()

        # Add new slot
        add_slot_res = self.client.post('/admin/slots/add', data={
            'slot_number': 'Z99',
            'section': 'Section Z - Executive Bay',
            'floor': 'Ground Floor',
            'vehicle_type': 'Car',
            'status': 'available'
        }, follow_redirects=True)
        self.assertEqual(add_slot_res.status_code, 200)
        self.assertIn(b'Z99', add_slot_res.data)

        # Edit slot
        edit_slot_res = self.client.post('/admin/slots/edit/1', data={
            'slot_number': 'A01',
            'section': 'Section A - North Wing',
            'floor': 'Ground Floor',
            'vehicle_type': 'Car',
            'status': 'maintenance'
        }, follow_redirects=True)
        self.assertEqual(edit_slot_res.status_code, 200)
        self.assertIn(b'details updated successfully', edit_slot_res.data)

    def test_admin_booking_status_update(self):
        self.login_admin()

        # Update booking 3 status to active
        status_res = self.client.post('/admin/bookings/3/status', data={
            'status': 'active'
        }, follow_redirects=True)
        self.assertEqual(status_res.status_code, 200)
        self.assertIn(b'status changed to', status_res.data)

if __name__ == '__main__':
    unittest.main()

import unittest
from app.main import create_app
from flask import json

class AuthAPITestCase(unittest.TestCase):
    def setUp(self):
        # Create a test client
        self.app = create_app('test')
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        
    def tearDown(self):
        # Remove the app context after each test
        self.app_context.pop()

    def test_register_success(self):
        """Test that a new user can register successfully"""
        user_data = {
            "username": "testuser7",
            "email": "test7@example.com",
            "password": "password123"
        }

        # Make a POST request to the register endpoint
        response = self.client.post('/auth/register-user', data=json.dumps(user_data), content_type='application/json')
        
        # Assert the response
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Registration successful', response.data)
        
    def test_register_duplicate_user(self):
        """Test that registration fails for duplicate user"""
        # First registration
        user_data = {
            "username": "testuser5",
            "email": "test5@example.com",
            "password": "password123"
        }
        self.client.post('/auth/register-user', data=json.dumps(user_data), content_type='application/json')

        # Try registering again with the same email
        response = self.client.post('/auth/register-user', data=json.dumps(user_data), content_type='application/json')
        
        # Assert the response for duplicate user
        self.assertEqual(response.status_code, 400)  # Assuming 400 for duplicate
        self.assertIn(b'already exists', response.data)
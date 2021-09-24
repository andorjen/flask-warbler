"""User View tests."""

import os
from test_message_model import TEST_USER_DATA
from unittest import TestCase

from models import db, connect_db, Message, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler_test"

# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class UserViewTestCase(TestCase):
    """Test views for users."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)

        self.testuser2 = User.signup(username="testuser2",
                                    email="test2@test.com",
                                    password="testuser2",
                                    image_url=None)
        db.session.commit()
        self.testuser.followers.append(self.testuser2)
        db.session.commit()
        self.test_user_id = self.testuser.id
        self.test_user2_id = self.testuser2.id

    def tearDown(self):
        """Clean up any fouled transaction."""
        db.session.rollback()

    def test_show_login_form(self):
        """Test for show login form successfully"""


        with self.client as c:

            resp = c.get("/login")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Log in</button>", html)

    
    def test_login(self):
        """Test for show login form successfully"""

        with self.client as c:
            resp = c.post("/login", data={
                "username": "testuser",
                "password": "testuser"
            }, follow_redirects=True)

            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("testuser", html)
    
    def test_fail_login(self):
        """test failed login with invalid credentials"""
        with self.client as c:
            resp = c.post("/login", data={
                "username": "testuser",
                "password": "otherpassword"
            }, follow_redirects=True)    

            html = resp.get_data(as_text=True)    
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Invalid credentials.", html)

    def test_logout(self):
        """test if user can log out after being logged in"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            resp = c.post('/logout', follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Log in</button>", html)


    def test_list_users(self):
        """test if the /users route show all users properly"""
        with self.client as c:
            resp = c.get('/users')
            html = resp.get_data(as_text=True)
            
            self.assertEqual(resp.status_code, 200)
            self.assertIn("testuser", html)
            self.assertIn("testuser2", html)  #test for specific features of the html

    def test_show_individual_user(self):
        """test to show individual user info page"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            resp = c.get(f'/users/{self.testuser.id}')
            html = resp.get_data(as_text=True)
        
            self.assertEqual(resp.status_code, 200)
            self.assertIn("testuser", html)
            self.assertIn("Edit Profile</a>", html)

    def test_show_individual_other_user(self):
        """test to show another individual user info page after logged in"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.get(f'/users/{self.test_user2_id}')
            html = resp.get_data(as_text=True)
                
            self.assertEqual(resp.status_code, 200)
            self.assertIn("testuser2", html)

    def test_user_following_page(self):
        """test user's following page content"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser2.id

            resp = c.get(f'/users/{self.test_user2_id}/following')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("testuser", html)
            self.assertIn("You are following these people</h1>", html)

    def test_user_followers_page(self):
        """test user's followers page content"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.get(f'/users/{self.test_user_id}/followers')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("testuser2", html)
            self.assertIn("Here are your followers</h1>", html)


    def test_user_followers_fail_page(self):
        """test unauthorized view case of user's followers page content"""
        with self.client as c:

            resp = c.get(f'/users/{self.test_user_id}/followers',
                        follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", html)

    def test_user_add_follow(self):
        """test if user could follow another user"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post(f'/users/follow/{self.test_user2_id}',
                        follow_redirects=True)  
            html = resp.get_data(as_text=True)  
            self.assertEqual(resp.status_code, 200)
            self.assertIn("testuser2", html)
            self.assertIn("You are following these people</h1>", html)

    def test_user_fail_add_follow(self):
        """test if invalid user could follow another user"""
        with self.client as c:

            resp = c.post(f'/users/follow/{self.test_user2_id}',
                        follow_redirects=True)  
            html = resp.get_data(as_text=True)  
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", html)

    def test_user_stop_follow(self):
        """test if user could unfollow another user"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser2.id

            resp = c.post(f'/users/stop-following/{self.test_user_id}',
                        follow_redirects=True)  
            html = resp.get_data(as_text=True)  
            self.assertEqual(resp.status_code, 200)
            self.assertNotIn("testuser ", html)
            self.assertIn("You are following these people</h1>", html)


    def test_user_fail_stop_follow(self):
        """test if invalid user could unfollow another user"""
        with self.client as c:

            resp = c.post(f'/users/follow/{self.test_user2_id}',
                        follow_redirects=True)  
            html = resp.get_data(as_text=True)  
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", html)


    def test_show_edit_user_profile(self):
        """test to see edit user's profile page"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            resp = c.get('/users/profile')
            html = resp.get_data(as_text=True)
        
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Edit Your Profile.</h2>", html)
            self.assertIn("Edit this user!</button>", html)
            self.assertIn("Cancel</a>", html)

    def test_show_user_fail_edit_profile(self):
        """test if invalid user could see edit user profile"""
        with self.client as c:

            resp = c.get('/users/profile',
                        follow_redirects=True)  
            html = resp.get_data(as_text=True)  
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Warbler</span>", html)

    def test_edit_user_profile(self):
        """test to edit user's profile page"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            resp = c.post('/users/profile',data={
                "username": "testuseredit",
                "email": "testedit@test.com",
                "password": "testuser"
            },follow_redirects=True)
            html = resp.get_data(as_text=True)
        
            self.assertEqual(resp.status_code, 200)
            self.assertIn("testuseredit", html)
            self.assertIn("Edit Profile</a>", html)

    def test_fail_edit_user_profile(self):
        """test to edit user's profile page with invalid password"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            resp = c.post('/users/profile',data={
                "username": "testuseredit",
                "email": "testedit@test.com",
                "password": "testuserfailpassword"
            },follow_redirects=True)
            html = resp.get_data(as_text=True)
        
            self.assertEqual(resp.status_code, 200)
            self.assertNotIn("testuseredit", html)
            self.assertIn("Invalid credentials to edit user", html)
    
    def test_delete_user_profile(self):
        """test to delete user's profile page"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser2.id
            resp = c.post('/users/delete',follow_redirects=True)
            html = resp.get_data(as_text=True)
        
            self.assertEqual(resp.status_code, 200)
            self.assertNotIn("testuser2", html)
            self.assertIn("Sign me up!</button>", html)
    

    def test_fail_delete_user_profile(self):
        """test to delete user's profile page"""

        with self.client as c:
            resp = c.post('/users/delete',follow_redirects=True)
            html = resp.get_data(as_text=True)
        
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", html)
       
"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


from app import app
import os
from unittest import TestCase

from models import db, User, Message, Follows
from sqlalchemy import exc

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler_test"

# Now we can import app


# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

TEST_USER_DATA = {
    "email": "test@test.com",
    "username": "testuser1",
    "password": "HASHED_PASSWORD1",
    "image_url": ""
}

TEST_USER_DATA2 = {
    "email": "test2@test.com",
    "username": "testuser2",
    "password": "HASHED_PASSWORD2",
    "image_url": ""
}

TEST_USER_DATA3 = {
    "email": "test3@test.com",
    "username": "testuser3",
    "password": "HASHED_PASSWORD3",
    "image_url": ""
}


class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        self.client = app.test_client()

        test_user = User.signup(**TEST_USER_DATA)
        test_user2 = User.signup(**TEST_USER_DATA2)
        db.session.commit()

        self.test_user = test_user
        self.test_user2 = test_user2

    def tearDown(self):
        """Clean up any fouled transaction."""
        db.session.rollback()

    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="testtest@test.com",
            username="testusertest",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)

    def test_user_repr(self):
        """test for the user repr method returning the correct string"""

        resp = self.test_user.__repr__()
        self.assertEqual(
            f"<User #{self.test_user.id}: testuser1, test@test.com>", resp)

    def test_user_is_following(self):
        """test for if user is following test_user"""

        self.test_user.following.append(self.test_user2)
        resp = self.test_user.is_following(self.test_user2)
        self.assertEqual(True, resp)

    def test_user_is_not_following(self):
        """test for if user is not following test_user"""

        resp = self.test_user.is_following(self.test_user2)
        self.assertEqual(False, resp)

    def test_user_is_followed_by(self):
        """test for if user is followed by test_user"""

        self.test_user.followers.append(self.test_user2)
        resp = self.test_user.is_followed_by(self.test_user2)
        self.assertEqual(True, resp)

    def test_user_is_not_followed_by(self):
        """test for if user is not followed by test_user"""

        resp = self.test_user.is_followed_by(self.test_user2)
        self.assertEqual(False, resp)

    def test_user_signup(self):
        """test if a new user is successfully created when given valid credentials"""
        new_user = User.signup(**TEST_USER_DATA3)
        self.assertTrue(new_user)

    def test_user_fail_signup(self):
        """test if a user creation fails when given invalid credentials"""

        User.signup(**TEST_USER_DATA)

        with self.assertRaises(exc.IntegrityError):
            db.session.commit()

    def test_user_authenticate(self):
        """test if authenticate user successes when given valid credentials"""

        resp = User.authenticate("testuser2", "HASHED_PASSWORD2")
        self.assertTrue(resp)

    def test_user_fail_authenticate(self):
        """test if authenticate user fails when given invalid credentials"""

        resp = User.authenticate("testuser2", "HASHED_PASSWORDNOTTHIS")
        self.assertFalse(resp)

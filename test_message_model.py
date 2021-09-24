"""Message model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py



import os
from unittest import TestCase

from models import db, User, Message


# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler_test"

# Now we can import app
from app import app

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

TEST_MESSAGE_DATA = "First Message"


TEST_MESSAGE_DATA2 = "Second Message"



class MessageModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        test_user = User.signup(**TEST_USER_DATA)
        test_user2 = User.signup(**TEST_USER_DATA2)
        db.session.commit()
        self.test_user = test_user
        self.test_user2 = test_user2

        test_message = Message(text=TEST_MESSAGE_DATA, user_id= self.test_user.id)
        test_message2 = Message(text=TEST_MESSAGE_DATA2, user_id= self.test_user2.id)
        db.session.add_all([test_message,test_message2])
        db.session.commit()

        self.test_message = test_message
        self.test_message2 = test_message2

    def tearDown(self):
        """Clean up any fouled transaction."""
        db.session.rollback()

    def test_message_author(self):
        """Test if author of message is correct user"""
        self.assertEqual(self.test_message.user_id, self.test_user.id)
        self.assertEqual(self.test_message2.user_id, self.test_user2.id)

    def test_message_model(self):
        """Does basic model work?"""

        m = Message(
            text="Test message",
            user_id=self.test_user.id
        )

        db.session.add(m)
        db.session.commit()

        self.assertEqual(len(self.test_user.messages), 2)

    def test_like_messages(self):
        """ Test for if message is liked by user"""
        self.test_user.liked_messages.append(self.test_message2)
        db.session.commit()

        self.assertIn(self.test_message2, self.test_user.liked_messages)  #test database directly

    def test_not_like_messages(self):
        """ Test for if message is not liked by user"""

        self.assertNotIn(self.test_message2, self.test_user.liked_messages)

"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from werkzeug import test

from models import db, connect_db, Message, User, LikedMessage

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


class MessageViewTestCase(TestCase):
    """Test views for messages."""

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

        test_message= Message(text="test message")
        self.testuser.messages.append(test_message)
        test_message2= Message(text="test message2")
        self.testuser2.messages.append(test_message2)
        db.session.commit()

        self.test_message = test_message
        self.test_message_id = test_message.id

        self.test_message2 = test_message2
        self.test_message_id2 = test_message2.id

    def tearDown(self):
        """Clean up any fouled transaction."""
        db.session.rollback()

    def test_add_message(self):
        """Can use add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.post("/messages/new", data={"text": "Hello"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            msg = Message.query.filter(Message.text=="Hello").one()
            self.assertEqual(msg.text, "Hello")

    def test_show_message_form(self):
        """Can we see message form"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.get("/messages/new")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Add my message!</button>", html)

    def test_show_message(self):
        """Can we see individual message?"""
        # QUESTION: we are unable to grab self.test_message.id 
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
           
            resp = c.get(f"/messages/{self.test_message_id}")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("test message</p>", html)


    def test_destroy_message(self):
        """Can we remove a message?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post(f"/messages/{self.test_message_id}/delete")

            self.assertEqual(resp.status_code, 302)

            msg = Message.query.filter(Message.text=="test message").one_or_none()
            self.assertIsNone(msg)


    def test_add_liked_message(self):
        """Can we add a liked message?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post(f"/messages/{self.test_message_id2}/like")

            self.assertEqual(resp.status_code, 302)

            msg = LikedMessage.query.one()
            self.assertEqual(self.test_message_id2, msg.message_id)

    def test_remove_liked_message(self):
        """Can we remove a liked message?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            liked = LikedMessage(message_id=self.test_message_id2, user_id=self.testuser.id)
            db.session.add(liked)
            db.session.commit()

            resp = c.post(f"/messages/{self.test_message_id2}/unlike")

            self.assertEqual(resp.status_code, 302)

            msg = LikedMessage.query.one_or_none()
            self.assertIsNone(msg)

    def test_show_liked_message(self):
        """Can we see users liked messages?"""
        
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
           
            liked = LikedMessage(message_id=self.test_message_id2, user_id=self.testuser.id)
            db.session.add(liked)
            db.session.commit()

            resp = c.get(f"/users/{self.testuser.id}/likes")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("test message2</p>", html)
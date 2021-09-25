"""Message View tests."""

from app import app, CURR_USER_KEY
from unittest import TestCase
from models import db, Message, User, LikedMessage
import os
os.environ['DATABASE_URL'] = "postgresql:///warbler_test"

db.create_all()

app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(
            username="testuser",
            email="test@test.com",
            password="testuser",
            image_url=None)

        self.testuser2 = User.signup(
            username="testuser2",
            email="test2@test.com",
            password="testuser2",
            image_url=None)
        db.session.commit()

        test_message = Message(text="test message")
        self.testuser.messages.append(test_message)
        test_message2 = Message(text="test message2")
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
        """test for add a new message for logged in user"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post("/messages/new",
                          data={"text": "Hello"})
            msg = Message.query.filter(Message.text == "Hello").one()
            self.assertEqual(resp.status_code, 302)
            self.assertEqual(msg.text, "Hello")

    def test_fail_add_message(self):
        """test for fail add message for no logged in user"""

        with self.client as c:

            resp = c.post("/messages/new",
                          data={"text": "Hello"},
                          follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", html)

    def test_show_message_form(self):
        """test for show add message form when user logged in"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.get("/messages/new")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Add my message!</button>", html)

    def test_show_message(self):
        """test for show individual message page when user logged in"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.get(f"/messages/{self.test_message_id}")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("test message</p>", html)

    def test_destroy_message(self):
        """test if logged in user can delete a message"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post(f"/messages/{self.test_message_id}/delete")
            msg = Message.query.filter(
                Message.text == "test message").one_or_none()
            self.assertEqual(resp.status_code, 302)
            self.assertIsNone(msg)

    def test_fail_destroy_message(self):
        """test if invalid user can delete a message"""

        with self.client as c:

            resp = c.post(f"/messages/{self.test_message_id}/delete",
                          follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", html)

    def test_add_liked_message(self):
        """test for add liked message for valid user"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post(f"/messages/{self.test_message_id2}/like")
            msg = LikedMessage.query.one()

            self.assertEqual(resp.status_code, 302)
            self.assertEqual(self.test_message_id2, msg.message_id)

    def test_fail_add_liked_message(self):
        """test for fail adding liked message with no valid user"""

        with self.client as c:
            resp = c.post(f"/messages/{self.test_message_id2}/like",
                          follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", html)

    def test_remove_liked_message(self):
        """test for remove liked message with logged in user"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            liked = LikedMessage(
                message_id=self.test_message_id2,
                user_id=self.testuser.id)

            db.session.add(liked)
            db.session.commit()

            resp = c.post(f"/messages/{self.test_message_id2}/unlike")
            msg = LikedMessage.query.one_or_none()

            self.assertEqual(resp.status_code, 302)
            self.assertIsNone(msg)

    def test_fail_remove_liked_message(self):
        """test for fail removing liked message when no valid user"""

        with self.client as c:
            resp = c.post(f"/messages/{self.test_message_id2}/unlike",
                          follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", html)

    def test_show_liked_message(self):
        """test to show all of logged in user's liked messages"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            liked = LikedMessage(
                message_id=self.test_message_id2,
                user_id=self.testuser.id)

            db.session.add(liked)
            db.session.commit()

            resp = c.get(f"/users/{self.testuser.id}/likes")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("test message2</p>", html)

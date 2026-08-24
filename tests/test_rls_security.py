"""UniAssist Security Test Suite: Supabase Auth & PostgreSQL Row Level Security (RLS).

Tests:
1. User A creates Conversation A and Messages.
2. User B logs in and verifies Conversation A is not visible.
3. User B attempts to directly query User A's conversation UUID (Expects: 0 rows).
4. User B attempts to directly query User A's messages (Expects: 0 rows).
5. User B attempts to update User A's conversation title (Expects: 0 rows).
6. User B attempts to delete User A's conversation (Expects: 0 rows).
7. Logout and switch account verifies complete state and history isolation.
"""

import os
import sys
import unittest
import uuid
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from App.auth_service import sign_in, sign_out, sign_up, validate_email, validate_password
from App.chat_service import (
    create_conversation,
    delete_conversation,
    generate_chat_title,
    get_conversation_messages,
    get_user_conversations,
    rename_conversation,
    save_message,
)
from App.supabase_client import get_authenticated_client, get_supabase_client, get_supabase_config


class TestUniAssistAuthValidation(unittest.TestCase):
    """Test validation and business logic."""

    def test_email_validation(self):
        self.assertTrue(validate_email("student@university.edu"))
        self.assertTrue(validate_email("user.name+tag@domain.co.uk"))
        self.assertFalse(validate_email("invalid-email"))
        self.assertFalse(validate_email("@missing-user.com"))
        self.assertFalse(validate_email("user@.com"))

    def test_password_validation(self):
        valid, msg = validate_password("strongpass123")
        self.assertTrue(valid)
        self.assertEqual(msg, "")

        invalid, msg = validate_password("12345")
        self.assertFalse(invalid)
        self.assertIn("at least 6 characters", msg)

    def test_chat_title_generation(self):
        title1 = generate_chat_title("What is Dijkstra's algorithm and how does it work?")
        self.assertTrue(len(title1.split()) <= 6)
        self.assertIn("Dijkstra", title1)

        title2 = generate_chat_title("Explain gradient descent in machine learning")
        self.assertTrue(len(title2.split()) <= 6)
        self.assertIn("Gradient", title2)


class TestUniAssistRLSSecurity(unittest.TestCase):
    """Verify Supabase Authentication and PostgreSQL Row Level Security (RLS) policies."""

    @classmethod
    def setUpClass(cls):
        cls.url, cls.key = get_supabase_config()
        cls.has_credentials = bool(cls.url and cls.key)

    def setUp(self):
        if not self.has_credentials:
            self.skipTest("Supabase credentials not configured in environment/secrets.")

    def test_complete_7_point_rls_security_flow(self):
        """Execute the full 7-step security audit."""
        base_client = get_supabase_client()
        self.assertIsNotNone(base_client, "Failed to initialize base Supabase client.")

        test_id = uuid.uuid4().hex[:8]
        user_a_email = f"test_user_a_{test_id}@uniassist-test.edu"
        user_b_email = f"test_user_b_{test_id}@uniassist-test.edu"
        password = "SecurePassword123!"

        print(f"\n--- [RLS Security Test] Starting audit with Test ID: {test_id} ---")

        # Step 1: Sign up User A
        res_a = sign_up(user_a_email, password, password, "User Alpha")
        if not res_a.get("success") and "already exists" not in res_a.get("error", ""):
            self.skipTest(f"Sign up failed (check Supabase Auth settings / verification): {res_a.get('error')}")

        sign_in_a = sign_in(user_a_email, password)
        if not sign_in_a.get("success"):
            self.skipTest(f"Sign in User A failed: {sign_in_a.get('error')}")

        token_a = sign_in_a["access_token"]
        user_a_id = sign_in_a["user"]["id"]
        client_a = get_authenticated_client(token_a)
        self.assertIsNotNone(client_a)

        # User A creates Conversation A and Messages
        conv_a = create_conversation(client_a, user_a_id, "User A Secret Algorithms Notes")
        self.assertIsNotNone(conv_a, "User A should be able to create Conversation A.")
        conv_a_id = conv_a["id"]
        print(f"✓ Test 1: User A created Conversation A ({conv_a_id})")

        msg_a = save_message(client_a, conv_a_id, user_a_id, "user", "Confidential research question from User A")
        self.assertIsNotNone(msg_a, "User A should be able to save message in Conversation A.")
        msg_a_id = msg_a["id"]
        print(f"✓ Test 1: User A saved Message A1 ({msg_a_id})")

        # Step 2: Sign up & Sign in User B
        res_b = sign_up(user_b_email, password, password, "User Beta")
        sign_in_b = sign_in(user_b_email, password)
        self.assertTrue(sign_in_b.get("success"), f"User B sign in failed: {sign_in_b.get('error')}")

        token_b = sign_in_b["access_token"]
        user_b_id = sign_in_b["user"]["id"]
        client_b = get_authenticated_client(token_b)
        self.assertIsNotNone(client_b)

        # Verify Conversation A does NOT appear in User B's conversation list
        user_b_convs = get_user_conversations(client_b, user_b_id)
        user_b_conv_ids = [c["id"] for c in user_b_convs]
        self.assertNotIn(conv_a_id, user_b_conv_ids, "CRITICAL: User B must NOT see User A's conversation list!")
        print("✓ Test 2: User B cannot see User A's conversation in conversation list.")

        # Step 3: User B attempts to access User A's messages
        user_b_msgs = get_conversation_messages(client_b, conv_a_id, user_b_id)
        self.assertEqual(
            len(user_b_msgs),
            0,
            "CRITICAL: User B must receive 0 messages when accessing User A's conversation!",
        )
        print("✓ Test 3: User B query for User A's conversation returned 0 messages (RLS Protected).")

        # Step 4: Verify User A's messages remain intact for User A
        user_a_msgs = get_conversation_messages(client_a, conv_a_id, user_a_id)
        self.assertGreaterEqual(
            len(user_a_msgs),
            1,
            "CRITICAL: User A must see own messages!",
        )
        print("✓ Test 4: User A sees own messages successfully.")

        # Step 5: User B attempts to update User A's conversation title
        rename_res = rename_conversation(client_b, conv_a_id, "Hacked by User B", user_b_id)
        user_a_convs = get_user_conversations(client_a, user_a_id)
        conv_a_obj = next((c for c in user_a_convs if c["id"] == conv_a_id), None)
        self.assertIsNotNone(conv_a_obj)
        self.assertEqual(conv_a_obj["title"], "User A Secret Algorithms Notes")
        print("✓ Test 5: User B update attempt on Conversation A rejected (RLS Protected).")

        # Step 6: User B attempts to delete User A's conversation
        delete_res = delete_conversation(client_b, conv_a_id, user_b_id)
        user_a_convs_after = get_user_conversations(client_a, user_a_id)
        conv_a_still_exists = any(c["id"] == conv_a_id for c in user_a_convs_after)
        self.assertTrue(conv_a_still_exists, "CRITICAL: User A's conversation must still exist!")
        print("✓ Test 6: User B delete attempt on Conversation A rejected (RLS Protected).")

        # Step 7: Logout User B and Login back as User A
        sign_out(token_b)
        sign_in_a_again = sign_in(user_a_email, password)
        self.assertTrue(sign_in_a_again.get("success"))
        client_a_new = get_authenticated_client(sign_in_a_again["access_token"])
        user_a_convs = get_user_conversations(client_a_new, user_a_id)
        user_a_conv_ids = [c["id"] for c in user_a_convs]
        self.assertIn(conv_a_id, user_a_conv_ids, "User A's conversations must persist and be visible to User A.")
        print("✓ Test 7: Account switching verified. User A's conversation history intact and isolated.")

        # Cleanup test conversation
        delete_conversation(client_a_new, conv_a_id, user_a_id)
        print("--- [RLS Security Test] All 7 Security and RLS Tests Passed Successfully! ---\n")


if __name__ == "__main__":
    unittest.main()

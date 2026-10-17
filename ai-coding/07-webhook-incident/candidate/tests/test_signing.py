import unittest

from hooks import signing
from sdk.webhooks import SignatureVerificationError, construct_event, verify_signature

SECRET = "whsec_test_123"


class SigningTest(unittest.TestCase):
    def test_header_format(self):
        header = signing.sign(b'{"id":"evt_1"}', SECRET, 1000)
        self.assertRegex(header, r"^t=1000,v1=[0-9a-f]{64}$")

    def test_sdk_verifies_what_we_sign(self):
        body = b'{"id":"evt_1","type":"charge.succeeded"}'
        header = signing.sign(body, SECRET, 1000)
        self.assertTrue(verify_signature(body, header, SECRET, now=1010))
        self.assertEqual(construct_event(body, header, SECRET, now=1010)["type"], "charge.succeeded")

    def test_tampered_body_is_rejected(self):
        header = signing.sign(b'{"amount":100}', SECRET, 1000)
        with self.assertRaises(SignatureVerificationError):
            verify_signature(b'{"amount":999}', header, SECRET, now=1000)

    def test_wrong_secret_is_rejected(self):
        header = signing.sign(b"{}", SECRET, 1000)
        with self.assertRaises(SignatureVerificationError):
            verify_signature(b"{}", header, "whsec_other", now=1000)

    def test_old_timestamp_is_rejected(self):
        header = signing.sign(b"{}", SECRET, 1000)
        with self.assertRaises(SignatureVerificationError):
            verify_signature(b"{}", header, SECRET, now=1000 + 301)

    def test_malformed_header(self):
        with self.assertRaises(SignatureVerificationError):
            verify_signature(b"{}", "v1=abc", SECRET, now=0)


if __name__ == "__main__":
    unittest.main()

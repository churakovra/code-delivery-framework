import unittest
from app import submit


class CheckoutTest(unittest.TestCase):
    def test_submit_charges_wallet(self):
        self.assertEqual(submit(3), 'charged:3')

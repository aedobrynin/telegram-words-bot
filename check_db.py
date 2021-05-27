"""
Checks database validity.
Checks if word.word and word.bad_variant are equal (case insensetive)
Checks if there is only one uppercase letter in word.word and word.bad_variant
"""

import unittest
from models import Session, Word


class WordsTest(unittest.TestCase):
    def test_only_one_ellipsis_in_word(self):
        session = Session()
        for word in session.query(Word).all():
            self.assertEqual(word.word.count('.'), 3,
                             msg=f"WORD ID: {word.id}")
            self.assertEqual(word.word.count('...'), 1,
                             msg=f"WORD ID: {word.id}")
        session.close()

    def test_at_least_two_variants(self):
        session = Session()
        for word in session.query(Word).all():
            self.assertGreaterEqual(len(word.variants), 2,
                                    msg=f"WORD ID: {word.id}")
        session.close()


if __name__ == "__main__":
    unittest.main()

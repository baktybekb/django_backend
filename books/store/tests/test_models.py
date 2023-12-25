from unittest.mock import patch
from django.contrib.auth.models import User
from django.test import TestCase
from store.models import Book, UserBookRelation


class SetRatingTestCase(TestCase):
    def setUp(self) -> None:
        user1 = User.objects.create(username='user1', first_name='John', last_name='Snow')
        self.book_1 = Book.objects.create(name='Test book 1', price=25, owner=user1)
        self.relation = UserBookRelation(user=user1, book=self.book_1, like=True, rate=5)

    def test_set_rating_called(self):
        with patch('store.models.Book.set_rating') as mocked_func:
            self.relation.save()
            mocked_func.assert_called()

    def test_set_rating_call_only_after_rate_change(self):
        with patch('store.models.Book.set_rating') as mocked_func:
            self.relation.save()
            self.assertEqual(mocked_func.call_count, 1)

            self.relation.in_bookmarks = True
            self.relation.save()
            self.assertEqual(mocked_func.call_count, 1)

            self.relation.rate = 1
            self.relation.save()
            self.assertEqual(mocked_func.call_count, 2)

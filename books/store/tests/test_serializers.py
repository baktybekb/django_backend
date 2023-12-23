from django.test import TestCase

from store.models import Book
from store.serializers import BooksSerializer


class BookSerializerTestCase(TestCase):
    def test_ok(self):
        book_1 = Book.objects.create(name='Test book 1', price=25)
        book_2 = Book.objects.create(name='Test book 1', price=55)
        serializer_data = BooksSerializer([book_1, book_2], many=True).data
        expected_data = [
            {
                'id': book_1.id,
                'name': book_1.name,
                'price': '25.00'
            },
            {
                'id': book_2.id,
                'name': book_2.name,
                'price': '55.00'
            },
        ]
        self.assertEqual(expected_data, serializer_data)

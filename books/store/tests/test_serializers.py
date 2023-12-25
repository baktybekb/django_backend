from django.contrib.auth.models import User
from django.db.models import Count, Case, When, Avg, Prefetch, F
from django.test import TestCase

from store.models import Book, UserBookRelation
from store.serializers import BooksSerializer


class BookSerializerTestCase(TestCase):
    def test_ok(self):
        user1 = User.objects.create(username='user1', first_name='John', last_name='Snow')
        user2 = User.objects.create(username='user2', first_name='Micheal', last_name='Jordan')
        user3 = User.objects.create(username='user3', first_name='Cristiano', last_name='Ronaldo')

        book_1 = Book.objects.create(name='Test book 1', price=25, owner=user1)
        book_2 = Book.objects.create(name='Test book 2', price=55)

        UserBookRelation.objects.create(user=user1, book=book_1, like=True, rate=5)
        UserBookRelation.objects.create(user=user2, book=book_1, like=True, rate=5)
        relation = UserBookRelation.objects.create(user=user3, like=True, book=book_1)
        relation.rate = 4
        relation.save()

        UserBookRelation.objects.create(user=user1, book=book_2, like=True, rate=3)
        UserBookRelation.objects.create(user=user2, book=book_2, like=True, rate=2)
        UserBookRelation.objects.create(user=user3, book=book_2, like=False)
        books = Book.objects.all().annotate(
            annotated_likes=Count(Case(When(userbookrelation__like=True, then=1))),
            owner_name=F('owner__username')).prefetch_related(
            Prefetch('readers', queryset=User.objects.all().only('first_name', 'last_name'))).order_by('id')
        serializer_data = BooksSerializer(books, many=True).data
        expected_data = [
            {
                'id': book_1.id,
                'name': book_1.name,
                'price': '25.00',
                'author_name': 'Author',
                'annotated_likes': 3,
                'rating': '4.67',
                'owner_name': 'user1',
                'readers': [
                    {
                        'first_name': 'John',
                        'last_name': 'Snow',
                    },
                    {
                        'first_name': 'Micheal',
                        'last_name': 'Jordan',
                    },
                    {
                        'first_name': 'Cristiano',
                        'last_name': 'Ronaldo',
                    }
                ]
            },
            {
                'id': book_2.id,
                'name': book_2.name,
                'price': '55.00',
                'author_name': 'Author',
                'annotated_likes': 2,
                'rating': '2.50',
                'owner_name': None,  # TODO need to return empty string ""
                'readers': [
                    {
                        'first_name': 'John',
                        'last_name': 'Snow',
                    },
                    {
                        'first_name': 'Micheal',
                        'last_name': 'Jordan',
                    },
                    {
                        'first_name': 'Cristiano',
                        'last_name': 'Ronaldo',
                    }
                ]
            },
        ]
        self.assertEqual(expected_data, serializer_data)

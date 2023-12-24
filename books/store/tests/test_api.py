import json

from django.contrib.auth.models import User
from django.db.models import Count, Case, When, Avg
from django.urls import reverse
from rest_framework import status
from rest_framework.exceptions import ErrorDetail
from rest_framework.test import APITestCase

from store.models import Book, UserBookRelation
from store.serializers import BooksSerializer


class BooksAPITestCase(APITestCase):
    def setUp(self) -> None:
        self.user = User.objects.create(username='test_username')
        self.book_1 = Book.objects.create(name='Test book 1', price=25, author_name='Author 1', owner=self.user)
        self.book_2 = Book.objects.create(name='Test book 2', price=55, author_name='Author 1')
        self.book_3 = Book.objects.create(name='Test book 3', price=55, author_name='Author 2')

        UserBookRelation.objects.create(user=self.user, book=self.book_1, rate=5, like=True)

    def test_get(self):
        url = reverse('book-list')
        response = self.client.get(url)
        books = Book.objects.all().annotate(
            annotated_likes=Count(Case(When(userbookrelation__like=True, then=1))),
            rating=Avg('userbookrelation__rate')
        ).order_by('id')
        serializer_data = BooksSerializer(books, many=True).data
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(serializer_data, response.data)
        self.assertEqual(serializer_data[0]['rating'], '5.00')
        self.assertEqual(serializer_data[0]['likes_count'], 1)
        self.assertEqual(serializer_data[0]['annotated_likes'], 1)

    def test_get_search(self):
        url = reverse('book-list')
        response = self.client.get(url, data={'search': 'Author 1'})
        books = Book.objects.filter(author_name='Author 1').annotate(
            annotated_likes=Count(Case(When(userbookrelation__like=True, then=1))),
            rating=Avg('userbookrelation__rate')
        ).order_by('id')
        serializer_data = BooksSerializer(books, many=True).data
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(serializer_data, response.data)

    def test_create(self):
        self.assertEqual(Book.objects.count(), 3)
        url = reverse('book-list')
        self.client.force_login(self.user)
        data = {'name': 'Programming in Python 3', 'price': 20, 'author_name': 'Mark Summerfield'}
        response = self.client.post(url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Book.objects.count(), 4)
        self.assertEqual(Book.objects.last().owner, self.user)

    def test_update(self):
        url = reverse('book-detail', args=(self.book_1.id,))
        self.client.force_login(self.user)
        data = {'name': self.book_1.name, 'price': 200, 'author_name': self.book_1.author_name}
        response = self.client.put(url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.book_1.refresh_from_db()
        self.assertEqual(self.book_1.price, 200)

    def test_update_not_owner(self):
        self.user2 = User.objects.create(username='test_username2')
        url = reverse('book-detail', args=(self.book_1.id,))
        self.client.force_login(self.user2)
        data = {'name': self.book_1.name, 'price': 200, 'author_name': self.book_1.author_name}
        response = self.client.put(url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.data, {
            'detail': ErrorDetail(string='You do not have permission to perform this action.',
                                  code='permission_denied')})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.book_1.refresh_from_db()
        self.assertEqual(self.book_1.price, 25)

    def test_update_not_owner_but_staff(self):
        self.user2 = User.objects.create(username='test_username2', is_staff=True)
        url = reverse('book-detail', args=(self.book_1.id,))
        self.client.force_login(self.user2)
        data = {'name': self.book_1.name, 'price': 200, 'author_name': self.book_1.author_name}
        response = self.client.put(url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.book_1.refresh_from_db()
        self.assertEqual(self.book_1.price, 200)


class BooksRelationTestCase(APITestCase):
    def setUp(self) -> None:
        self.user = User.objects.create(username='test_username')
        self.user2 = User.objects.create(username='test_username2')
        self.book_1 = Book.objects.create(name='Test book 1', price=25, author_name='Author 1')
        self.book_2 = Book.objects.create(name='Test book 2', price=55, author_name='Author 1')

    def test_like(self):
        url = reverse('userbookrelation-detail', args=(self.book_1.id,))
        self.client.force_login(self.user)
        response = self.client.patch(url, data=json.dumps({'like': True}), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        relation = UserBookRelation.objects.get(user=self.user, book=self.book_1)
        self.assertTrue(relation.like)

        response = self.client.patch(url, data=json.dumps({'in_bookmarks': True}), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        relation.refresh_from_db()
        self.assertTrue(relation.in_bookmarks)

    def test_rate(self):
        url = reverse('userbookrelation-detail', args=(self.book_1.id,))
        self.client.force_login(self.user)
        response = self.client.patch(url, data=json.dumps({'rate': 3}), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        relation = UserBookRelation.objects.get(user=self.user, book=self.book_1)
        self.assertEqual(relation.rate, 3)

    def test_rate_wrong(self):
        url = reverse('userbookrelation-detail', args=(self.book_1.id,))
        self.client.force_login(self.user)
        response = self.client.patch(url, data=json.dumps({'rate': 10}), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data,
                         {'rate': [ErrorDetail(string='"10" is not a valid choice.', code='invalid_choice')]})

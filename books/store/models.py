from django.contrib.auth.models import User
from django.db import models
from django.db.models import Avg


class Book(models.Model):
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=7, decimal_places=2)
    author_name = models.CharField(max_length=255, default='Author')
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='my_books')
    readers = models.ManyToManyField(User, through='UserBookRelation', related_name='books')
    rating = models.DecimalField(max_digits=3, decimal_places=2, null=True)

    def __str__(self):
        return f'{self.id}: {self.name}'

    def set_rating(self):
        self.rating = UserBookRelation.objects.filter(book=self).aggregate(rating=Avg('rate'))['rating']
        self.save()


class UserBookRelation(models.Model):
    RATE_CHOICES = (
        (1, 'Ok'),
        (2, 'Fine'),
        (3, 'Good'),
        (4, 'Amazing'),
        (5, 'Incredible'),
    )

    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    like = models.BooleanField(default=False)
    in_bookmarks = models.BooleanField(default=False)
    rate = models.PositiveSmallIntegerField(choices=RATE_CHOICES, null=True)

    def __str__(self):
        return f'{self.user.username}: {self.book.name}, rate: {self.rate}'

    def save(self, *args, **kwargs):
        old_rate = UserBookRelation.objects.get(id=self.pk).rate if self.pk else None
        super(UserBookRelation, self).save(*args, **kwargs)
        new_rate = self.rate
        if old_rate != new_rate or self.pk is None:
            self.book.set_rating()

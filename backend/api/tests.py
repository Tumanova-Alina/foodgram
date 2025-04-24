#!-*-coding:utf-8-*-
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITransactionTestCase
from rest_framework.authtoken.models import Token

from recipes.models import User, Follow


class SubscribeUserTestCase(APITransactionTestCase):

    @classmethod
    def setUpClass(cls):
        cls.url = reverse('api:users-list')

    def setUp(self):
        self.user = User.objects.create_user(username='vi', email='v@v.ru')
        token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        self.author = User.objects.create_user(username='author', email='a@a.ru')

    def test_subscribe(self):
        url = reverse('api:users-subscribe', kwargs={'pk': self.author.pk})
        self.assertEqual(Follow.objects.count(), 0)

        resp = self.client.post(url)

        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        follow = Follow.objects.last()
        self.assertEqual(follow.user, self.user)
        self.assertEqual(follow.author, self.author)
        self.assertEqual(Follow.objects.count(), 1)

    def test_subscribe_list(self):
        url = reverse('api:users-subscriptions')
        Follow.objects.create(user=self.user, author=self.author)
        self.assertEqual(Follow.objects.count(), 1)

        resp = self.client.get(url)

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        print(resp.data)

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from http import HTTPStatus

from ..forms import PostForm
from ..models import Group, Post, Comment


User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_author = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='ts',
            description='Тестовое описание',
        )
        cls.group_2 = Group.objects.create(
            title='Тестовая группа 2',
            slug='ts_2',
            description='Тестовое описание 2',
        )

        cls.post = Post.objects.create(
            author=cls.user_author,
            text='Тестовый пост',
            group=cls.group,
        )

        cls.form = PostForm()

    def setUp(self):
        self.author_client = Client()
        self.author_client.force_login(self.user_author)
        self.user = User.objects.create_user(username='auth_user')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        post_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый кекс',
            'group': self.group.id,
        }

        self.author_client.post(reverse('posts:post_create'),
                                data=form_data, follow=True)
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                author=self.user_author,
            ).exists()
        )

    def test_edit_post(self):
        post_count = Post.objects.count()
        form_data = {
            'text': 'Замена текста',
            'group': self.group_2.id,
        }

        response = self.author_client.post(reverse('posts:post_edit',
                                           kwargs={'post_id': self.post.id}),
                                           data=form_data, follow=True)
        response_2 = self.authorized_client.get(reverse('posts:post_detail',
                                                kwargs={'post_id': 1}))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Post.objects.count(), post_count)
        self.assertEqual(response_2.context.get('post').text, 'Замена текста')
        self.assertEqual(response_2.context.get('post').group.title,
                         'Тестовая группа 2')

    def summ_comment(self):
        summ = Comment.objects.count()
        self.assertEqual(summ, 0)
        form_data = {
            'text': 'Замена текста',
        }
        response = self.author_client.post(reverse('posts:add_comment',
                                           kwargs={'post_id': self.post.id}),
                                           data=form_data, follow=True)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(summ, summ)
        response_2 = self.author_client.get(reverse('posts:post_detail',
                                            kwargs={'post_id': 1}))
        self.assertEqual(response_2.context.get('comments').text,
                         'Замена текста')
        self.assertEqual(response_2.context.get('comments').author,
                         self.user)

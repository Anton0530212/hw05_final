from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from http import HTTPStatus
from django.core.cache import cache

from posts.models import Post, Group


User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.user_author = User.objects.create_user(username='author')

        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='ts',
            description='Тестовое описание',
        )

        cls.post = Post.objects.create(
            author=cls.user_author,
            text='Тестовый пост',
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='auth_user')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author_client = Client()
        self.author_client.force_login(self.user_author)
        cache.clear()

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.post.author}/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            f'/posts/{self.post.id}/edit/': 'posts/create_post.html',
        }

        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.author_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_urls_guest_client(self):
        addres = ['/', f'/group/{self.group.slug}/',
                  '/profile/auth_user/', f'/posts/{self.post.id}/']
        for i in addres:
            response = self.guest_client.get(i)
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_location_authorized(self):
        response = self.authorized_client.get(f'/posts/{self.post.id}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_urls_unexisting_page(self):
        response = self.client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_create_url_exists_at_desired_location_authorized(self):
        """Страница /posts/create_post.html/ доступна авторизованному
        пользователю."""
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_url_exists_at_desired_location_guest(self):
        """Страница /posts/create_post.html/ не доступна не авторизованному
        пользователю."""
        response = self.guest_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_create_user_url_redirect_anonymous_admin(self):
        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(
            response, '/auth/login/?next=/create/')

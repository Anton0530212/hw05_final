import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from posts.forms import PostForm
from django.core.cache import cache
from genericpath import exists

from ..models import Post, Group, Follow

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.testuser = User.objects.create_user(username='author')

        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='ts',
            description='Тестовое описание',
        )

        cls.posts = Post.objects.create(author=cls.testuser,
                                        text='Тестовый пост',
                                        group=cls.group,
                                        image=uploaded,
                                        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='auth_user')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.testuser)
        self.author_client = Client()
        self.author_client.force_login(self.testuser)
        cache.clear()

    def test_wiews_uses_correct_template(self):
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_post',
                    kwargs={'slug': 'ts'}): 'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username': 'author'}): 'posts/profile.html',
            reverse('posts:post_detail',
                    kwargs={'post_id': 1}): 'posts/post_detail.html',
            reverse('posts:post_edit',
                    kwargs={'post_id': 1}): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }

        for reverse_name, template in templates_pages_names.items():
            with self.subTest(temlate=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_context_post_edit(self):
        url = (reverse('posts:post_edit', kwargs={'post_id': self.posts.id}))
        response = self.authorized_client.get(url)
        form = response.context['form']
        self.assertEqual(response.context['is_edit'], True)
        self.assertIsInstance(form, PostForm)

    def test_context_create_post(self):
        response = self.authorized_client.get(reverse('posts:post_create'))
        form = response.context['form']
        none_edit = response.context.get('is_edit', None)
        self.assertIsNone(none_edit)
        self.assertIsInstance(form, PostForm)

    def test_page_show_index_context(self):
        response = self.authorized_client.get(reverse('posts:index'))
        posts = response.context['page_obj'][0]
        self.assertEqual(posts.text, PostURLTests.posts.text)
        self.assertEqual(posts.image, PostURLTests.posts.image)

    def test_page_show_group_post_context(self):
        response = self.authorized_client.get(reverse('posts:group_post',
                                              kwargs={'slug': 'ts'}))
        posts = response.context['page_obj'][0]
        self.assertEqual(posts.text, PostURLTests.posts.text)
        self.assertEqual(posts.image, PostURLTests.posts.image)
        post = response.context['group']
        self.assertEqual(post, self.group)

    def test_page_show_profile_context(self):
        response = self.authorized_client.get(reverse('posts:profile',
                                              kwargs={'username': 'author'}))
        posts = response.context['page_obj'][0]
        self.assertEqual(posts.text, PostURLTests.posts.text)
        self.assertEqual(posts.image, PostURLTests.posts.image)
        post = response.context['profile']
        self.assertEqual(post, self.testuser)

    def test_post_detail_context_image(self):
        response = self.authorized_client.get(reverse('posts:post_detail',
                                              kwargs={'post_id': 1}))
        posts = response.context['post']
        self.assertEqual(posts.text, PostURLTests.posts.text)
        self.assertEqual(posts.image, PostURLTests.posts.image)

    def test_follow_view_adds_followers(self):
        """"Подписка на авторов работает корректно."""

        test_author = User.objects.create(username='test_auth')

        test_follower_count = Follow.objects.filter(author=test_author).count()

        self.authorized_client.get(
            reverse('posts:profile_follow',
                    kwargs={'username': test_author}))

        self.assertEqual(
            Follow.objects.filter(author=test_author).count(),
            test_follower_count + 1)

        follow_relation = Follow.objects.last()

        self.assertEqual(
            follow_relation.author,
            test_author,
            'В новой подписке неправильный автор!')

        self.assertEqual(
            follow_relation.user,
            self.testuser,
            'В новой подписке неправильный подписчик!')

    def test_author_cant_follow_himself(self):
        """"Автор не может подписаться на себя."""
        self.authorized_client.force_login(self.user)
        request = self.authorized_client.get(
            reverse('posts:profile_follow',
                    kwargs={'username': self.user}))

        self.assertFalse(
            Follow.objects.filter(
                author=self.user, user=self.user),
            exists)

        self.assertRedirects(
            request,
            reverse('posts:profile',
                    kwargs={'username': self.user})
        )

    def test_unfollow_view_removes_followers(self):
        """"Отписка от авторов работает корректно."""
        test_author = User.objects.create(username='test_auth2')

        Follow.objects.get_or_create(
            author=test_author, user=self.testuser)

        self.authorized_client.get(
            reverse('posts:profile_unfollow',
                    kwargs={'username': test_author}))

        self.assertFalse((
            Follow.objects.filter(author=test_author, user=self.user)),
            exists)


class PiginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='ts',
            description='Тестовое описание',
        )
        Post.objects.bulk_create([Post(
            text='Пост №' + str(i),
            author=cls.user,
            group=cls.group) for i in range(13)])

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def TestPaginator(self):
        FIRST_PAGE = 10
        SECOND_PAGE = 3
        context = {
            reverse('posts:index'): FIRST_PAGE,
            reverse('posts:index') + '?page=2': SECOND_PAGE,
            reverse('posts:group_post',
                    kwargs={'slug': 'ts'}): FIRST_PAGE,
            reverse('posts:group_post',
                    kwargs={'slug': 'ts'}) + '?page=2': SECOND_PAGE,
            reverse('posts:profile',
                    kwargs={'username': 'author'}): FIRST_PAGE,
            reverse('posts:profile',
                    kwargs={'username': 'author'}) + '?page=2': SECOND_PAGE
        }

        for reverse_page, len_posts in context.items():
            with self.subTest(reverse=reverse):
                response = self.authorized_client.get(reverse_page)
                self.assertEqual(len(response), len_posts)

    def test_post_invisibility_for_not_follower(self):
        author = User.objects.create_user(username='test_author')
        not_follower = User.objects.create_user(username='not_follower')
        self.not_follower_client = Client()
        self.not_follower_client.force_login(not_follower)
        Follow.objects.create(user=self.user, author=author)
        response = self.not_follower_client.get(
            reverse('posts:follow_index')
        )
        self.assertEqual(len(response.context['page_obj']), 0)

    def test_cache_index_page(self):
        """Проверяем что главная страница кешируется на 20 секунд."""
        Post.objects.create(
            text='Текст тестировки кэша',
            author=self.user,
        )
        response_one = self.authorized_client.get(reverse('posts:index'))
        Post.objects.create(
            text='Текст тестировки кэша',
            author=self.user,
        )
        response_two = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(response_one.content, response_two.content)
        cache.clear()
        
        response_three = self.authorized_client.get(reverse('posts:index'))
        self.assertNotEqual(response_one.content, response_three.content)
        
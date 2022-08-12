from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост для корректной работы',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у постов корректно работает __str__."""
        post = PostModelTest.post
        object_name = post.text[:15]
        self.assertEqual(object_name, str(post))

    def test_models_have_correct_object_group(self):
        """Проверяем, что у моделей корректно работает __str__."""
        group = PostModelTest.group
        group_object = group.title
        self.assertEqual(group_object, str(group))

    def test_verbose_name(self):
        group = PostModelTest.group
        field_vebrose = {
            'title': 'Группа',
            'slug': 'Адрес для страницы с задачей',
            'description': 'Тестовое описание',
        }

        for field, expected_value in field_vebrose.items():
            with self.subTest(field=field):
                self.assertEqual(
                    group._meta.get_field(field).verbose_name, expected_value)

    def test_title_help_text(self):
        group = PostModelTest.group
        field_help_texts = {
            'title': 'Название группы',
            'slug': 'Укажите адрес для страницы задачи.'
                    'Используйте только латиницу, цифры,'
                    'дефисы и знаки подчёркивания',
            'description': 'Тестовое описание',
        }

        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    group._meta.get_field(field).help_text, expected_value)

    def test_verbose_name_post(self):
        post = PostModelTest.post
        field_vebrose = {
            'text': 'Пост',
        }

        for field, expected_value in field_vebrose.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name, expected_value)

    def test_title_help_text_post(self):
        post = PostModelTest.post
        field_help_texts = {
            'text': 'Написать пост',
        }

        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text, expected_value)

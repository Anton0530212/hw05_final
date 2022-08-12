from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Group(models.Model):
    title = models.CharField(verbose_name='Группа',
                             max_length=200, help_text='Название группы')
    slug = models.SlugField(verbose_name='Адрес для страницы с задачей',
                            db_index=True, unique=True,
                            help_text='Укажите адрес для страницы задачи.'
                                      'Используйте только латиницу, цифры,'
                                      'дефисы и знаки подчёркивания')
    description = models.TextField(verbose_name='Тестовое описание',
                                   help_text='Тестовое описание')

    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField(verbose_name='Пост', help_text='Написать пост')
    pub_date = models.DateTimeField('date published', auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='posts')
    group = models.ForeignKey(Group, on_delete=models.SET_NULL,
                              related_name='posts', blank=True, null=True,)
    image = models.ImageField('Картинка', upload_to='posts/', blank=True)  

    def __str__(self):
        return self.text[:15]


class Meta:
    ordering = ['-pub_date',]


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE,
                             related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='comments')
    text = models.TextField()
    created = models.DateTimeField('date published', auto_now_add=True)

    def __str__(self):
        return self.text


class Follow(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name='follower',
                             verbose_name='Подписчик',)
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='following',
                               verbose_name='Отслеживается')

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_pairs'),
        ]
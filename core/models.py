from django.db import models

LEVEL_CHOICES = [
    ('beginner',     'Beginner'),
    ('intermediate', 'Intermediate'),
    ('advanced',     'Advanced'),
]

class Concept(models.Model):
    title             = models.CharField(max_length=200)
    slug              = models.SlugField(max_length=200, unique=True)
    level             = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='beginner')
    short_description = models.TextField()
    created_at        = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['title']   # alphabetical by default

    def __str__(self):
        return self.title
# slideapp/models.py

from django.db import models
from django.contrib.auth.models import User

class Slide(models.Model):
    title = models.CharField(max_length=200, default='未命名')
    content = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    lock = models.BooleanField(default=True)
    version = models.IntegerField(default=0)

    def extract_title_from_content(self):
        lines = self.content.split('\n')
        in_front_matter = False
        for line in lines:
            stripped_line = line.strip()
            if stripped_line in ('---', '+++'):
                in_front_matter = not in_front_matter
                continue
            if in_front_matter:
                continue
            if stripped_line.startswith('#'):
                return stripped_line.lstrip('#').strip()
        return '未命名幻灯片'

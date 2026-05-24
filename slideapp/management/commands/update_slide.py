import sys
from django.core.management.base import BaseCommand, CommandError
from slideapp.models import Slide


class Command(BaseCommand):
    help = 'Update slide content from a file or stdin, incrementing the version number'

    def add_arguments(self, parser):
        parser.add_argument('slide_id', type=int, help='ID of the slide to update')
        parser.add_argument('content_file', nargs='?', default='-',
                            help='Path to content file (use - or omit for stdin)')

    def handle(self, *args, **options):
        slide_id = options['slide_id']
        content_file = options['content_file']

        try:
            slide = Slide.objects.get(id=slide_id)
        except Slide.DoesNotExist:
            raise CommandError(f'Slide {slide_id} does not exist')

        if content_file == '-':
            content = sys.stdin.read()
        else:
            try:
                with open(content_file, 'r', encoding='utf-8') as f:
                    content = f.read()
            except FileNotFoundError:
                raise CommandError(f'File not found: {content_file}')

        slide.content = content
        slide.version = slide.version + 1
        slide.title = slide.extract_title_from_content()
        slide.save()

        self.stdout.write(self.style.SUCCESS(
            f'Updated slide {slide_id} to version {slide.version}'
        ))

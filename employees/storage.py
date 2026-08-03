import mimetypes

from django.core.files.base import ContentFile
from django.core.files.storage import Storage
from django.urls import reverse


class DatabaseStorage(Storage):
    """
    Stores files as rows in the MediaBlob table instead of the local
    filesystem. Used in production when Cloudinary isn't configured, so
    uploads survive Render's ephemeral disk without needing an external
    storage service — the already-persistent Postgres database is the
    backing store instead.
    """

    def _model(self):
        from .models import MediaBlob
        return MediaBlob

    def _open(self, name, mode='rb'):
        blob = self._model().objects.get(name=name)
        return ContentFile(bytes(blob.content), name=name)

    def _save(self, name, content):
        name = self.get_available_name(name)
        data = content.read()
        content_type = (
            getattr(content, 'content_type', None)
            or mimetypes.guess_type(name)[0]
            or 'application/octet-stream'
        )
        self._model().objects.update_or_create(
            name=name,
            defaults={
                'content': data,
                'content_type': content_type,
                'size': len(data),
            },
        )
        return name

    def get_available_name(self, name, max_length=None):
        # Overwrite in place on the same name (unique=True) — callers
        # (ImageField) already generate a unique-enough path per upload.
        return name

    def exists(self, name):
        return self._model().objects.filter(name=name).exists()

    def delete(self, name):
        self._model().objects.filter(name=name).delete()

    def size(self, name):
        return self._model().objects.get(name=name).size

    def url(self, name):
        return reverse('serve_media_blob', kwargs={'name': name})

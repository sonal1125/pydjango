from pathlib import Path

from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible

from cloudinary_storage.storage import (
    MediaCloudinaryStorage,
    VideoMediaCloudinaryStorage,
    RawMediaCloudinaryStorage,
)

@deconstructible
class ProductMediaCloudinaryStorage(Storage):

    def __init__(self):
        self.image_storage = MediaCloudinaryStorage()
        self.video_storage = VideoMediaCloudinaryStorage()
        self.raw_storage = RawMediaCloudinaryStorage()

    def _get_storage(self, name, content=None):

        extension = Path(name).suffix.lower()

        video_extensions = {
            ".mp4",
            ".webm",
            ".mov",
            ".avi",
            ".mkv",
            ".wmv",
            ".flv",
            ".3gp",
            ".mpeg",
        }

        raw_extensions = {
            ".pdf",
            ".doc",
            ".docx",
            ".txt",
        }

        if extension in video_extensions:
            return self.video_storage

        if extension in raw_extensions:
            return self.raw_storage

        return self.image_storage

    def _save(self, name, content):
        storage = self._get_storage(name, content)
        return storage.save(name, content)

    def delete(self, name):
        storage = self._get_storage(name)
        return storage.delete(name)

    def exists(self, name):
        storage = self._get_storage(name)
        return storage.exists(name)

    def url(self, name):
        storage = self._get_storage(name)
        return storage.url(name)

    def size(self, name):
        storage = self._get_storage(name)
        return storage.size(name)

    def get_accessed_time(self, name):
        storage = self._get_storage(name)
        return storage.get_accessed_time(name)

    def get_created_time(self, name):
        storage = self._get_storage(name)
        return storage.get_created_time(name)

    def get_modified_time(self, name):
        storage = self._get_storage(name)
        return storage.get_modified_time(name)
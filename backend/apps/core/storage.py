from django.core.files.storage import default_storage
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from backend.apps.core.di import IStorageProvider, ioc

def generate_scoped_upload_path(tenant_id: str, school_id: str, academic_year: str, module: str, filename: str) -> str:
    """
    Generate isolated upload storage paths:
    uploads/<tenant_id>/<school_id>/<academic_year>/<module>/<filename>
    """
    clean_year = str(academic_year).replace("/", "-").replace("\\", "-")
    return f"uploads/{tenant_id}/{school_id}/{clean_year}/{module}/{filename}"

class LocalStorage(IStorageProvider):
    def save_file(self, path: str, content) -> str:
        saved_name = default_storage.save(path, content)
        return default_storage.url(saved_name)

    def delete_file(self, path: str) -> bool:
        if default_storage.exists(path):
            default_storage.delete(path)
            return True
        return False

    def get_url(self, path: str) -> str:
        return default_storage.url(path)


class S3Storage(IStorageProvider):
    def __init__(self):
        try:
            from storages.backends.s3boto3 import S3Boto3Storage
            self.storage = S3Boto3Storage()
        except ImportError:
            raise ImproperlyConfigured("django-storages package is required for Amazon S3.")

    def save_file(self, path: str, content) -> str:
        name = self.storage.save(path, content)
        return self.storage.url(name)

    def delete_file(self, path: str) -> bool:
        if self.storage.exists(path):
            self.storage.delete(path)
            return True
        return False

    def get_url(self, path: str) -> str:
        return self.storage.url(path)


class GCSStorage(IStorageProvider):
    def __init__(self):
        try:
            from storages.backends.gcloud import GoogleCloudStorage
            self.storage = GoogleCloudStorage()
        except ImportError:
            raise ImproperlyConfigured("django-storages package is required for Google Cloud Storage.")

    def save_file(self, path: str, content) -> str:
        name = self.storage.save(path, content)
        return self.storage.url(name)

    def delete_file(self, path: str) -> bool:
        if self.storage.exists(path):
            self.storage.delete(path)
            return True
        return False

    def get_url(self, path: str) -> str:
        return self.storage.url(path)


# ==============================================================
# DEFAULT REGISTRATIONS
# ==============================================================

def register_storage_dependencies():
    provider = getattr(settings, 'DEFAULT_FILE_STORAGE_PROVIDER', 'local').lower()
    
    if provider == 'local':
        ioc.register(IStorageProvider, LocalStorage)
    elif provider == 's3':
        ioc.register(IStorageProvider, S3Storage)
    elif provider == 'gcs':
        ioc.register(IStorageProvider, GCSStorage)
    else:
        # Default fallback
        ioc.register(IStorageProvider, LocalStorage)

# Register on module loading
register_storage_dependencies()

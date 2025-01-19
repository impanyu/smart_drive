from django.apps import AppConfig


class ChatConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'chatgpt_django_app.chat'

    def ready(self):
        from smart_drive.chat import receivers

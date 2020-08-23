from django.contrib import admin

# Register your models here.
from .models import Question, Answer, Topic

admin.site.register(Question)
admin.site.register(Topic)
admin.site.register(Answer)

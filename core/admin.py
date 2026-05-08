from django.contrib import admin
from .models import Concept

@admin.register(Concept)
class ConceptAdmin(admin.ModelAdmin):
    list_display  = ['title', 'level', 'created_at']
    prepopulated_fields = {'slug': ('title',)}  # auto-fills slug as you type title
    search_fields = ['title']
    list_filter   = ['level']
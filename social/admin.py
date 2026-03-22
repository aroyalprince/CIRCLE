from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Profile, Squad, SquadMember

# 1. Make the Profile Visible
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'gender', 'is_id_verified')
    search_fields = ('user__username', 'full_name')

# 2. Make the Squads Visible
@admin.register(Squad)
class SquadAdmin(admin.ModelAdmin):
    # CHANGE 'leader' TO 'host' HERE 👇
    list_display = ('activity', 'host', 'gender_rule', 'created_at')
    list_filter = ('gender_rule',)

# 3. Make the Members Visible
admin.site.register(SquadMember)
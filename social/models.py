from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import datetime
import random
import string
from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    # --- PUBLIC SOCIAL DATA (Insta Style) ---
    full_name = models.CharField(max_length=100, blank=True) # e.g. "Rahul Sharma"
    bio = models.TextField(max_length=500, blank=True)       # e.g. "CS Student | Guitarist 🎸"
    dob = models.DateField(null=True, blank=True)            # Date of Birth
    profile_pic = models.ImageField(upload_to='profile_pics/', blank=True, null=True) # Public Photo

    # --- EXISTING FIELDS ---
    gender = models.CharField(max_length=1, choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')], default='O')
    college_id_card = models.ImageField(upload_to='verification_ids/', blank=True, null=True)
    is_id_verified = models.BooleanField(default=False)
    drishti_id = models.CharField(max_length=50, blank=True, null=True, unique=True)
    
    def __str__(self):
        return self.user.username
    
import random
import string
import datetime
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# 👇 1. HELPER FUNCTION TO GENERATE CODE
def generate_squad_code():
    # Generates a code like "SQ-4X9A"
    chars = string.ascii_uppercase + string.digits
    return 'SQ-' + ''.join(random.choices(chars, k=4))

class Squad(models.Model):
    
    host = models.ForeignKey(User, on_delete=models.CASCADE, related_name='squads_hosted')
    
    unique_code = models.CharField(max_length=10, null=True, blank=True)
    
    name = models.CharField(max_length=100, blank=True, null=True)
    # What are they doing?
    activity = models.CharField(max_length=100) 
    
    # Safety: Gender Rules
    FILTER_CHOICES = [('ANY', 'Anyone'), ('SAME', 'Same Gender Only')]
    gender_rule = models.CharField(max_length=10, choices=FILTER_CHOICES, default='ANY')
    
    # Location
    latitude = models.FloatField()
    longitude = models.FloatField()
    
    # The Timer
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(blank=True, null=True) # Allow null initially
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        # Set 30 min timer if not set
        if not self.expires_at:
            self.expires_at = timezone.now() + datetime.timedelta(minutes=30)
        
        # Ensure unique code (Collision check loop)
        if not self.unique_code:
            self.unique_code = generate_squad_code()
            while Squad.objects.filter(unique_code=self.unique_code).exists():
                self.unique_code = generate_squad_code()
                
        super().save(*args, **kwargs)



class SquadMember(models.Model):
    squad = models.ForeignKey(Squad, related_name='members', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)



class SquadMessage(models.Model):
    squad = models.ForeignKey(Squad, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()

    image = models.ImageField(upload_to='chat_images/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender.username}: {self.text[:20]}"

from django.db.models.signals import post_save
from django.dispatch import receiver

# This function runs automatically every time a User is saved
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()


import uuid


class VideoQueue(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    room_id = models.CharField(max_length=50, blank=True, null=True)
    is_matched = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - Matched: {self.is_matched}"
from rest_framework import serializers
from .models import Squad, SquadMember, Profile, SquadMessage

class SquadSerializer(serializers.ModelSerializer):
    # These fields pull data from the User -> Profile relationship
    host_pic = serializers.SerializerMethodField()
    host_bio = serializers.SerializerMethodField()
    host_real_name = serializers.SerializerMethodField()
    host_dob = serializers.ReadOnlyField(source='host.profile.dob')
    host_gender = serializers.SerializerMethodField()
    created_by = serializers.ReadOnlyField(source='host.username')
    # Optional: Send host verification status too if needed for map pins
    # host_verified = serializers.SerializerMethodField()

    class Meta:
        model = Squad
        fields = [
            'id', 'unique_code', 'name', 'activity', 'latitude', 'longitude', 'created_by', 
            'host_pic', 'host_bio', 'host_real_name', 'host_dob', 'host_gender'
        ]

    def get_host_pic(self, obj):
        if hasattr(obj.host, 'profile') and obj.host.profile.profile_pic:
            return obj.host.profile.profile_pic.url
        return None

    def get_host_bio(self, obj):
        try: return obj.host.profile.bio
        except: return ""

    def get_host_real_name(self, obj):
        try: return obj.host.profile.full_name
        except: return obj.host.username

    def get_host_gender(self, obj):
        try: return obj.host.profile.get_gender_display()
        except: return "Unknown"


class SquadMessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.ReadOnlyField(source='sender.username')
    sender_pic = serializers.SerializerMethodField()
    
    # 👇 NEW FIELD: This sends True/False for the tick
    is_sender_verified = serializers.SerializerMethodField()
    
    class Meta:
        model = SquadMessage
        # 👇 Added 'is_sender_verified' to the fields list
        fields = ['id', 'squad', 'sender', 'sender_name', 'sender_pic', 'text', 'image', 'created_at', 'is_sender_verified']

    def get_sender_pic(self, obj):
        try: 
            if obj.sender.profile.profile_pic:
                return obj.sender.profile.profile_pic.url
            return None
        except: 
            return None

    # 👇 LOGIC FOR THE TICK
    def get_is_sender_verified(self, obj):
        try:
            return obj.sender.profile.is_id_verified
        except:
            return False
        
    

    
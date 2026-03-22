import json
from time import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from django.dispatch import receiver
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, parsers
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from dj_rest_auth.registration.views import SocialLoginView
from .models import Profile
from dj_rest_auth.views import LoginView
from django.core.cache import cache
import time
# ==========================================
# 1. MANUAL SIGNUP (ID Card Upload)
# ==========================================
class ManualSignupView(APIView):
    permission_classes = [permissions.AllowAny] 
    
    authentication_classes = []
    def post(self, request):
        data = request.data
        
        try:
            # 1. Create the User (This triggers the signal to create a Profile)
            user = User.objects.create_user(
                username=data.get('username'),
                password=data.get('password')
            )
            
            # 2. GET the profile (don't CREATE it)
            # The signal at the bottom of models.py already made this!
            profile = user.profile 
            
            # 3. Update the fields with your form data
            profile.full_name = data.get('full_name', '')
            profile.bio = data.get('bio', '')
            profile.gender = data.get('gender', 'O')
            profile.dob = data.get('dob') if data.get('dob') else None
            
            # Handle Files
            if 'profile_pic' in request.FILES:
                profile.profile_pic = request.FILES['profile_pic']
            if 'id_card' in request.FILES:
                profile.college_id_card = request.FILES['id_card']
                
            profile.save()

            # 4. Generate Token for auto-login
            token, _ = Token.objects.get_or_create(user=user)
            
            return Response({'token': token.key}, status=201)

        except Exception as e:
            return Response({'error': str(e)}, status=400)
# ==========================================
# 2. DRISTI SIGNUP (External ID)
# ==========================================
class DrishtiSignupView(APIView):
    """
    User provides: Drishti ID and sets a New Password.
    We trust Drishti, so they are Auto-Verified.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        drishti_id = request.data.get('drishti_id')
        password = request.data.get('password') # They set this now

        if not drishti_id or not password:
            return Response({'error': 'Drishti ID and Password required'}, status=400)

        if User.objects.filter(username=drishti_id).exists():
            return Response({'error': 'This ID is already registered. Please Login.'}, status=400)

        # (Optional: Add your simulated Drishti check here if needed)

        try:
            # 1. Create User (Username = Drishti ID)
            user = User.objects.create_user(username=drishti_id, password=password)
            
            # 2. Create Verified Profile
            Profile.objects.create(
                user=user,
                drishti_id=drishti_id,
                is_id_verified=True, # Trusted Source
                gender='O' # They fill this later
            )

            # 3. Generate Token
            token, _ = Token.objects.get_or_create(user=user)

            return Response({
                'message': 'Drishti Account Linked Successfully',
                'token': token.key,
                'user_id': user.id
            }, status=201)

        except Exception as e:
            return Response({'error': str(e)}, status=500)


# ==========================================
# 3. GOOGLE SIGNUP (Social)
# ==========================================
class GoogleLoginView(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    

from .models import Squad, SquadMember
from .serializers import SquadSerializer

# ... imports ...



# social/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from django.utils import timezone  
from .models import Squad, SquadMember
from .serializers import SquadSerializer

# ==========================================
# 4. CREATE SQUAD (The Fix)
# ==========================================
class CreateSquadView(APIView):
    """
    User sends: Activity, Location, Gender Rule.
    We create a Squad + Add them as the Leader + Start Timer.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        data = request.data
        
        activity = data.get('activity')
        lat = data.get('latitude')
        lng = data.get('longitude')
        gender_rule = data.get('gender_rule', 'ANY')

        if not activity or not lat or not lng:
            return Response({'error': 'Activity and Location are required'}, status=400)

        try:
            # 👇 FIX IS HERE: We added 'host=user'
            new_squad = Squad.objects.create(
                host=user,              # <--- THIS WAS MISSING
                activity=activity,
                latitude=lat,
                longitude=lng,
                gender_rule=gender_rule
            )
            
            # Add user as the first member too (so they appear in the list)
            SquadMember.objects.create(squad=new_squad, user=user)

            serializer = SquadSerializer(new_squad)
            return Response({
                'message': 'Squad Created! Timer started (30 mins).',
                'squad': serializer.data
            }, status=201)

        except Exception as e:
            return Response({'error': str(e)}, status=500)


# ==========================================
# 5. FIND SQUADS (Updated)
# ==========================================
# social/views.py

# social/views.py
import math # <--- Make sure to import math at the top of the file!

# ... other imports ...

class FindSquadsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            # 1. Get My Location
            my_lat = float(request.query_params.get('latitude', 0))
            my_lng = float(request.query_params.get('longitude', 0))
            
            if my_lat == 0 and my_lng == 0:
                return Response([]) 

            # 2. Settings
            MAX_RANGE_KM = 50.0  # <--- CHANGE THIS NUMBER to set your app's radius
            
            # 3. Get My Gender (Safe Check)
            try: my_gender = request.user.profile.gender
            except: my_gender = 'O' 

            # 4. Filter Loop
            active_squads = Squad.objects.filter(is_active=True)
            valid_squads = []
            now = timezone.now()

            for squad in active_squads:
                # A. Check Timer
                if squad.expires_at < now:
                    squad.is_active = False
                    squad.save()
                    continue

                # B. Check Gender Rule
                try: leader_gender = squad.host.profile.gender
                except: leader_gender = 'O'
                
                if squad.gender_rule == 'SAME':
                    if my_gender != leader_gender:
                        continue 

                # C. Check Exact Distance (The Haversine Formula)
                lat1, lon1 = my_lat, my_lng
                lat2, lon2 = squad.latitude, squad.longitude
                
                # Convert degrees to radians
                R = 6371 # Earth radius in km
                dlat = math.radians(lat2 - lat1)
                dlon = math.radians(lon2 - lon1)
                
                a = math.sin(dlat/2) * math.sin(dlat/2) + \
                    math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * \
                    math.sin(dlon/2) * math.sin(dlon/2)
                
                c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
                distance_km = R * c
                
                # D. Final Decision
                if distance_km <= MAX_RANGE_KM:
                    # Optional: Attach distance to object so UI can show "2.5km away"
                    # squad.distance = round(distance_km, 1) 
                    valid_squads.append(squad)

            serializer = SquadSerializer(valid_squads, many=True)
            return Response(serializer.data)

        except Exception as e:
            print("FIND ERROR:", e)
            return Response({'error': str(e)}, status=500)


# ==========================================
# 6. SQUAD VIEWSET (Master Controller)
# ==========================================
class SquadViewSet(viewsets.ModelViewSet):
    queryset = Squad.objects.all()
    serializer_class = SquadSerializer
    permission_classes = [permissions.IsAuthenticated]

    # 1. FIND SQUADS (GET /api/squad/find/?latitude=...&longitude=...)
    @action(detail=False, methods=['get'])
    def find(self, request):
        try:
            my_lat = float(request.query_params.get('latitude', 0))
            my_lng = float(request.query_params.get('longitude', 0))
            
            if my_lat == 0: return Response([]) 

            # Gender Check
            try: my_gender = request.user.profile.gender
            except: my_gender = 'O' 

            active_squads = Squad.objects.filter(is_active=True)
            valid_squads = []
            now = timezone.now()

            for squad in active_squads:
                # Timer Check
                if squad.expires_at < now:
                    squad.is_active = False
                    squad.save()
                    continue

                # Gender Rule Check
                try: leader_gender = squad.host.profile.gender
                except: leader_gender = 'O'

                if squad.gender_rule == 'SAME' and my_gender != leader_gender:
                    continue 

                # Distance Check (0.2 approx 20km)
                if abs(squad.latitude - my_lat) < 0.2 and abs(squad.longitude - my_lng) < 0.2:
                    valid_squads.append(squad)

            serializer = SquadSerializer(valid_squads, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response({'error': str(e)}, status=500)

    # 2. CREATE SQUAD (POST /api/squad/create/)
    def create(self, request, *args, **kwargs):
        user = request.user
        data = request.data
        
        # New: Get Name
        name = data.get('name') 
        activity = data.get('activity')
        
        if not activity: 
            return Response({'error': 'Activity required'}, status=400)

        try:
            new_squad = Squad.objects.create(
                host=user,
                name=name,        # <--- Added Name
                activity=activity,
                latitude=data.get('latitude'),
                longitude=data.get('longitude'),
                gender_rule=data.get('gender_rule', 'ANY')
            )
            # Add host as member
            SquadMember.objects.create(squad=new_squad, user=user)

            return Response(SquadSerializer(new_squad).data, status=201)
        except Exception as e:
            return Response({'error': str(e)}, status=500)

    # 3. JOIN SQUAD (POST /api/squad/join/ID/)
    @action(detail=True, methods=['post'])
    def join(self, request, pk=None):
        user = request.user
        squad = self.get_object() # Auto-finds squad by ID (pk)

        if not squad.is_active:
            return Response({'error': 'Squad ended'}, status=400)

        if SquadMember.objects.filter(squad=squad, user=user).exists():
            return Response({'message': 'Already joined'}, status=200)

        SquadMember.objects.create(squad=squad, user=user)
        return Response({'message': 'Joined!'}, status=200)

# social/views.py (Add this at the bottom)

class JoinSquadView(APIView):
    """
    User clicks "JOIN".
    We add them to the SquadMember list AND send a chat notification.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk): # 'pk' is the Squad ID
        user = request.user
        
        try:
            squad = Squad.objects.get(pk=pk)

            # 1. Check if Squad is Active
            if not squad.is_active:
                return Response({'error': 'This squad has ended.'}, status=400)

            # 2. Check if I am already a member
            if SquadMember.objects.filter(squad=squad, user=user).exists():
                return Response({'message': 'You are already in this squad!'}, status=200)

            # 3. Add me to the list!
            SquadMember.objects.create(squad=squad, user=user)

            # 👇 4. AUTOMATICALLY SEND THE "JOINED" MESSAGE 👇
            # This specific text triggers the 'System Message' style in your frontend
            SquadMessage.objects.create(
                squad=squad,
                sender=user,
                text=f"{user.username} joined the squad"
            )

            return Response({'message': 'Successfully Joined!'}, status=200)

        except Squad.DoesNotExist:
            return Response({'error': 'Squad not found'}, status=404)
        


class GetSquadView(APIView):
    """
    Get details of ONE specific squad (Name, Activity, Host).
    Used by the Chat Page to set the header title.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk): # 'pk' is the Squad ID (e.g. 30)
        try:
            squad = Squad.objects.get(pk=pk)
            # This serializer MUST have 'name' in its fields!
            serializer = SquadSerializer(squad)
            return Response(serializer.data)
        except Squad.DoesNotExist:
            return Response({'error': 'Squad not found'}, status=404)
        


from .models import SquadMessage
from .serializers import SquadMessageSerializer

class SendMessageView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser] # Allow file uploads

    def post(self, request, squad_id):
        text = request.data.get('text', '')
        image = request.FILES.get('image') # Get the file
        
        if not text and not image:
            return Response({'error': 'Message cannot be empty'}, status=400)
        
        try:
            squad = Squad.objects.get(id=squad_id)
            # Create message with optional text AND optional image
            SquadMessage.objects.create(
                squad=squad, 
                sender=request.user, 
                text=text, 
                image=image
            )
            return Response({'message': 'Sent'}, status=201)
        except Squad.DoesNotExist:
            return Response({'error': 'Squad not found'}, status=404)


# 2. NEW Leave Squad View
class LeaveSquadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk): # pk = Squad ID
        try:
            squad = Squad.objects.get(pk=pk)
            
            # If I am the Host, delete the squad (or handle differently)
            if squad.host == request.user:
                squad.is_active = False # End the squad
                squad.save()
                return Response({'message': 'Squad ended successfully.'})
            
            # If I am a Member, remove me from the list
            member_entry = SquadMember.objects.filter(squad=squad, user=request.user)
            if member_entry.exists():
                member_entry.delete()
                return Response({'message': 'Left squad.'})
            else:
                return Response({'error': 'You are not in this squad.'}, status=400)

        except Squad.DoesNotExist:
            return Response({'error': 'Squad not found'}, status=404)

class GetMessagesView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, squad_id):
        # Get all messages for this squad
        messages = SquadMessage.objects.filter(squad_id=squad_id).order_by('created_at')
        serializer = SquadMessageSerializer(messages, many=True)
        return Response(serializer.data)
    
# social/views.py
class GetProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, username):
        try:
            target_user = User.objects.get(username=username)
            # Use getattr to prevent crash if profile is missing
            profile = getattr(target_user, 'profile', None)
            
            if not profile:
                 return Response({'error': 'Profile incomplete'}, status=404)

            return Response({
                'username': target_user.username,
                'real_name': profile.full_name,
                'bio': profile.bio,
                'gender': profile.gender,
                'dob': profile.dob,
                'profile_pic': profile.profile_pic.url if profile.profile_pic else None
            })
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=404)


class SquadTypingView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, squad_id):
        cache_key = f"squad_{squad_id}_typing"
        typing_data = cache.get(cache_key, {})
        
        # Update this user's timestamp
        typing_data[request.user.id] = {
            'username': request.user.username,
            'time': time.time()
        }
        
        # Key lives for 8 seconds (gave it more time)
        cache.set(cache_key, typing_data, timeout=8) 
        return Response({'status': 'ok'})

    def get(self, request, squad_id):
        cache_key = f"squad_{squad_id}_typing"
        typing_data = cache.get(cache_key, {})
        
        active_typers = []
        now = time.time()
        
        for uid, data in typing_data.items():
            # Show users who typed in the last 5 seconds
            if now - data['time'] < 5: 
                if uid != request.user.id: # Don't show myself
                    active_typers.append(data['username'])
        
        return Response({'typing_users': active_typers})



from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

@csrf_exempt 
@api_view(['POST'])
#  CRITICAL: This line forces Django to IGNORE the session cookie.
# If SessionAuthentication is not in this list, CSRF checks are effectively disabled for this view.
@authentication_classes([TokenAuthentication]) 
@permission_classes([IsAuthenticated])
def update_profile(request):
    try:
        user = request.user
        profile = user.profile # Signal ensured this exists

        # Update text fields
        data = request.data
        if 'real_name' in data: profile.full_name = data['real_name']
        if 'bio' in data: profile.bio = data['bio']
        if 'gender' in data: profile.gender = data['gender']
        if 'dob' in data and data['dob']: profile.dob = data['dob']

        # Update images
        if 'profile_pic' in request.FILES:
            profile.profile_pic = request.FILES['profile_pic']

        profile.save()
        
        # Return the new pic URL so the frontend updates immediately
        return Response({
            "message": "Profile updated!",
            "profile_pic": profile.profile_pic.url if profile.profile_pic else None
        }, status=200)

    except Exception as e:
        return Response({"detail": str(e)}, status=400)




class CustomLoginView(LoginView):
    def get_response(self):
        # 1. Get the standard response (Token only)
        response = super().get_response()
        
        # 2. Add Profile Data to the response
        try:
            profile = self.user.profile
            response.data['username'] = self.user.username
            response.data['real_name'] = profile.full_name
            response.data['bio'] = profile.bio
            response.data['gender'] = profile.gender
            response.data['dob'] = profile.dob
            # Send full URL for the image
            if profile.profile_pic:
                response.data['profile_pic'] = self.request.build_absolute_uri(profile.profile_pic.url)
            else:
                response.data['profile_pic'] = None
        except:
            pass
            
        return response


from django.db.models import Q




from django.shortcuts import render
from django.db.models.signals import post_save 
@receiver(post_save, sender=User)
def manage_user_profile(sender, instance, created, **kwargs):
    if created:
        # Safety net: only create if it doesn't exist
        Profile.objects.get_or_create(user=instance)

def index_page(request): 
    return render(request, 'index.html')

def login_page(request):
    return render(request, 'login.html')

def dashboard_page(request):
    return render(request, 'dashboard.html')

def signup_page(request):
    return render(request, 'signup.html')

def chat_page(request, squad_id):
    return render(request, 'chat.html')



from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from .models import VideoQueue
import uuid

class RandomVideoMatchView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        
        # 1. Clean up any stuck queues for this user
        VideoQueue.objects.filter(user=user).delete()

        # 2. Look for a stranger who is waiting
        waiting_stranger = VideoQueue.objects.filter(is_matched=False).exclude(user=user).first()

        if waiting_stranger:
            # WE FOUND SOMEONE! Generate a unique room name
            new_room_id = f"circle_room_{uuid.uuid4().hex[:8]}"
            
            # Update the stranger's queue so they know the room
            waiting_stranger.room_id = new_room_id
            waiting_stranger.is_matched = True
            waiting_stranger.save()
            
            return Response({'status': 'matched', 'room_id': new_room_id})
        
        else:
            # NOBODY IS WAITING. Put me in the queue.
            my_queue = VideoQueue.objects.create(user=user)
            return Response({'status': 'waiting', 'queue_id': my_queue.id})

class CheckMatchStatusView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, queue_id):
        try:
            my_queue = VideoQueue.objects.get(id=queue_id, user=request.user)
            
            if my_queue.is_matched:
                room_id = my_queue.room_id
                my_queue.delete() # We are matched, remove from queue
                return Response({'status': 'matched', 'room_id': room_id})
                
            return Response({'status': 'waiting'})
            
        except VideoQueue.DoesNotExist:
            return Response({'error': 'Queue not found'}, status=404)
        

def random_video_page(request):
    return render(request, 'random_video.html')



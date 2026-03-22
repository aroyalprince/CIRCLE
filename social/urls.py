from django.urls import path
from .views import ManualSignupView, DrishtiSignupView, GoogleLoginView
from dj_rest_auth.views import LoginView # Standard Login for returning users
from .views import CreateSquadView
from .views import FindSquadsView
from .views import login_page, dashboard_page, ManualSignupView, JoinSquadView, CustomLoginView, GetProfileView
from .views import chat_page, SendMessageView, GetMessagesView,  update_profile, GetSquadView, LeaveSquadView, SquadTypingView
from social import views
urlpatterns = [
    # 1. Manual Signup (With ID Card)
    path('auth/signup/manual/', ManualSignupView.as_view(), name='manual_signup'),
    
    # 2. Drishti Signup
    path('auth/signup/drishti/', DrishtiSignupView.as_view(), name='drishti_signup'),
    
    # 3. Google Signup/Login
    path('auth/google/', GoogleLoginView.as_view(), name='google_login'),

    # 4. Standard Login (For Manual & Drishti users coming back)
    path('auth/login/', CustomLoginView.as_view(), name='custom_login'),




    
    
    path('squad/create/', CreateSquadView.as_view(), name='create_squad'),

    path('squad/find/', FindSquadsView.as_view(), name='find_squads'),

    path('squad/join/<int:pk>/', JoinSquadView.as_view()),
    path('squad/<int:pk>/', GetSquadView.as_view(), name='get_squad_details'),
    path('api/squad/join/<int:pk>/', JoinSquadView.as_view(), name='join_squad'),
    path('api/profile/<str:username>/', GetProfileView.as_view(), name='get_profile'),
    path('chat/<int:squad_id>/', chat_page),
    path('chat/send/<int:squad_id>/', SendMessageView.as_view()),
    path('chat/get/<int:squad_id>/', GetMessagesView.as_view()),
    path('squad/leave/<int:pk>/', LeaveSquadView.as_view(), name='leave_squad'),
    path('api/chat/typing/<int:squad_id>/', SquadTypingView.as_view(), name='squad_typing'),
    path('auth/signup/manual/', ManualSignupView.as_view(), name='manual_signup'),
    path('login/', login_page, name='ui_login'),
    path('random-video/', views.random_video_page),
    path('dashboard/', dashboard_page, name='ui_dashboard'),
    path('api/profile/update/', update_profile, name='update_profile'),
    path('', login_page),
]
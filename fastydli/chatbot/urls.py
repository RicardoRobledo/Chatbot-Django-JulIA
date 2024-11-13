from django.urls import path

from .views import home, send_message


urlpatterns = [
    # -------------------- Chatbot views -------------------

    path('home/', home, name='home'),

    # ----------------- Chatbot paths -----------------

    path('message/', send_message, name='chatbot'),

]

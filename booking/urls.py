from django.urls import path
from . import views

urlpatterns = [
    path('book/', views.BookView.as_view(), name='book'),
    path('cancel/<int:reservation_id>/', views.CancelView.as_view(), name='cancel')
]
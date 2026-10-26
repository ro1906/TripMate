from django.urls import path

from . import views

urlpatterns = [
    path("", views.trip_list, name="trip_list"),
    path("register/", views.register, name="register"),
    path("trips/new/", views.trip_create, name="trip_create"),
    path("trips/<int:pk>/", views.trip_detail, name="trip_detail"),
    path("trips/<int:pk>/delete/", views.trip_delete, name="trip_delete"),
    path("trips/<int:pk>/activities/add/", views.activity_add, name="activity_add"),
    path("trips/<int:pk>/activities/<int:activity_id>/delete/", views.activity_delete, name="activity_delete"),
    path("trips/<int:pk>/expenses/add/", views.expense_add, name="expense_add"),
    path("trips/<int:pk>/expenses/<int:expense_id>/delete/", views.expense_delete, name="expense_delete"),
]

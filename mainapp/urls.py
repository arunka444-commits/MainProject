from django.urls import include, path

from mainapp import views

urlpatterns = [
  path('', views.welcome, name='welcome'),
  path('signuppage/', views.signuppage, name='signuppage'),
  path('adminpage/', views.adminpage, name='adminpage'),
  path('userpage/', views.userpage, name='userpage'),
  path('employeepage/', views.employeepage, name='employeepage'),
  path('serviceproviderpage/', views.serviceproviderpage, name='serviceproviderpage'),
  path('signupuser/', views.signupuser, name='signupuser'),
  path('loginuser/', views.loginuser, name='loginuser'),
  path('basepage/', views.basepage, name='basepage'),
  path('api/bookings/recent/', views.recent_bookings, name='recent_bookings'),
  path('addservice/', views.addservice, name='addservice'),
  path('approve_service/<int:service_id>/', views.approve_service, name='approve_service'),
  path('deleteservice/<int:service_id>/', views.deleteservice, name='deleteservice'),
  path('book/<str:service_name>/', views.book_service, name='book_service'),
  path('accept_booking/<int:booking_id>/', views.accept_booking, name='accept_booking'),
  path('reject_booking/<int:booking_id>/', views.reject_booking, name='reject_booking'),
  path('service_provider_dashboard/', views.service_provider_dashboard, name='service_provider_dashboard'),
  path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
  path('all_users/', views.all_users, name='all_users'),
  path('addservicepage/', views.addservicepage, name='addservicepage'),
  path('logout_view/', views.logout_view, name='logout_view'),
    path("book-service/<int:service_id>/",views.book_service,name="book_service"),
    path('assign_employee/<int:booking_id>/',views.assign_employee,name='assign_employee'),

]
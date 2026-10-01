from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('register/',views.user_register,name='user_register'),
    path('login/',views.user_login,name='user_login'),

path(
    'logout/',
    views.user_logout,
    name='user_logout'
),

path(
    'dashboard/',
    views.user_dashboard,
    name='user_dashboard'
),

# Rentals
path(
    'rent/<int:tool_id>/',
    views.create_rental,
    name='create_rental'
),

path(
    'my-rentals/',
    views.my_rentals,
    name='my_rentals'
),

path(
    'cancel-rental/<int:rental_id>/',
    views.cancel_rental,
    name='cancel_rental'
),

path(
    'admin_login/',
    views.admin_login,
    name='admin_login'
),

path(
    'admin_dashboard/',
    views.admin_dashboard,
    name='admin_dashboard'
),

path(
    'admin_logout/',
    views.admin_logout,
    name='admin_logout'
),

# Tools
path(
    'manage_tools/',
    views.manage_tool,
    name='add_tool'
),


path(
    'delete_tool/<int:tool_id>/',
    views.delete_tool,
    name='delete_tool'
),  


path(
    'view_tool/',
    views.view_tool,
    name='view_tool'
),

path(
    'edit_tool/<int:tool_id>/',
    views.edit_tool,
    name='edit_tool'
),

# Customers
path(
    'customers/',
    views.view_customers,
    name='view_customers'
),

# Admin rentals
path(
    'manage-rentals/',
    views.manage_rentals,
    name='manage_rentals'),

path('update-rental/<int:rental_id>/',views.update_rental_status,name='update_rental_status'),

path('profile/', views.user_profile, name='user_profile'),
path(
    'edit-profile/',
    views.edit_profile,
    name='edit_profile'
),
]
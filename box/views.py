
from datetime import datetime
from functools import wraps

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import check_password, make_password
from django.shortcuts import get_object_or_404, redirect, render
from django.db import transaction
from .models import Customers, Rental, Tool
from django.views.decorators.cache import never_cache

# Create your views here.

def admin_required(view_func):
    @wraps(view_func)
    @login_required(login_url="admin_login")
    def wrapper(request, *args, **kwargs):

        if not request.user.is_superuser:
            messages.error(request,"You are not authorized to access this page.")
            return redirect("admin_login")
        return view_func(request, *args, **kwargs)
    return wrapper

def customer_required(view_func):

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):

        customer_id = request.session.get("customer_id")

        if not customer_id:
            messages.error(request, "Please login to continue.")
            return redirect("user_login")

        return view_func(request, *args, **kwargs)

    return wrapper


 
def index(request):

    tools = Tool.objects.filter(
        count__gt=0
    ).order_by("-id")[:6]

    return render(request, "index.html", {
        "tools": tools
    })






def user_register(request):

    if request.method == "POST":

        username = request.POST.get("username", "").strip()
        address = request.POST.get("address", "").strip()
        phone = request.POST.get("phone", "").strip()
        password = request.POST.get("password", "")
        c_password = request.POST.get("c_password", "")


        # Required field validation

        if not username or not address or not phone or not password or not c_password:

            messages.error(
                request,
                "Please fill all fields."
            )

            return redirect("user_register")


        # Username length

        if len(username) < 3:

            messages.error(
                request,
                "Username must contain at least 3 characters."
            )

            return redirect("user_register")


        if len(username) > 10:

            messages.error(
                request,
                "Username cannot exceed 10 characters."
            )

            return redirect("user_register")


        # Username duplicate

        if Customers.objects.filter(username=username).exists():

            messages.error(
                request,
                "Username already exists."
            )

            return redirect("user_register")


        # Phone validation

        if not phone.isdigit() or len(phone) != 10:

            messages.error(
                request,
                "Phone number must contain exactly 10 digits."
            )

            return redirect("user_register")


        # Password length

        if len(password) < 6:

            messages.error(
                request,
                "Password must contain at least 6 characters."
            )

            return redirect("user_register")


        # Confirm password

        if password != c_password:

            messages.error(
                request,
                "Passwords do not match."
            )

            return redirect("user_register")


        # Create customer

        Customers.objects.create(

            username=username,

            address=address,

            phone=phone,

            password=make_password(password)

        )


        messages.success(
            request,
            "Registration successful."
        )

        return redirect("user_login")


    return render(
        request,
        "user_register.html"
    )




def user_login(request):

    if request.method == "POST":

        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        if not username or not password:

            messages.error(
                request,
                "Please enter username and password."
            )

            return redirect("user_login")

        try:

            user = Customers.objects.get(
                username=username
            )

            if check_password(password, user.password):

                # Prevent session fixation
                request.session.cycle_key()

                request.session["customer_id"] = user.id
                request.session["customer_username"] = user.username

                return redirect("user_dashboard")

            messages.error(
                request,
                "Invalid username or password."
            )

        except Customers.DoesNotExist:

            messages.error(
                request,
                "Invalid username or password."
            )

    return render(request, "user_login.html")



@never_cache
@customer_required
def user_dashboard(request):
    customer_id = request.session.get("customer_id")


    customer = get_object_or_404(
        Customers,
        id=customer_id
    )

    tools = Tool.objects.filter(count__gt=0)

    rentals = Rental.objects.filter(
        customer=customer
    ).select_related("tool").order_by("-created_at")

    total_rentals = rentals.count()

    pending_rentals = rentals.filter(
        status="Pending"
    ).count()

    active_rentals = rentals.filter(
        status__in=["Approved", "Active"]
    ).count()

    completed_rentals = rentals.filter(
        status="Completed"
    ).count()

    return render(
        request,
        "user_dashboard.html",
        {
            "customer": customer,
            "tools": tools,
            "rentals": rentals,
            "total_rentals": total_rentals,
            "pending_rentals": pending_rentals,
            "active_rentals": active_rentals,
            "completed_rentals": completed_rentals,
        }
    )


@never_cache
@customer_required
def user_profile(request):

    customer_id = request.session.get("customer_id")

    customer = get_object_or_404(
        Customers,
        id=customer_id
    )

    return render(request, "user_profile.html", {
        "customer": customer
    })


@customer_required
def edit_profile(request):
    customer_id = request.session.get("customer_id")

    if not customer_id:
        messages.error(request, "Please login first.")
        return redirect("user_login")

    customer = get_object_or_404(
        Customers,
        id=customer_id
    )

    if request.method == "POST":

        username = request.POST.get("username")
        phone = request.POST.get("phone")
        address = request.POST.get("address")

        if not username or not phone or not address:
            messages.error(
                request,
                "Please fill all fields."
            )
            return redirect("edit_profile")

        if not phone.isdigit() or len(phone) != 10:
            messages.error(
                request,
                "Phone number must contain exactly 10 digits."
            )
            return redirect("edit_profile")

        username_exists = Customers.objects.filter(
            username=username
        ).exclude(
            id=customer.id
        ).exists()

        if username_exists:
            messages.error(
                request,
                "Username already exists."
            )
            return redirect("edit_profile")

        customer.username = username
        customer.phone = phone
        customer.address = address

        customer.save()

        request.session["customer_username"] = customer.username

        messages.success(
            request,
            "Profile updated successfully."
        )

        return redirect("user_profile")

    return render(
        request,
        "edit_profile.html",
        {
            "customer": customer
        }
    )
 

def admin_login(request):

    if request.method == "POST":

        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        if not username or not password:

            messages.error(
                request,
                "Please enter username and password."
            )

            return redirect("admin_login")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None and user.is_superuser:

            login(request, user)

            return redirect("admin_dashboard")

        messages.error(
            request,
            "Invalid username or password."
        )

    return render(
        request,
        "admin_login.html"
    )



@never_cache
@admin_required
def admin_dashboard(request):

    total_customers = Customers.objects.count()
    total_tools = Tool.objects.count()

    available_tools = Tool.objects.filter(count__gt=0).count()

    total_rentals = Rental.objects.count()

    pending_rentals = Rental.objects.filter(
        status="Pending"
    ).count()

    active_rentals = Rental.objects.filter(
        status__in=["Approved", "Active"]
    ).count()

    completed_rentals = Rental.objects.filter(
        status="Completed"
    ).count()

    return render(
        request,
        "admin_dashboard.html",
        {
            "total_customers": total_customers,
            "total_tools": total_tools,
            "available_tools": available_tools,
            "total_rentals": total_rentals,
            "pending_rentals": pending_rentals,
            "active_rentals": active_rentals,
            "completed_rentals": completed_rentals,
        }
    )


@never_cache
@admin_required
def manage_tool(request):

    if request.method == "POST":

        name = request.POST.get("name", "").strip()
        category = request.POST.get("category", "").strip()
        count = request.POST.get("count")
        price_per_day = request.POST.get("price_per_day")
        description = request.POST.get("description", "").strip()
        image = request.FILES.get("image")

        # Required field validation
        if not name or not category or not count or not price_per_day:

            messages.error(
                request,
                "Please fill all required fields."
            )

            return redirect("manage_tool")

        # Number validation
        try:

            count = int(count)
            price_per_day = float(price_per_day)

        except (ValueError, TypeError):

            messages.error(
                request,
                "Count and price must be valid numbers."
            )

            return redirect("manage_tool")

        # Count validation
        if count <= 0:

            messages.error(
                request,
                "Tool count must be greater than 0."
            )

            return redirect("manage_tool")

        # Price validation
        if price_per_day <= 0:

            messages.error(
                request,
                "Price per day must be greater than 0."
            )

            return redirect("manage_tool")

        # Create tool
        Tool.objects.create(
            name=name,
            category=category,
            count=count,
            price_per_day=price_per_day,
            description=description,
            image=image,
            available=count > 0
        )

        messages.success(
            request,
            "Tool added successfully."
        )

        return redirect("admin_dashboard")

    return render(request, "add_tool.html")



@admin_required
def delete_tool(request, tool_id):

    tool = get_object_or_404(Tool, id=tool_id)

    if request.method == "POST":

        # Check whether this tool has rental records
        if tool.rentals.exists():
            messages.error(
                request,
                "This tool cannot be deleted because it has rental records."
            )
            return redirect("view_tool")

        tool.delete()

        messages.success(
            request,
            "Tool deleted successfully."
        )

    return redirect("view_tool")


@never_cache
@admin_required
def view_tool(request):

    tools = Tool.objects.all()

    return render(
        request,
        "view_tool.html",
        {
            "tools": tools
        }
    )


@admin_required
def edit_tool(request, tool_id):

    tool = get_object_or_404(Tool, id=tool_id)

    if request.method == "POST":

        name = request.POST.get("name", "").strip()
        category = request.POST.get("category", "").strip()
        count = request.POST.get("count")
        price_per_day = request.POST.get("price_per_day")
        description = request.POST.get("description", "").strip()

        # Required field validation
        if not name or not category or not count or not price_per_day:

            messages.error(
                request,
                "Please fill all required fields."
            )

            return redirect("edit_tool", tool_id=tool.id)

        # Number validation
        try:

            count = int(count)
            price_per_day = float(price_per_day)

        except (ValueError, TypeError):

            messages.error(
                request,
                "Count and price must be valid numbers."
            )

            return redirect("edit_tool", tool_id=tool.id)

        # Count validation
        if count <= 0:

            messages.error(
                request,
                "Tool count must be greater than 0."
            )

            return redirect("edit_tool", tool_id=tool.id)

        # Price validation
        if price_per_day <= 0:

            messages.error(
                request,
                "Price per day must be greater than 0."
            )

            return redirect("edit_tool", tool_id=tool.id)

        # Update tool
        tool.name = name
        tool.category = category
        tool.count = count
        tool.price_per_day = price_per_day
        tool.description = description

        # Update availability
        tool.available = count > 0

        # Update image only if a new image is selected
        new_image = request.FILES.get("image")

        if new_image:
            tool.image = new_image

        tool.save()

        messages.success(
            request,
            "Tool updated successfully."
        )

        return redirect("view_tool")

    return render(
        request,
        "edit_tool.html",
        {"tool": tool}
    )



@never_cache
@admin_required
def view_customers(request):

    customers = Customers.objects.all()

    return render(
        request,
        "view_customers.html",
        {"customers": customers}
    )



def admin_logout(request):
    logout(request)
    return redirect("admin_login")



# CUSTOMER LOGOUT


def user_logout(request):
    request.session.flush()
    return redirect("user_login")


# CREATE RENTAL

@never_cache
@customer_required
def create_rental(request, tool_id):

    customer_id = request.session.get("customer_id")

    if not customer_id:
        messages.error(
            request,
            "Please login before renting a tool."
        )
        return redirect("user_login")

    customer = get_object_or_404(
        Customers,
        id=customer_id
    )

    tool = get_object_or_404(
        Tool,
        id=tool_id
    )

    # --------------------------------------------
    # Check whether at least one physical copy
    # is currently available
    # --------------------------------------------
    if tool.count <= 0:

        messages.error(
            request,
            "This tool is currently unavailable."
        )

        return redirect("index")

    if request.method == "POST":

        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")

        if not start_date or not end_date:

            messages.error(
                request,
                "Please select both dates."
            )

            return redirect(
                "create_rental",
                tool_id=tool.id
            )

        try:

            start = datetime.strptime(
                start_date,
                "%Y-%m-%d"
            ).date()

            end = datetime.strptime(
                end_date,
                "%Y-%m-%d"
            ).date()

        except ValueError:

            messages.error(
                request,
                "Invalid date."
            )

            return redirect(
                "create_rental",
                tool_id=tool.id
            )

        # --------------------------------------------
        # Date validation
        # --------------------------------------------

        today = datetime.today().date()

        if start < today:

            messages.error(
                request,
                "Start date cannot be in the past."
            )

            return redirect(
                "create_rental",
                tool_id=tool.id
            )

        if end < start:

            messages.error(
                request,
                "End date cannot be before start date."
            )

            return redirect(
                "create_rental",
                tool_id=tool.id
            )


        # --------------------------------------------
        # Calculate rental amount
        # --------------------------------------------

        total_days = (
            end - start
        ).days + 1

        total_price = (
            total_days *
            tool.price_per_day
        )

        # --------------------------------------------
        # Create rental
        # --------------------------------------------

        Rental.objects.create(
            customer=customer,
            tool=tool,
            start_date=start,
            end_date=end,
            total_days=total_days,
            total_price=total_price,
            status="Pending"
        )

        messages.success(
            request,
            "Rental request submitted successfully."
        )

        return redirect("user_dashboard")

    return render(
        request,
        "create_rental.html",
        {
            "tool": tool
        }
    )



@never_cache
@customer_required
def my_rentals(request):
    customer_id = request.session.get("customer_id")

    if not customer_id:
        messages.error(request,"Please login to view your rentals.")
        return redirect("user_login")

    customer = get_object_or_404(
    Customers,
    id=customer_id
)

    rentals = Rental.objects.filter(
    customer=customer
).select_related("tool").order_by("-created_at")

    return render(
        request,
        "my_rentals.html",
        {
        "customer": customer,
        "rentals": rentals
    }
)


# ---------------------------------------------------------

# CANCEL RENTAL

# ---------------------------------------------------------

@customer_required
def cancel_rental(request, rental_id):

    customer_id = request.session.get("customer_id")

    rental = get_object_or_404(
        Rental,
        id=rental_id,
        customer_id=customer_id
    )

    if request.method == "POST":

        if rental.status == "Pending":

            rental.status = "Cancelled"
            rental.save()

            messages.success(
                request,
                "Rental cancelled successfully."
            )

        else:

            messages.error(
                request,
                "Only pending rentals can be cancelled."
            )

    return redirect("my_rentals")


# ADMIN RENTAL MANAGEMENT

@never_cache
@admin_required
def manage_rentals(request):

    rentals = Rental.objects.select_related("customer","tool").order_by("-created_at")

    return render(request, "manage_rentals.html",{"rentals": rentals})


# UPDATE RENTAL STATUS


@admin_required
def update_rental_status(request, rental_id):

    rental = get_object_or_404(Rental, id=rental_id)

    if request.method == "POST":

        new_status = request.POST.get("status")

        valid_statuses = [
            choice[0]
            for choice in Rental.STATUS_CHOICES
        ]

        if new_status not in valid_statuses:

            messages.error(
                request,
                "Invalid rental status."
            )

            return redirect("manage_rentals")

        old_status = rental.status

        if old_status == new_status:

            messages.info(
                request,
                "Rental status is already set to this value."
            )

            return redirect("manage_rentals")

        with transaction.atomic():

            tool = rental.tool

            # Pending → Approved / Active
            # Tool is taken from available stock
            if (
                old_status == "Pending"
                and new_status in ["Approved", "Active"]
            ):

                if tool.count <= 0:

                    messages.error(
                        request,
                        "This tool is currently unavailable."
                    )

                    return redirect("manage_rentals")

                tool.count -= 1

            # Approved / Active → Completed / Cancelled
            # Tool is returned to stock
            elif (
                old_status in ["Approved", "Active"]
                and new_status in ["Completed", "Cancelled"]
            ):

                tool.count += 1

            rental.status = new_status
            rental.save()

            tool.available = tool.count > 0
            tool.save()

        messages.success(
            request,
            f"Rental status updated to {new_status}."
        )

    return redirect("manage_rentals")
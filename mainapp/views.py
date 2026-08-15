from decimal import Decimal, InvalidOperation
from django.db.models import Prefetch
from django.http import JsonResponse
from django.urls import reverse
from django.contrib.auth import logout
from django.contrib import auth, messages
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404, render, redirect

from mainapp.models import Booking, Profilee, addservice as ServiceModel

# Create your views here.


def signuppage(request):
    return render(request, "signup.html")


def welcome(request):
    return render(request, "welcome.html")


def adminpage(request):
    services = ServiceModel.objects.filter(status="Pending").order_by("-created_at")
    total_users = Profilee.objects.filter(role="USER").count()
    total_service_providers = Profilee.objects.filter(role="SERVICE_PROVIDER").count()
    total_bookings = Booking.objects.count()
    customers = Profilee.objects.filter(role="USER").select_related("user")
    providers = Profilee.objects.filter(role="SERVICE_PROVIDER").select_related("user")
    employees = Profilee.objects.filter(role="EMPLOYEE").select_related("user")

    context = {
        "services": services,
        "total_users": total_users,
        "total_service_providers": total_service_providers,
        "total_bookings": total_bookings,
        "customers": customers,
        "providers": providers,
        "employees": employees,
    }
    return render(request, "admin.html", context)


def userpage(request):
    approved_services = ServiceModel.objects.filter(status="Approved")

    providers = (
        User.objects.filter(addservice__status="Approved")
        .distinct()
        .prefetch_related(
            Prefetch(
                "addservice_set",
                queryset=approved_services,
                to_attr="approved_services",
            )
        )
    )

    my_bookings = Booking.objects.filter(user=request.user).order_by("-created_at")

    context = {
        "providers": providers,
        "my_bookings": my_bookings,
        "total_bookings": my_bookings.count(),
        "pending_bookings": my_bookings.filter(status="Pending").count(),
        "accepted_bookings": my_bookings.filter(status="Accepted").count(),
        "completed_bookings": my_bookings.filter(status="Completed").count(),
    }

    return render(request, "user.html", context)


def employeepage(request):
    return render(request, "employee.html")


def serviceproviderpage(request):

    bookings = []

    if request.user.is_authenticated:

        bookings = Booking.objects.filter(
            service_provider=request.user
        ).order_by("-created_at")

        for booking in bookings:

            booking.available_employees = Profilee.objects.filter(
                role="EMPLOYEE",
                skill__icontains=booking.service_name
            ).select_related("user")

    return render(
        request,
        "serviceprovider.html",
        {
            "bookings": bookings,
        }
    )


def basepage(request):
    return render(request, "base.html")


def addservicepage(request):
    return render(request, "add_service.html")


# login code


def _get_profile_role(user):
    try:
        profile = user.profilee
    except ObjectDoesNotExist:
        if user.is_superuser or user.is_staff:
            role = "ADMIN"
        else:
            role = "USER"
        profile = Profilee.objects.create(user=user, role=role)
    return profile.role


def signupuser(request):

    if request.method == "POST":

        firstname = request.POST.get("firstname", "").strip()
        lastname = request.POST.get("lastname", "").strip()
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        role = request.POST.get("role", "").strip()
        phone = request.POST.get("number", "").strip()
        skills = request.POST.getlist("skills")
        password = request.POST.get("password", "")
        confpass = request.POST.get("confpass", "")

        if password != confpass:
            messages.error(request, "Passwords do not match")
            return redirect("signuppage")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            return redirect("signuppage")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists")
            return redirect("signuppage")

        user = User.objects.create_user(
            first_name=firstname,
            last_name=lastname,
            username=username,
            email=email,
            password=password,
        )

        role_map = {
            "customer": "USER",
            "service_provider": "SERVICE_PROVIDER",
            "employee": "EMPLOYEE",
        }

        profile_role = role_map.get((role or "").lower(), "USER")

        Profilee.objects.create(
            user=user,
            role=profile_role,
            phone=phone,
            skill=", ".join(skills) if profile_role == "EMPLOYEE" else None,
        )

        messages.success(request, "Account created successfully")
        return redirect("welcome")

    return render(request, "signup.html")


# login code


def loginuser(request):

    if request.method == "POST":

        email = request.POST.get("email")
        password = request.POST.get("password")

        try:
            user_obj = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, "Invalid Email or Password")
            return redirect("welcome")

        user = auth.authenticate(username=user_obj.username, password=password)

        if user is not None:

            auth.login(request, user)

            role = _get_profile_role(user)

            if role == "ADMIN":
                return redirect("adminpage")

            elif role == "EMPLOYEE":
                return redirect("employeepage")

            elif role == "USER":
                return redirect("userpage")

            elif role == "SERVICE_PROVIDER":
                return redirect("serviceproviderpage")

        messages.error(request, "Invalid Email or Password")
        return redirect("welcome")

    return render(request, "welcome.html")


# addservicssavetodb


def addservice(request):
    if request.method == "POST":
        service_name = request.POST.get("service_name", "").strip()
        category = request.POST.get("category", "").strip()
        print("CATEGORY =", category)
        description = request.POST.get("description", "").strip()
        price_value = request.POST.get("price", "").strip() or "0"

        try:
            price = Decimal(price_value)
        except (InvalidOperation, TypeError, ValueError):
            price = Decimal("0")

        ServiceModel.objects.create(
            service_provider=request.user,
            service_name=service_name,
            category=category,
            description=description,
            price=price,
        )

    return redirect("serviceproviderpage")


def addservicetable(request):
    services = ServiceModel.objects.all()
    return render(request, "add_service.html", {"services": services})


def approve_service(request, service_id):
    service = get_object_or_404(ServiceModel, id=service_id)
    service.status = "Approved"
    service.save()
    return redirect(reverse("adminpage") + "?view=service-approval")


def deleteservice(request, service_id):
    try:
        deletepro = ServiceModel.objects.get(id=service_id)
        deletepro.delete()
    except ServiceModel.DoesNotExist:
        messages.error(request, "Service not found")
    # Redirect back to adminpage and keep the Service Approval view active
    return redirect(reverse("adminpage") + "?view=service-approval")


# book now button in user page
def book_service(request, service_id):

    service = get_object_or_404(ServiceModel, id=service_id)

    Booking.objects.create(
        user=request.user,
        service_provider=service.service_provider,
        service_name=service.service_name,
        status="Pending",
    )

    messages.success(request, "Booking request sent")
    return redirect("userpage")


def service_provider_dashboard(request):
    bookings = Booking.objects.all().order_by("-id")

    print("BOOKINGS COUNT:", bookings.count())

    return render(request, "serviceprovider.html", {"bookings": bookings})


def recent_bookings(request):
    bookings = Booking.objects.order_by("-created_at")[:5]
    data = []
    for booking in bookings:
        booking_date = getattr(booking, "created_at", None)
        data.append(
            {
                "customer": booking.user.username,
                "service": booking.service_name,
                "provider": "",
                "date": booking_date,
                "status": booking.status.lower(),
            }
        )
    for item in data:
        if hasattr(item["date"], "strftime"):
            item["date"] = item["date"].strftime("%b %d, %Y")
    return JsonResponse(data, safe=False)


def accept_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    booking.status = "Accepted"
    booking.save()
    return redirect("serviceproviderpage")


def reject_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    booking.status = "Rejected"
    booking.save()
    return redirect("serviceproviderpage")


# for total bookibg,user,serviceprovider display in admin page


def admin_dashboard(request):

    total_users = Profilee.objects.filter(role="USER").count()
    total_service_providers = Profilee.objects.filter(role="SERVICE_PROVIDER").count()
    total_bookings = Booking.objects.count()

    context = {
        "total_users": total_users,
        "total_service_providers": total_service_providers,
        "total_bookings": total_bookings,
    }

    return render(request, "admin_dashboard.html", context)


# adminpage view users
def all_users(request):

    users = Profilee.objects.filter(role="USER").select_related("user")

    context = {"users": users}

    return render(request, "admin.html", context)


# view all users menu
def customer_list(request):
    customers = Profilee.objects.filter(role="USER")

    return render(request, "admin.html", {"customers": customers})


# adminpage view serviceproviders
def all_providers(request):
    providers = Profilee.objects.filter(role="SERVICE_PROVIDER").select_related("user")

    context = {"Provider": providers}

    return render(request, "admin.html", context)


# view all provider (menu)
def provider_list(request):
    providers = Profilee.objects.filter(role="SERVICE_PROVIDER")

    print("Providers:", providers.count())

    return render(request, "admin.html", {"providers": providers})


####################     EMPLOYEE VIEW     #########################################
# adminpage view employees
def all_employees(request):
    employees = Profilee.objects.filter(role="EMPLOYEE").select_related("user")

    context = {"employees": employees}

    return render(request, "admin.html", context)


# view all employee (menu)
def employee_list(request):
    employees = Profilee.objects.filter(role="EMPLOYEE")

    print("employees:", employees.count())
    return render(request, "admin.html", {"employees": employees})






def assign_employee(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    # Only pending bookings can be assigned
    if booking.status != "Pending":
        messages.error(request, "This booking cannot be assigned.")
        return redirect("serviceproviderpage")

    if request.method == "POST":
        employee_id = request.POST.get("employee_id")

        employee_profile = get_object_or_404(
            Profilee,
            user_id=employee_id,
            role="EMPLOYEE"
        )

        # Make sure employee has the required skill
        if employee_profile.skill.lower() != booking.service_name.lower():
            messages.error(
                request,
                "This employee does not have the required skill."
            )
            return redirect("serviceproviderpage")

        booking.assigned_employee = employee_profile.user
        booking.status = "Accepted"
        booking.save()

        messages.success(
            request,
            f"{employee_profile.user.username} assigned successfully."
        )

        return redirect("serviceproviderpage")

    return redirect("serviceproviderpage")






# logout code
def logout_view(request):
    logout(request)
    return redirect("welcome")

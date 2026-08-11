from decimal import Decimal, InvalidOperation
from django.http import JsonResponse
from django.urls import reverse

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
    services = ServiceModel.objects.all()
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
        "employees":employees,
    }
    return render(request, "admin.html", context)


def userpage(request):
    return render(request, "user.html")


def employeepage(request):
    return render(request, "employee.html")


def serviceproviderpage(request):
    bookings = []
    if request.user.is_authenticated:
        bookings = Booking.objects.filter(service_provider=request.user).order_by(
            "-created_at"
        )
    return render(request, "serviceprovider.html", {"bookings": bookings})


def basepage(request):
    return render(request, "base.html")


def addservice(request):
    if request.method == "POST":
        service_name = request.POST.get("service_name", "").strip()
        description = request.POST.get("description", "").strip()
        price_value = request.POST.get("price", "").strip() or "0"
        try:
            price = Decimal(price_value)
        except (InvalidOperation, TypeError, ValueError):
            price = Decimal("0")

        service = ServiceModel(
            service_name=service_name,
            description=description,
            price=price,
        )
        service.save()
        return redirect("serviceproviderpage")
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

        firstname = request.POST.get("firstname")
        lastname = request.POST.get("lastname")
        username = request.POST.get("username")
        email = request.POST.get("email")
        role = request.POST.get("role")
        password = request.POST.get("password")
        confpass = request.POST.get("confpass")

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

        profile, created = Profilee.objects.get_or_create(
            user=user, defaults={"role": profile_role}
        )
        phone = request.POST.get("number", "").strip()
        if phone:
            profile.phone = phone
            profile.save()

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


def addservicedb(request):
    if request.method == "POST":
        servicename = request.POST.get("service_name", "").strip()
        description = request.POST.get("description", "").strip()
        price_value = request.POST.get("price", "").strip() or "0"
        try:
            price = Decimal(price_value)
        except (InvalidOperation, TypeError, ValueError):
            price = Decimal("0")

        details = ServiceModel(
            service_name=servicename,
            description=description,
            price=price,
        )
        details.save()
        return redirect("serviceproviderpage")
    return redirect("serviceproviderpage")


def addservicetable(request):
    services = ServiceModel.objects.all()
    return render(request, "add_service.html", {"services": services})


def deleteservice(request, service_id):
    try:
        deletepro = ServiceModel.objects.get(id=service_id)
        deletepro.delete()
    except ServiceModel.DoesNotExist:
        messages.error(request, "Service not found")
    # Redirect back to adminpage and keep the Service Approval view active
    return redirect(reverse("adminpage") + "?view=service-approval")


# book now button in user page
def book_service(request, service_name):
    provider = User.objects.filter(profilee__role="SERVICE_PROVIDER").first()
    if provider is None:
        provider = User.objects.filter(username="provider").first()

    Booking.objects.create(
        user=request.user, service_provider=provider, service_name=service_name
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
    providers = Profilee.objects.filter(role='SERVICE_PROVIDER').select_related('user')

    context = {"Provider": providers}

    return render(request, "admin.html", context)


# view all provider (menu)
def provider_list(request):
    providers = Profilee.objects.filter(role="SERVICE_PROVIDER")

    print("Providers:", providers.count())

    return render(request, "admin.html", {"providers": providers})



#adminpage view employees
def all_employees(request):
    employees = Profilee.objects.filter(role='EMPLOYEE').select_related('user')

    context = {"employees": employees}

    return render(request, "admin.html", context)


# view all employee (menu)
def employee_list(request):
    employees = Profilee.objects.filter(role="EMPLOYEE")

    print("employees:", employees.count())
    return render(request, "admin.html", {"employees": employees})
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, get_user_model

from .forms import StudentCreateForm, MockCreatorCreateForm, AssistantAdminCreateForm
from academics.models import StudentClass
from tracking.models import Attendance, HomeworkStatus



# Create your views here.



User = get_user_model()


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:
            login(request, user)
            return redirect('home')

        return render(
            request,
            'accounts/login.html',
            {'error': 'Login yoki parol noto‘g‘ri'}
        )

    return render(request, 'accounts/login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


def create_student(request):
    if not request.user.is_authenticated:
        return redirect('login')

    if request.user.role not in ['assistant_admin', 'super_admin']:
        return redirect('home')

    if request.method == 'POST':
        form = StudentCreateForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect('cabinet')
    else:
        form = StudentCreateForm()

    return render(
        request,
        'accounts/create_student.html',
        {'form': form}
    )


def create_mock_creator(request):
    if not request.user.is_authenticated:
        return redirect('login')

    if request.user.role != 'super_admin':
        return redirect('home')

    if request.method == 'POST':
        form = MockCreatorCreateForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect('cabinet')
    else:
        form = MockCreatorCreateForm()

    return render(
        request,
        'accounts/create_mock_creator.html',
        {'form': form}
    )

def create_assistant_admin(request):
    if not request.user.is_authenticated:
        return redirect('login')

    if request.user.role != 'super_admin':
        return redirect('home')

    if request.method == 'POST':
        form = AssistantAdminCreateForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect('cabinet')
    else:
        form = AssistantAdminCreateForm()

    return render(
        request,
        'accounts/create_assistant_admin.html',
        {'form': form}
    )
def student_profile(request, student_id):
    if not request.user.is_authenticated:
        return redirect('login')

    if request.user.role not in ['teacher', 'assistant_admin', 'super_admin']:
        return redirect('home')

    student = User.objects.filter(
        id=student_id,
        role='student'
    ).first()

    if not student:
        return redirect('cabinet')

    if request.user.role == 'teacher':
        allowed = StudentClass.objects.filter(
            student=student,
            classroom__teacher=request.user
        ).exists()

    elif request.user.role == 'assistant_admin':
        allowed = StudentClass.objects.filter(
            student=student,
            classroom__assistant_admin=request.user
        ).exists()

    else:
        allowed = True

    if not allowed:
        return redirect('cabinet')

    class_history = StudentClass.objects.filter(
        student=student
    ).select_related(
        'classroom',
        'classroom__teacher',
        'classroom__assistant_admin',
        'removed_by'
    ).order_by('-joined_at')

    attendances = Attendance.objects.filter(
        student=student
    ).select_related(
        'classroom',
        'marked_by'
    ).order_by('-date')

    homework_statuses = HomeworkStatus.objects.filter(
        student=student
    ).select_related(
        'homework',
        'homework__classroom',
        'checked_by'
    ).order_by('-checked_at')

    present_count = attendances.filter(status='present').count()
    absent_count = attendances.filter(status='absent').count()
    late_count = attendances.filter(status='late').count()

    context = {
        'student': student,
        'class_history': class_history,
        'attendances': attendances,
        'homework_statuses': homework_statuses,
        'present_count': present_count,
        'absent_count': absent_count,
        'late_count': late_count,
    }

    return render(request, 'accounts/student_profile.html', context)
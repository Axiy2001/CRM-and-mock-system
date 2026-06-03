from django.shortcuts import render, redirect
from django.utils import timezone
from .forms import AssignAssistantAdminForm
from .models import ClassRoom, StudentClass
from .forms import ClassRoomCreateForm, AssignTeacherForm, AddStudentToClassForm


def class_list(request):
    classes = ClassRoom.objects.all()
    return render(request, 'academics/class_list.html', {'classes': classes})


def create_class(request):
    if not request.user.is_authenticated:
        return redirect('login')

    if request.user.role != 'super_admin':
        return redirect('home')

    if request.method == 'POST':
        form = ClassRoomCreateForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect('cabinet')
    else:
        form = ClassRoomCreateForm()

    return render(request, 'academics/create_class.html', {'form': form})


def assign_teacher(request, class_id):
    if not request.user.is_authenticated:
        return redirect('login')

    if request.user.role not in ['assistant_admin', 'super_admin']:
        return redirect('home')

    if request.user.role == 'assistant_admin':
        classroom = ClassRoom.objects.filter(
            id=class_id,
            assistant_admin=request.user
        ).first()
    else:
        classroom = ClassRoom.objects.filter(id=class_id).first()

    if not classroom:
        return redirect('cabinet')

    if request.method == 'POST':
        form = AssignTeacherForm(request.POST)

        if form.is_valid():
            classroom.teacher = form.cleaned_data['teacher']
            classroom.save()
            return redirect('cabinet')
    else:
        form = AssignTeacherForm(initial={'teacher': classroom.teacher})

    context = {
        'form': form,
        'classroom': classroom,
    }
    return render(request, 'academics/assign_teacher.html', context)


def manage_students(request, class_id):
    if not request.user.is_authenticated:
        return redirect('login')

    if request.user.role not in ['assistant_admin', 'super_admin']:
        return redirect('home')

    if request.user.role == 'assistant_admin':
        classroom = ClassRoom.objects.filter(
            id=class_id,
            assistant_admin=request.user
        ).first()
    else:
        classroom = ClassRoom.objects.filter(id=class_id).first()

    if not classroom:
        return redirect('cabinet')

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add':
            form = AddStudentToClassForm(request.POST)

            if form.is_valid():
                student = form.cleaned_data['student']

                active_link_exists = StudentClass.objects.filter(
                    student=student,
                    classroom=classroom,
                    is_active=True
                ).exists()

                if not active_link_exists:
                    StudentClass.objects.create(
                        student=student,
                        classroom=classroom
                    )

            return redirect('manage_students', class_id=classroom.id)

        if action == 'remove':
            student_class_id = request.POST.get('student_class_id')

            student_class = StudentClass.objects.filter(
                id=student_class_id,
                classroom=classroom,
                is_active=True
            ).first()

            if student_class:
                student_class.is_active = False
                student_class.left_at = timezone.now()
                student_class.removed_by = request.user
                student_class.save()

            return redirect('manage_students', class_id=classroom.id)

    form = AddStudentToClassForm()

    active_students = StudentClass.objects.filter(
        classroom=classroom,
        is_active=True
    ).select_related('student').order_by('-joined_at')

    archived_students = StudentClass.objects.filter(
        classroom=classroom,
        is_active=False
    ).select_related('student', 'removed_by').order_by('-left_at')

    context = {
        'classroom': classroom,
        'form': form,
        'active_students': active_students,
        'archived_students': archived_students,
    }

    return render(request, 'academics/manage_students.html', context)

def assign_assistant_admin(request, class_id):
    if not request.user.is_authenticated:
        return redirect('login')

    if request.user.role != 'super_admin':
        return redirect('home')

    classroom = ClassRoom.objects.filter(id=class_id).first()

    if not classroom:
        return redirect('cabinet')

    if request.method == 'POST':
        form = AssignAssistantAdminForm(request.POST, instance=classroom)

        if form.is_valid():
            form.save()
            return redirect('cabinet')
    else:
        form = AssignAssistantAdminForm(instance=classroom)

    context = {
        'form': form,
        'classroom': classroom,
    }

    return render(request, 'academics/assign_assistant_admin.html', context)
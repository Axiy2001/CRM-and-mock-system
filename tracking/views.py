from datetime import date

from django.shortcuts import render, redirect

from academics.models import ClassRoom, StudentClass
from .forms import HomeworkCreateForm
from .models import Attendance, Homework, HomeworkStatus


def get_attendance_classes(user):
    if user.role == 'teacher':
        return ClassRoom.objects.filter(teacher=user).order_by('name')

    if user.role == 'assistant_admin':
        return ClassRoom.objects.filter(assistant_admin=user).order_by('name')

    return ClassRoom.objects.none()


def attendance_list(request):
    if not request.user.is_authenticated:
        return redirect('login')

    if request.user.role not in ['teacher', 'assistant_admin']:
        return redirect('home')

    classes = get_attendance_classes(request.user)

    if request.method == 'POST':
        class_id = request.POST.get('take_class_id')
        selected_class = classes.filter(id=class_id).first()

        if not selected_class:
            return redirect('attendance_list')

        students = StudentClass.objects.filter(
            classroom=selected_class,
            is_active=True
        ).select_related('student')

        today = date.today()

        for item in students:
            student = item.student
            status = request.POST.get(f'status_{student.id}')
            late_time = request.POST.get(f'late_time_{student.id}')

            if not status:
                continue

            Attendance.objects.update_or_create(
                student=student,
                classroom=selected_class,
                date=today,
                defaults={
                    'status': status,
                    'late_time': late_time if status == 'late' and late_time else None,
                    'marked_by': request.user,
                }
            )

        return redirect(
            f'/attendance/?class_id={selected_class.id}&take_class_id={selected_class.id}'
        )

    selected_class_id = request.GET.get('class_id')
    take_class_id = request.GET.get('take_class_id')

    selected_class = None
    take_class = None
    student_data = []
    take_students = []

    if selected_class_id:
        selected_class = classes.filter(id=selected_class_id).first()

        if selected_class:
            student_links = StudentClass.objects.filter(
                classroom=selected_class,
                is_active=True
            ).select_related('student')

            for item in student_links:
                student = item.student

                attendances = Attendance.objects.filter(
                    student=student,
                    classroom=selected_class
                )

                student_data.append({
                    'student': student,
                    'present_count': attendances.filter(status='present').count(),
                    'absent_count': attendances.filter(status='absent').count(),
                    'late_count': attendances.filter(status='late').count(),
                    'last_attendance': attendances.order_by('-date').first(),
                })

    if take_class_id:
        take_class = classes.filter(id=take_class_id).first()

        if take_class:
            take_students = StudentClass.objects.filter(
                classroom=take_class,
                is_active=True
            ).select_related('student')

    context = {
        'classes': classes,

        'selected_class_id': selected_class_id,
        'selected_class': selected_class,
        'student_data': student_data,

        'take_class_id': take_class_id,
        'take_class': take_class,
        'take_students': take_students,
    }

    return render(request, 'tracking/attendance_list.html', context)


def take_attendance(request):
    return redirect('attendance_list')


def homework_list(request):
    if not request.user.is_authenticated:
        return redirect('login')

    if request.user.role == 'teacher':
        classes = ClassRoom.objects.filter(teacher=request.user)

        homeworks = Homework.objects.filter(
            classroom__in=classes
        ).select_related(
            'classroom',
            'created_by'
        ).order_by('-due_date')

        create_form = HomeworkCreateForm(teacher=request.user)

        selected_homework = None
        student_links = []

        if request.method == 'POST':
            action = request.POST.get('action')

            if action == 'create_homework':
                create_form = HomeworkCreateForm(
                    request.POST,
                    teacher=request.user
                )

                if create_form.is_valid():
                    homework = create_form.save(commit=False)
                    homework.created_by = request.user
                    homework.save()

                    return redirect('homework_list')

            elif action == 'check_homework':
                homework_id = request.POST.get('homework_id')

                selected_homework = Homework.objects.filter(
                    id=homework_id,
                    classroom__in=classes
                ).select_related('classroom').first()

                if not selected_homework:
                    return redirect('homework_list')

                student_links = StudentClass.objects.filter(
                    classroom=selected_homework.classroom,
                    is_active=True
                ).select_related('student')

                for item in student_links:
                    student = item.student

                    status_value = request.POST.get(f'status_{student.id}')
                    score_value = request.POST.get(f'score_{student.id}')
                    comment_value = request.POST.get(f'comment_{student.id}')

                    if not status_value:
                        continue

                    HomeworkStatus.objects.update_or_create(
                        homework=selected_homework,
                        student=student,
                        defaults={
                            'status': status_value,
                            'score': int(score_value) if score_value else None,
                            'comment': comment_value,
                            'checked_by': request.user,
                        }
                    )

                return redirect('homework_list')

        homework_id = request.GET.get('homework_id')

        if homework_id:
            selected_homework = Homework.objects.filter(
                id=homework_id,
                classroom__in=classes
            ).select_related('classroom').first()

            if selected_homework:
                student_links = StudentClass.objects.filter(
                    classroom=selected_homework.classroom,
                    is_active=True
                ).select_related('student')

        context = {
            'homeworks': homeworks,
            'create_form': create_form,
            'selected_homework': selected_homework,
            'student_links': student_links,
        }

        return render(request, 'tracking/homework_list.html', context)

    elif request.user.role == 'student':
        student_class_ids = StudentClass.objects.filter(
            student=request.user,
            is_active=True
        ).values_list('classroom_id', flat=True)

        homeworks = Homework.objects.filter(
            classroom_id__in=student_class_ids
        ).select_related(
            'classroom',
            'created_by'
        ).order_by('-due_date')

        homework_statuses = HomeworkStatus.objects.filter(
            student=request.user
        ).select_related('homework')

        status_map = {
            hs.homework_id: hs for hs in homework_statuses
        }

        context = {
            'homeworks': homeworks,
            'status_map': status_map,
        }

        return render(request, 'tracking/homework_list.html', context)

    return redirect('home')


def create_homework(request):
    return redirect('homework_list')


def check_homework(request):
    return redirect('homework_list')


def homework_detail(request, homework_id):
    if not request.user.is_authenticated:
        return redirect('login')

    if request.user.role != 'teacher':
        return redirect('home')

    classes = ClassRoom.objects.filter(teacher=request.user)

    homework = Homework.objects.filter(
        id=homework_id,
        classroom__in=classes
    ).select_related('classroom', 'created_by').first()

    if not homework:
        return redirect('homework_list')

    statuses = HomeworkStatus.objects.filter(
        homework=homework
    ).select_related('student', 'checked_by').order_by('student__username')

    return render(
        request,
        'tracking/homework_detail.html',
        {
            'homework': homework,
            'statuses': statuses,
        }
    )
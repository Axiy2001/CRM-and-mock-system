import json
from datetime import datetime, timedelta
from calendar import monthrange

from django.shortcuts import render, redirect
from django.utils import timezone

from accounts.models import User
from academics.models import ClassRoom, StudentClass
from tracking.models import Attendance, Homework, HomeworkStatus


def home(request):
    if request.user.is_authenticated and request.user.role in ['super_admin', 'assistant_admin']:
        if request.user.role == 'super_admin':
            classes = ClassRoom.objects.all().order_by('name')
            dashboard_title = 'Super Admin Dashboard'
        else:
            classes = ClassRoom.objects.filter(
                assistant_admin=request.user
            ).order_by('name')
            dashboard_title = 'Assistant Admin Dashboard'

        selected_class_id = request.GET.get('class_id')
        period_type = request.GET.get('period_type', 'month')

        today = timezone.localdate()
        selected_month = request.GET.get('month', today.strftime('%Y-%m'))
        selected_day = request.GET.get('day', today.strftime('%Y-%m-%d'))

        selected_class = None

        if selected_class_id:
            selected_class = classes.filter(id=selected_class_id).first()
        elif classes.exists():
            selected_class = classes.first()

        if period_type == 'day':
            start_date = datetime.strptime(selected_day, '%Y-%m-%d').date()
            end_date = start_date
        else:
            year, month = map(int, selected_month.split('-'))
            start_date = datetime(year, month, 1).date()
            last_day = monthrange(year, month)[1]
            end_date = datetime(year, month, last_day).date()

        attendances = Attendance.objects.none()

        if selected_class:
            attendances = Attendance.objects.filter(
                classroom=selected_class,
                date__gte=start_date,
                date__lte=end_date
            )

        present_count = attendances.filter(status='present').count()
        absent_count = attendances.filter(status='absent').count()
        late_count = attendances.filter(status='late').count()

        line_labels = []
        present_data = []
        absent_data = []
        late_data = []

        current_date = start_date

        while current_date <= end_date:
            day_attendances = attendances.filter(date=current_date)

            line_labels.append(current_date.strftime('%Y-%m-%d'))
            present_data.append(day_attendances.filter(status='present').count())
            absent_data.append(day_attendances.filter(status='absent').count())
            late_data.append(day_attendances.filter(status='late').count())

            current_date += timedelta(days=1)

        context = {
            'dashboard_title': dashboard_title,

            'classes': classes,
            'selected_class': selected_class,
            'selected_class_id': str(selected_class.id) if selected_class else '',

            'period_type': period_type,
            'selected_month': selected_month,
            'selected_day': selected_day,

            'present_count': present_count,
            'absent_count': absent_count,
            'late_count': late_count,

            'line_labels': json.dumps(line_labels),
            'present_data': json.dumps(present_data),
            'absent_data': json.dumps(absent_data),
            'late_data': json.dumps(late_data),
        }

        return render(request, 'core/home.html', context)

    return render(request, 'core/home.html')


def cabinet(request):
    if not request.user.is_authenticated:
        return redirect('login')

    role = request.user.role

    if role == 'student':
        student_classes = StudentClass.objects.filter(
            student=request.user,
            is_active=True
        ).select_related('classroom', 'classroom__teacher')

        attendances = Attendance.objects.filter(
            student=request.user
        ).select_related('classroom').order_by('-date')

        present_count = attendances.filter(status='present').count()
        absent_count = attendances.filter(status='absent').count()
        late_count = attendances.filter(status='late').count()

        homework_statuses = HomeworkStatus.objects.filter(
            student=request.user
        ).select_related('homework').order_by('checked_at')

        done_count = homework_statuses.filter(status='done').count()
        not_done_count = homework_statuses.filter(status='not_done').count()
        partial_count = homework_statuses.filter(status='partial').count()

        progress_labels = []
        progress_scores = []

        for hs in homework_statuses:
            if hs.score is not None:
                progress_labels.append(hs.checked_at.strftime('%Y-%m-%d'))
                progress_scores.append(hs.score)

        context = {
            'student_classes': student_classes,
            'attendances': attendances,

            'present_count': present_count,
            'absent_count': absent_count,
            'late_count': late_count,

            'done_count': done_count,
            'not_done_count': not_done_count,
            'partial_count': partial_count,

            'progress_labels': progress_labels,
            'progress_scores': progress_scores,
        }

        return render(request, 'dashboard/student.html', context)

    if role == 'teacher':
        classes = ClassRoom.objects.filter(
            teacher=request.user
        ).order_by('name')

        selected_class_id = request.GET.get('class_id')
        selected_class = None
        student_links = []

        if selected_class_id:
            selected_class = classes.filter(
                id=selected_class_id
            ).first()

            if selected_class:
                student_links = StudentClass.objects.filter(
                    classroom=selected_class,
                    is_active=True
                ).select_related('student').order_by('student__username')

        context = {
            'classes': classes,
            'selected_class': selected_class,
            'selected_class_id': selected_class_id,
            'student_links': student_links,
        }

        return render(request, 'dashboard/teacher.html', context)

    if role in ['assistant_admin', 'super_admin']:
        today = timezone.localdate()
        period = request.GET.get('period', 'month')

        if period == 'year':
            start_date = today.replace(month=1, day=1)
        else:
            start_date = today.replace(day=1)

        if role == 'assistant_admin':
            managed_classes = ClassRoom.objects.filter(
                assistant_admin=request.user
            ).select_related('teacher', 'assistant_admin')
        else:
            managed_classes = ClassRoom.objects.all().select_related(
                'teacher',
                'assistant_admin'
            )

        total_students = User.objects.filter(role='student').count()
        total_teachers = User.objects.filter(role='teacher').count()
        total_classes = ClassRoom.objects.count()
        total_homeworks = Homework.objects.count()
        total_attendances = Attendance.objects.count()

        done_count = HomeworkStatus.objects.filter(status='done').count()
        not_done_count = HomeworkStatus.objects.filter(status='not_done').count()
        partial_count = HomeworkStatus.objects.filter(status='partial').count()

        students_added_period = User.objects.filter(
            role='student',
            date_joined__date__gte=start_date,
            date_joined__date__lte=today
        ).count()

        teachers_added_period = User.objects.filter(
            role='teacher',
            date_joined__date__gte=start_date,
            date_joined__date__lte=today
        ).count()

        classes_created_period = ClassRoom.objects.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=today
        ).count()

        students_deactivated_period = User.objects.filter(
            role='student',
            is_active=False,
            deactivated_at__date__gte=start_date,
            deactivated_at__date__lte=today
        ).count()

        active_students = User.objects.filter(
            role='student',
            is_active=True
        ).count()

        context = {
            'managed_classes': managed_classes,

            'total_students': total_students,
            'total_teachers': total_teachers,
            'total_classes': total_classes,
            'total_homeworks': total_homeworks,
            'total_attendances': total_attendances,

            'done_count': done_count,
            'not_done_count': not_done_count,
            'partial_count': partial_count,

            'period': period,
            'students_added_period': students_added_period,
            'teachers_added_period': teachers_added_period,
            'classes_created_period': classes_created_period,
            'students_deactivated_period': students_deactivated_period,
            'active_students': active_students,
        }

        return render(request, 'dashboard/admin.html', context)

    return redirect('home')
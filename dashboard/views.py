from django.shortcuts import render, redirect
from django.utils import timezone

from accounts.models import User
from academics.models import ClassRoom, StudentClass
from tracking.models import Attendance, Homework, HomeworkStatus
from payments.models import Payment

# Create your views here.



def assistant_dashboard(request):
    if not request.user.is_authenticated:
        return redirect('login')

    if request.user.role not in ['assistant_admin', 'super_admin']:
        return redirect('home')

    today = timezone.localdate()

    if request.user.role == 'assistant_admin':
        classes = ClassRoom.objects.filter(
            assistant_admin=request.user
        )
    else:
        classes = ClassRoom.objects.all()

    class_ids = classes.values_list('id', flat=True)

    students = User.objects.filter(
        role='student',
        student_classes__classroom_id__in=class_ids,
        student_classes__is_active=True
    ).distinct()

    teachers = User.objects.filter(
        role='teacher',
        classes__id__in=class_ids
    ).distinct()

    active_student_classes = StudentClass.objects.filter(
        classroom_id__in=class_ids,
        is_active=True
    )

    today_attendance = Attendance.objects.filter(
        classroom_id__in=class_ids,
        date=today
    )

    homeworks = Homework.objects.filter(
        classroom_id__in=class_ids
    )

    homework_statuses = HomeworkStatus.objects.filter(
        homework__classroom_id__in=class_ids
    )

    payments = Payment.objects.filter(
        classroom_id__in=class_ids
    )

    unpaid_payments = payments.filter(
        status='unpaid'
    )

    partial_payments = payments.filter(
        status='partial'
    )

    total_debt = sum(
        payment.debt for payment in payments
    )

    context = {
        'today': today,

        'total_students': students.count(),
        'total_teachers': teachers.count(),
        'total_classes': classes.count(),
        'active_student_classes': active_student_classes.count(),

        'today_present': today_attendance.filter(status='present').count(),
        'today_absent': today_attendance.filter(status='absent').count(),
        'today_late': today_attendance.filter(status='late').count(),

        'total_homeworks': homeworks.count(),
        'homework_done': homework_statuses.filter(status='done').count(),
        'homework_not_done': homework_statuses.filter(status='not_done').count(),
        'homework_partial': homework_statuses.filter(status='partial').count(),

        'total_payments': payments.count(),
        'unpaid_count': unpaid_payments.count(),
        'partial_count': partial_payments.count(),
        'total_debt': total_debt,

        'classes': classes.order_by('-created_at')[:8],
        'unpaid_payments': unpaid_payments.select_related(
            'student',
            'classroom'
        )[:8],
    }

    return render(
        request,
        'dashboard/assistant_dashboard.html',
        context
    )


def calculate_student_progress(student):
    attendances = Attendance.objects.filter(student=student)

    total_attendance = attendances.count()
    present_count = attendances.filter(status='present').count()
    late_count = attendances.filter(status='late').count()

    if total_attendance > 0:
        attendance_percent = round(
            ((present_count + (late_count * 0.5)) / total_attendance) * 100
        )
    else:
        attendance_percent = 0

    homework_statuses = HomeworkStatus.objects.filter(student=student)

    total_homework = homework_statuses.count()
    done_count = homework_statuses.filter(status='done').count()
    partial_count = homework_statuses.filter(status='partial').count()

    if total_homework > 0:
        homework_percent = round(
            ((done_count + (partial_count * 0.5)) / total_homework) * 100
        )
    else:
        homework_percent = 0

    payments = Payment.objects.filter(student=student)

    unpaid_count = payments.filter(status='unpaid').count()
    partial_payment_count = payments.filter(status='partial').count()

    if unpaid_count > 0:
        payment_status = 'Unpaid'
        payment_percent = 40
    elif partial_payment_count > 0:
        payment_status = 'Partial'
        payment_percent = 70
    else:
        payment_status = 'Paid'
        payment_percent = 100

    overall_progress = round(
        (attendance_percent * 0.4) +
        (homework_percent * 0.4) +
        (payment_percent * 0.2)
    )

    return {
        'attendance_percent': attendance_percent,
        'homework_percent': homework_percent,
        'payment_status': payment_status,
        'payment_percent': payment_percent,
        'overall_progress': overall_progress,
    }


def student_progress_list(request):
    if not request.user.is_authenticated:
        return redirect('login')

    if request.user.role not in ['assistant_admin', 'super_admin']:
        return redirect('home')

    if request.user.role == 'assistant_admin':
        classes = ClassRoom.objects.filter(
            assistant_admin=request.user
        ).order_by('name')
    else:
        classes = ClassRoom.objects.all().order_by('name')

    selected_class_id = request.GET.get('class_id')
    selected_class = None

    if selected_class_id:
        selected_class = classes.filter(id=selected_class_id).first()

    students = User.objects.filter(
        role='student',
        student_classes__classroom__in=classes,
        student_classes__is_active=True
    )

    if selected_class:
        students = students.filter(
            student_classes__classroom=selected_class
        )

    students = students.distinct().order_by('username')

    progress_data = []

    for student in students:
        progress = calculate_student_progress(student)

        progress_data.append({
            'student': student,
            **progress,
        })

    return render(
        request,
        'dashboard/student_progress_list.html',
        {
            'progress_data': progress_data,
            'classes': classes,
            'selected_class': selected_class,
            'selected_class_id': selected_class_id,
        }
    )
def payment_crm(request):
    if not request.user.is_authenticated:
        return redirect('login')

    if request.user.role not in ['assistant_admin', 'super_admin']:
        return redirect('home')

    if request.user.role == 'assistant_admin':
        classes = ClassRoom.objects.filter(assistant_admin=request.user)
    else:
        classes = ClassRoom.objects.all()

    payments = Payment.objects.filter(
        classroom__in=classes
    ).select_related(
        'student',
        'classroom',
        'created_by'
    ).order_by('-month')

    status = request.GET.get('status')

    if status in ['paid', 'partial', 'unpaid']:
        payments = payments.filter(status=status)

    total_paid = sum(payment.paid_amount for payment in payments)
    total_amount = sum(payment.amount for payment in payments)
    total_debt = sum(payment.debt for payment in payments)

    context = {
        'payments': payments,
        'status': status,
        'total_paid': total_paid,
        'total_amount': total_amount,
        'total_debt': total_debt,
        'paid_count': payments.filter(status='paid').count(),
        'partial_count': payments.filter(status='partial').count(),
        'unpaid_count': payments.filter(status='unpaid').count(),
    }

    return render(
        request,
        'dashboard/payment_crm.html',
        context
    )

def students_crm(request):
    if not request.user.is_authenticated:
        return redirect('login')

    if request.user.role not in ['assistant_admin', 'super_admin']:
        return redirect('home')

    if request.user.role == 'assistant_admin':
        classes = ClassRoom.objects.filter(
            assistant_admin=request.user
        ).order_by('name')
    else:
        classes = ClassRoom.objects.all().order_by('name')

    selected_class_id = request.GET.get('class_id')
    selected_class = None

    if selected_class_id:
        selected_class = classes.filter(id=selected_class_id).first()

    student_links = StudentClass.objects.filter(
        classroom__in=classes,
        is_active=True
    ).select_related(
        'student',
        'classroom',
        'classroom__teacher'
    )

    if selected_class:
        student_links = student_links.filter(
            classroom=selected_class
        )

    student_links = student_links.order_by(
        'classroom__name',
        'student__username'
    )

    students_data = []

    for link in student_links:
        progress = calculate_student_progress(link.student)

        students_data.append({
            'link': link,
            'student': link.student,
            'classroom': link.classroom,
            'teacher': link.classroom.teacher,
            **progress,
        })

    return render(
        request,
        'dashboard/students_crm.html',
        {
            'classes': classes,
            'selected_class': selected_class,
            'selected_class_id': selected_class_id,
            'students_data': students_data,
        }
    )
def classes_crm(request):
    if not request.user.is_authenticated:
        return redirect('login')

    if request.user.role not in ['assistant_admin', 'super_admin']:
        return redirect('home')

    if request.user.role == 'assistant_admin':
        classes = ClassRoom.objects.filter(
            assistant_admin=request.user
        )
    else:
        classes = ClassRoom.objects.all()

    classes = classes.select_related(
        'teacher',
        'assistant_admin'
    ).order_by('-created_at')

    classes_data = []

    for classroom in classes:
        active_students_count = StudentClass.objects.filter(
            classroom=classroom,
            is_active=True
        ).count()

        classes_data.append({
            'classroom': classroom,
            'active_students_count': active_students_count,
        })

    return render(
        request,
        'dashboard/classes_crm.html',
        {
            'classes_data': classes_data,
        }
    )

def teacher_crm(request):
    if not request.user.is_authenticated:
        return redirect('login')

    if request.user.role not in ['assistant_admin', 'super_admin']:
        return redirect('home')

    if request.user.role == 'assistant_admin':
        classes = ClassRoom.objects.filter(
            assistant_admin=request.user
        )
    else:
        classes = ClassRoom.objects.all()

    teachers = User.objects.filter(
        role='teacher'
    ).order_by('username')

    teacher_data = []

    for teacher in teachers:
        teacher_classes = classes.filter(
            teacher=teacher
        )

        classes_count = teacher_classes.count()

        students_count = StudentClass.objects.filter(
            classroom__in=teacher_classes,
            is_active=True
        ).count()

        attendance_count = Attendance.objects.filter(
            classroom__in=teacher_classes,
            marked_by=teacher
        ).count()

        homework_count = Homework.objects.filter(
            classroom__in=teacher_classes,
            created_by=teacher
        ).count()

        checked_count = HomeworkStatus.objects.filter(
            checked_by=teacher,
            homework__classroom__in=teacher_classes
        ).count()

        attendance_score = min(
            attendance_count * 2,
            100
        )

        homework_score = min(
            checked_count * 3,
            100
        )

        student_score = min(
            students_count * 5,
            100
        )

        performance = round(
            (attendance_score * 0.4) +
            (homework_score * 0.4) +
            (student_score * 0.2)
        )

        if performance >= 80:
            performance_status = 'Excellent'
        elif performance >= 60:
            performance_status = 'Good'
        elif performance >= 40:
            performance_status = 'Warning'
        else:
            performance_status = 'Needs Attention'

        teacher_data.append({
            'teacher': teacher,
            'classes_count': classes_count,
            'students_count': students_count,
            'attendance_count': attendance_count,
            'homework_count': homework_count,
            'checked_count': checked_count,

            'attendance_score': attendance_score,
            'homework_score': homework_score,
            'student_score': student_score,

            'performance': performance,
            'performance_status': performance_status,
        })

    return render(
        request,
        'dashboard/teacher_crm.html',
        {
            'teacher_data': teacher_data,
        }
    )
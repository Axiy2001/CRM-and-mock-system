from datetime import datetime

from django.shortcuts import render, redirect

from academics.models import ClassRoom, StudentClass
from .models import Payment


def get_payment_classes(user):
    if user.role == 'assistant_admin':
        return ClassRoom.objects.filter(assistant_admin=user)

    if user.role == 'super_admin':
        return ClassRoom.objects.all()

    if user.role == 'teacher':
        return ClassRoom.objects.filter(teacher=user)

    return ClassRoom.objects.none()


def parse_money(value):
    if not value:
        return 0

    clean_value = str(value).replace(' ', '')

    if not clean_value.isdigit():
        return 0

    return int(clean_value)


def calculate_payment_amount(default_amount, month_lessons, student_lessons):
    if default_amount <= 0 or month_lessons <= 0 or student_lessons <= 0:
        return 0

    lesson_price = default_amount / month_lessons
    return round(lesson_price * student_lessons)


def calculate_status(amount, paid_amount):
    if amount > 0 and paid_amount >= amount:
        return 'paid'

    if paid_amount > 0:
        return 'partial'

    return 'unpaid'


def payment_list(request):
    if not request.user.is_authenticated:
        return redirect('login')

    if request.user.role not in ['assistant_admin', 'super_admin', 'teacher']:
        return redirect('home')

    can_edit = request.user.role in ['assistant_admin', 'super_admin']
    classes = get_payment_classes(request.user)

    selected_class_id = request.GET.get('class_id')
    selected_month = request.GET.get('month') or datetime.today().strftime('%Y-%m')
    month_lessons = request.GET.get('month_lessons') or ''
    default_amount = request.GET.get('default_amount') or ''

    selected_class = None
    student_links = []
    payment_map = {}

    if selected_class_id:
        selected_class = classes.filter(id=selected_class_id).first()

    month_date = datetime.strptime(selected_month, '%Y-%m').date()

    if selected_class:
        student_links = StudentClass.objects.filter(
            classroom=selected_class,
            is_active=True
        ).select_related('student').order_by('student__username')

        payments = Payment.objects.filter(
            classroom=selected_class,
            month=month_date
        ).select_related('student', 'created_by')

        payment_map = {
            payment.student_id: payment for payment in payments
        }

    if request.method == 'POST':
        if not can_edit:
            return redirect('payment_list')

        class_id = request.POST.get('class_id')
        selected_month = request.POST.get('month')

        month_lessons_value = int(request.POST.get('month_lessons') or 0)
        default_amount_value = parse_money(request.POST.get('default_amount'))

        selected_class = classes.filter(id=class_id).first()

        if not selected_class:
            return redirect('payment_list')

        month_date = datetime.strptime(selected_month, '%Y-%m').date()

        student_links = StudentClass.objects.filter(
            classroom=selected_class,
            is_active=True
        ).select_related('student')

        for item in student_links:
            student = item.student

            student_lessons = int(
                request.POST.get(f'student_lessons_{student.id}') or 0
            )

            amount = calculate_payment_amount(
                default_amount=default_amount_value,
                month_lessons=month_lessons_value,
                student_lessons=student_lessons
            )

            paid_amount = parse_money(
                request.POST.get(f'paid_amount_{student.id}')
            )

            comment = request.POST.get(f'comment_{student.id}', '')

            status = calculate_status(amount, paid_amount)

            Payment.objects.update_or_create(
                student=student,
                classroom=selected_class,
                month=month_date,
                defaults={
                    'month_lessons': month_lessons_value,
                    'student_lessons': student_lessons,
                    'amount': amount,
                    'paid_amount': paid_amount,
                    'status': status,
                    'comment': comment,
                    'created_by': request.user,
                }
            )

        return redirect(
            f'/payments/?class_id={selected_class.id}'
            f'&month={selected_month}'
            f'&month_lessons={month_lessons_value}'
            f'&default_amount={default_amount_value}'
        )

    total_amount = 0
    total_paid = 0
    total_debt = 0

    for payment in payment_map.values():
        total_amount += payment.amount
        total_paid += payment.paid_amount
        total_debt += payment.debt

    context = {
        'classes': classes,
        'selected_class': selected_class,
        'selected_class_id': selected_class_id,
        'selected_month': selected_month,
        'month_lessons': month_lessons,
        'default_amount': default_amount,

        'student_links': student_links,
        'payment_map': payment_map,
        'can_edit': can_edit,

        'total_amount': total_amount,
        'total_paid': total_paid,
        'total_debt': total_debt,
    }

    return render(request, 'payments/payment_list.html', context)
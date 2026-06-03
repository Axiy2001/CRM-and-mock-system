from django.shortcuts import render, redirect

from .forms import MockTestCreateForm
from .models import (
    MockTest,
    ReadingPart,
    ReadingPassage,
    Question,
    ListeningPart,
    ListeningQuestion,
)


READING_PARTS = {
    1: (1, 13),
    2: (14, 26),
    3: (27, 40),
}

LISTENING_PARTS = {
    1: (1, 10),
    2: (11, 20),
    3: (21, 30),
    4: (31, 40),
}


def get_reading_instruction(part_order):
    start, end = READING_PARTS[part_order]
    return f"Read the text and answer questions {start}–{end}."


def get_listening_instruction(part_order):
    start, end = LISTENING_PARTS[part_order]
    return f"Listen and answer questions {start}–{end}."


def ensure_reading_structure(mock):
    for part_order in READING_PARTS:
        part, _ = ReadingPart.objects.get_or_create(
            mock=mock,
            order=part_order,
            defaults={
                'title': f'Part {part_order}',
                'instruction': get_reading_instruction(part_order),
            }
        )

        part.title = f'Part {part_order}'
        part.instruction = get_reading_instruction(part_order)
        part.save()

        passage, _ = ReadingPassage.objects.get_or_create(
            part=part,
            order=1,
            defaults={
                'title': f'Part {part_order} Passage',
                'content': '',
            }
        )

        passage.title = f'Part {part_order} Passage'
        passage.save()


def ensure_listening_structure(mock):
    for part_order in LISTENING_PARTS:
        part, _ = ListeningPart.objects.get_or_create(
            mock=mock,
            order=part_order,
            defaults={
                'title': f'Part {part_order}',
                'instruction': get_listening_instruction(part_order),
                'content': '',
            }
        )

        part.title = f'Part {part_order}'
        part.instruction = get_listening_instruction(part_order)
        part.save()


def get_reading_parts_data(mock):
    ensure_reading_structure(mock)

    parts_data = []

    parts = ReadingPart.objects.filter(
        mock=mock
    ).prefetch_related(
        'passages',
        'passages__questions'
    ).order_by('order')

    for part in parts:
        passage = part.passages.order_by('order').first()
        start, end = READING_PARTS[part.order]

        questions_map = {
            question.order: question
            for question in passage.questions.all()
        }

        question_rows = []

        for number in range(start, end + 1):
            question_rows.append({
                'number': number,
                'question': questions_map.get(number),
            })

        parts_data.append({
            'part': part,
            'content': passage,
            'start': start,
            'end': end,
            'question_rows': question_rows,
        })

    return parts_data


def get_listening_parts_data(mock):
    ensure_listening_structure(mock)

    parts_data = []

    parts = ListeningPart.objects.filter(
        mock=mock
    ).prefetch_related(
        'questions'
    ).order_by('order')

    for part in parts:
        start, end = LISTENING_PARTS[part.order]

        questions_map = {
            question.order: question
            for question in part.questions.all()
        }

        question_rows = []

        for number in range(start, end + 1):
            question_rows.append({
                'number': number,
                'question': questions_map.get(number),
            })

        parts_data.append({
            'part': part,
            'content': part,
            'start': start,
            'end': end,
            'question_rows': question_rows,
        })

    return parts_data


def mock_list(request):
    if not request.user.is_authenticated:
        return redirect('login')

    if request.user.role == 'mock_creator':
        mocks = MockTest.objects.filter(
            created_by=request.user
        ).order_by('-created_at')

        return render(
            request,
            'mock/mock_creator_list.html',
            {'mocks': mocks}
        )

    return render(request, 'mock/mock_list.html')


def create_mock(request):
    if not request.user.is_authenticated:
        return redirect('login')

    if request.user.role != 'mock_creator':
        return redirect('home')

    if request.method == 'POST':
        form = MockTestCreateForm(request.POST)

        if form.is_valid():
            mock = form.save(commit=False)
            mock.created_by = request.user
            mock.save()

            return redirect('mock_detail', mock_id=mock.id)
    else:
        form = MockTestCreateForm()

    return render(
        request,
        'mock/create_mock.html',
        {'form': form}
    )


def save_reading_mock(request, mock):
    ensure_reading_structure(mock)

    for part_order in READING_PARTS:
        part = ReadingPart.objects.filter(
            mock=mock,
            order=part_order
        ).first()

        passage = part.passages.order_by('order').first()

        passage.content = request.POST.get(
            f'content_text_{part_order}',
            ''
        )
        passage.save()

        passage.questions.all().delete()

        start, end = READING_PARTS[part_order]

        for number in range(start, end + 1):
            question_text = request.POST.get(
                f'question_text_{number}',
                ''
            ).strip()

            question_type = request.POST.get(
                f'question_type_{number}',
                'true_false'
            )

            correct_answer = request.POST.get(
                f'correct_answer_{number}',
                ''
            ).strip()

            if question_text or correct_answer:
                Question.objects.create(
                    passage=passage,
                    question_text=question_text,
                    question_type=question_type,
                    correct_answer=correct_answer,
                    order=number
                )


def save_listening_mock(request, mock):
    ensure_listening_structure(mock)

    for part_order in LISTENING_PARTS:
        part = ListeningPart.objects.filter(
            mock=mock,
            order=part_order
        ).first()

        part.content = request.POST.get(
            f'content_text_{part_order}',
            ''
        )
        part.save()

        part.questions.all().delete()

        start, end = LISTENING_PARTS[part_order]

        for number in range(start, end + 1):
            question_text = request.POST.get(
                f'question_text_{number}',
                ''
            ).strip()

            question_type = request.POST.get(
                f'question_type_{number}',
                'text'
            )

            correct_answer = request.POST.get(
                f'correct_answer_{number}',
                ''
            ).strip()

            if question_text or correct_answer:
                ListeningQuestion.objects.create(
                    part=part,
                    question_text=question_text,
                    question_type=question_type,
                    correct_answer=correct_answer,
                    order=number
                )


def mock_detail(request, mock_id):
    if not request.user.is_authenticated:
        return redirect('login')

    if request.user.role != 'mock_creator':
        return redirect('home')

    mock = MockTest.objects.filter(
        id=mock_id,
        created_by=request.user
    ).first()

    if not mock:
        return redirect('mock_list')

    if request.method == 'POST':
        if mock.mock_type == 'reading':
            save_reading_mock(request, mock)

        elif mock.mock_type == 'listening':
            save_listening_mock(request, mock)

        return redirect('mock_list')

    if mock.mock_type == 'reading':
        context = {
            'mock': mock,
            'builder_type': 'reading',
            'builder_title': 'Reading Builder',
            'content_placeholder': 'reading passage matnini shu yerga to‘liq yozing...',
            'parts_data': get_reading_parts_data(mock),
            'part_count': 3,
        }

    elif mock.mock_type == 'listening':
        context = {
            'mock': mock,
            'builder_type': 'listening',
            'builder_title': 'Listening Builder',
            'content_placeholder': 'listening task / notes / form textini shu yerga yozing...',
            'parts_data': get_listening_parts_data(mock),
            'part_count': 4,
        }

    else:
        context = {
            'mock': mock,
            'builder_type': 'writing',
        }

    return render(
        request,
        'mock/mock_detail.html',
        context
    )


def delete_mock(request, mock_id):
    if not request.user.is_authenticated:
        return redirect('login')

    if request.user.role != 'mock_creator':
        return redirect('home')

    mock = MockTest.objects.filter(
        id=mock_id,
        created_by=request.user
    ).first()

    if mock:
        mock.delete()

    return redirect('mock_list')
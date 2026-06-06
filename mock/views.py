import re

from django.shortcuts import render, redirect

from .forms import MockTestCreateForm
from .models import (
    MockTest,
    ReadingPart,
    ReadingPassage,
    Question,
    ListeningPart,
    ListeningQuestion,
    ListeningQuestionChoice,
    WritingSubmission,
    WritingTask,
    MockResult,
    StudentAnswer,
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


def normalize_answer(value):
    return value.strip().lower()


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
        'questions',
        'questions__choices'
    ).order_by('order')

    for part in parts:
        start, end = LISTENING_PARTS[part.order]

        questions_map = {
            question.order: question
            for question in part.questions.all()
        }

        question_rows = []

        for number in range(start, end + 1):
            question = questions_map.get(number)

            choices_map = {}
            if question:
                choices_map = {
                    choice.order: choice
                    for choice in question.choices.all()
                }

            option_rows = []
            for option_order in range(1, 9):
                option_rows.append({
                    'order': option_order,
                    'choice': choices_map.get(option_order),
                })

            question_rows.append({
                'number': number,
                'question': question,
                'option_rows': option_rows,
            })

        parts_data.append({
            'part': part,
            'content': part,
            'start': start,
            'end': end,
            'question_rows': question_rows,
        })

    return parts_data

WRITING_TASKS = {
    1: {
        'task_type': 'task1',
        'title': 'Task 1',
        'minimum_words': 150,
        'instruction': 'Write at least 150 words.'
    },
    2: {
        'task_type': 'task2',
        'title': 'Task 2',
        'minimum_words': 250,
        'instruction': 'Write at least 250 words.'
    },
}

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

    if request.user.role == 'student':
        mocks = MockTest.objects.filter(
            is_active=True
        ).order_by('-created_at')

        return render(
            request,
            'mock/student_mock_list.html',
            {'mocks': mocks}
        )

    return redirect('home')


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
                'text'
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

        image = request.FILES.get(f'part_image_{part_order}')

        if image:
            part.image = image

        audio = request.FILES.get(f'part_audio_{part_order}')

        if audio:
            part.audio_file = audio

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

            option_texts = []

            for option_order in range(1, 9):
                option_texts.append(
                    request.POST.get(
                        f'option_{number}_{option_order}',
                        ''
                    ).strip()
                )

            correct_options = request.POST.getlist(
                f'correct_option_{number}'
            )

            has_options = any(option_texts)

            if question_text or correct_answer or has_options:
                question = ListeningQuestion.objects.create(
                    part=part,
                    question_text=question_text,
                    question_type=question_type,
                    correct_answer=correct_answer,
                    order=number
                )

                for index, option_text in enumerate(option_texts, start=1):
                    if option_text:
                        ListeningQuestionChoice.objects.create(
                            question=question,
                            text=option_text,
                            is_correct=str(index) in correct_options,
                            order=index
                        )

def ensure_writing_structure(mock):
    for order, data in WRITING_TASKS.items():
        task, _ = WritingTask.objects.get_or_create(
            mock=mock,
            order=order,
            defaults={
                'task_type': data['task_type'],
                'title': data['title'],
                'instruction': data['instruction'],
                'minimum_words': data['minimum_words'],
            }
        )

        task.task_type = data['task_type']
        task.title = request_title = task.title or data['title']
        task.save()


def get_writing_tasks_data(mock):
    ensure_writing_structure(mock)

    return WritingTask.objects.filter(
        mock=mock
    ).order_by('order')


def save_writing_mock(request, mock):
    ensure_writing_structure(mock)

    tasks = WritingTask.objects.filter(
        mock=mock
    ).order_by('order')

    for task in tasks:
        task.title = request.POST.get(
            f'writing_title_{task.order}',
            task.title
        ).strip()

        task.instruction = request.POST.get(
            f'writing_instruction_{task.order}',
            ''
        ).strip()

        minimum_words = request.POST.get(
            f'writing_minimum_words_{task.order}',
            task.minimum_words
        )

        if str(minimum_words).isdigit():
            task.minimum_words = int(minimum_words)

        image = request.FILES.get(
            f'writing_image_{task.order}'
        )

        if image:
            task.image = image

        task.save()

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

        elif mock.mock_type == 'writing':
            save_writing_mock(request, mock)

        return redirect('mock_detail', mock_id=mock.id)

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
            'content_placeholder': 'listening matni, note, form, table yoki inline completion matnini shu yerga yozing. Masalan: moving across [31] and mountains...',
            'parts_data': get_listening_parts_data(mock),
            'part_count': 4,
        }

    elif mock.mock_type == 'writing':
        context = {
            'mock': mock,
            'builder_type': 'writing',
            'builder_title': 'Writing Builder',
            'writing_tasks': get_writing_tasks_data(mock),
        }

    else:
        context = {
            'mock': mock,
            'builder_type': 'unknown',
        }

    return render(
        request,
        'mock/mock_detail.html',
        context
    )

def split_inline_content(content):
    parts = re.split(r'(\[\d+\])', content or '')
    segments = []

    for part in parts:
        match = re.fullmatch(r'\[(\d+)\]', part)

        if match:
            segments.append({
                'is_input': True,
                'number': int(match.group(1)),
                'text': part,
            })
        else:
            segments.append({
                'is_input': False,
                'text': part,
            })

    return segments


def get_student_answer_map(student, mock):
    answers = StudentAnswer.objects.filter(
        student=student,
        mock=mock
    )

    return {
        answer.question_number: answer.answer
        for answer in answers
    }


def get_correct_answer_for_listening(question):
    correct_choices = question.choices.filter(
        is_correct=True
    ).order_by('order')

    if correct_choices.exists():
        return ', '.join([
            choice.text
            for choice in correct_choices
        ])

    return question.correct_answer


def check_listening_answer(question, student_answer):
    correct_choices = question.choices.filter(
        is_correct=True
    ).order_by('order')

    if correct_choices.exists():
        correct_values = sorted([
            normalize_answer(choice.text)
            for choice in correct_choices
        ])

        student_values = sorted([
            normalize_answer(value)
            for value in student_answer.split(',')
            if value.strip()
        ])

        return student_values == correct_values

    return normalize_answer(student_answer) == normalize_answer(question.correct_answer)


def take_mock(request, mock_id):
    if not request.user.is_authenticated:
        return redirect('login')

    if request.user.role != 'student':
        return redirect('home')

    mock = MockTest.objects.filter(
        id=mock_id,
        is_active=True
    ).first()

    if not mock:
        return redirect('mock_list')

    if mock.mock_type == 'reading':
        parts_data = get_reading_parts_data(mock)

        return render(
            request,
            'mock/take_reading.html',
            {
                'mock': mock,
                'parts_data': parts_data,
            }
        )

    if mock.mock_type == 'listening':
        parts = ListeningPart.objects.filter(
            mock=mock
        ).prefetch_related(
            'questions',
            'questions__choices'
        ).order_by('order')

        if request.method == 'POST':
            score = 0
            total_questions = 0

            StudentAnswer.objects.filter(
                student=request.user,
                mock=mock
            ).delete()

            for part in parts:
                questions = part.questions.all().order_by('order')

                for question in questions:
                    total_questions += 1

                    if question.question_type == 'multiple_choice':
                        submitted_values = request.POST.getlist(
                            f'answer_{question.order}'
                        )

                        student_answer = ', '.join(submitted_values)
                    else:
                        student_answer = request.POST.get(
                            f'answer_{question.order}',
                            ''
                        ).strip()

                    is_correct = check_listening_answer(
                        question,
                        student_answer
                    )

                    if is_correct:
                        score += 1

                    StudentAnswer.objects.create(
                        student=request.user,
                        mock=mock,
                        question_number=question.order,
                        answer=student_answer,
                        is_correct=is_correct
                    )

            MockResult.objects.create(
                student=request.user,
                mock=mock,
                score=score,
                total_questions=total_questions
            )

            return render(
                request,
                'mock/mock_result.html',
                {
                    'mock': mock,
                    'score': score,
                    'total_questions': total_questions,
                }
            )

        answer_map = get_student_answer_map(request.user, mock)

        parts_data = []

        for part in parts:
            questions = part.questions.all().order_by('order')

            parts_data.append({
                'part': part,
                'segments': split_inline_content(part.content),
                'questions': questions,
            })

        return render(
            request,
            'mock/listening_exam.html',
            {
                'mock': mock,
                'parts_data': parts_data,
                'answer_map': answer_map,
            }
        )

    if mock.mock_type == 'writing':
        tasks = WritingTask.objects.filter(
            mock=mock
        ).order_by('order')

        return render(
            request,
            'mock/take_writing.html',
            {
                'mock': mock,
                'tasks': tasks,
            }
        )

    return redirect('mock_list')

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
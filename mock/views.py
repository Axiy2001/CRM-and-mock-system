import re

from django.shortcuts import render, redirect

from .forms import MockTestCreateForm
from .models import (
    MockTest,
    MockAccess,
    ReadingPart,
    ReadingPassage,
    ReadingQuestionGroup,
    ReadingGroupOption,
    Question,
    Choice,
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

WRITING_TASKS = {
    1: {
        'task_type': 'task1',
        'title': 'Task 1',
        'minimum_words': 150,
        'instruction': 'Write at least 150 words.',
    },
    2: {
        'task_type': 'task2',
        'title': 'Task 2',
        'minimum_words': 250,
        'instruction': 'Write at least 250 words.',
    },
}


def normalize_answer(value):
    return (value or '').strip().lower()


def get_reading_instruction(part_order):
    start, end = READING_PARTS[part_order]
    return f"Read the text and answer questions {start}–{end}."

def get_listening_instruction(part_order):
    start, end = LISTENING_PARTS[part_order]
    return f"Listen and answer questions {start}–{end}."


def ensure_reading_structure(mock):
    for part_order in READING_PARTS:
        default_start, default_end = READING_PARTS[part_order]

        part, _ = ReadingPart.objects.get_or_create(
            mock=mock,
            order=part_order,
            defaults={
                'title': f'Part {part_order}',
                'instruction': f"Read the text and answer questions {default_start}–{default_end}.",
                'start_number': default_start,
                'end_number': default_end,
            }
        )

        part.title = f'Part {part_order}'

        if not part.start_number:
            part.start_number = default_start

        if not part.end_number:
            part.end_number = default_end

        part.instruction = (
            f"Read the text and answer questions "
            f"{part.start_number}–{part.end_number}."
        )

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
        task.title = task.title or data['title']
        task.save()


def get_reading_parts_data(mock):
    ensure_reading_structure(mock)

    parts_data = []

    parts = ReadingPart.objects.filter(
        mock=mock
    ).prefetch_related(
        'passages',
        'question_groups',
        'question_groups__options',
        'question_groups__questions',
        'question_groups__questions__choices',
    ).order_by('order')

    for part in parts:
        passage = part.passages.order_by('order').first()

        groups = part.question_groups.all().order_by(
            'order',
            'start_number'
        )

        parts_data.append({
            'part': part,
            'content': passage,
            'start': part.start_number,
            'end': part.end_number,
            'groups': groups,
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


def get_writing_tasks_data(mock):
    ensure_writing_structure(mock)

    return WritingTask.objects.filter(
        mock=mock
    ).order_by('order')


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


def get_reading_student_answer(request, question):
    if question.group.question_type == 'mcq_multi':
        values = request.POST.getlist(f'answer_{question.order}')
        return ', '.join(values)

    return request.POST.get(
        f'answer_{question.order}',
        ''
    ).strip()


def check_reading_answer(question, student_answer):
    correct_answer = normalize_answer(question.correct_answer)

    if question.group.question_type == 'mcq_multi':
        student_values = sorted([
            normalize_answer(value)
            for value in student_answer.split(',')
            if value.strip()
        ])

        correct_values = sorted([
            normalize_answer(value)
            for value in question.correct_answer.split(',')
            if value.strip()
        ])

        return student_values == correct_values

    return normalize_answer(student_answer) == correct_answer


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
            student_accesses__student=request.user,
            student_accesses__is_completed=False,
            is_active=True
        ).distinct().order_by('-created_at')

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

        if not part:
            continue

        passage = part.passages.order_by('order').first()

        if not passage:
            continue

        part_start = request.POST.get(f'part_start_{part_order}', '')
        part_end = request.POST.get(f'part_end_{part_order}', '')

        if part_start.isdigit():
            part.start_number = int(part_start)

        if part_end.isdigit():
            part.end_number = int(part_end)

        part.instruction = (
            f"Read the text and answer questions "
            f"{part.start_number}–{part.end_number}."
        )
        part.save()

        passage.content = request.POST.get(
            f'content_text_{part_order}',
            ''
        )
        passage.save()

        part.question_groups.all().delete()

        group_indexes = request.POST.getlist(
            f'group_index_{part_order}'
        )

        for group_position, group_index in enumerate(group_indexes, start=1):
            start_number = request.POST.get(
                f'group_start_{part_order}_{group_index}',
                ''
            )
            end_number = request.POST.get(
                f'group_end_{part_order}_{group_index}',
                ''
            )

            if not start_number.isdigit() or not end_number.isdigit():
                continue

            start_number = int(start_number)
            end_number = int(end_number)

            question_type = request.POST.get(
                f'group_type_{part_order}_{group_index}',
                'tfng'
            )

            word_limit = request.POST.get(
                f'group_word_limit_{part_order}_{group_index}',
                ''
            )

            group = ReadingQuestionGroup.objects.create(
                part=part,
                title=request.POST.get(
                    f'group_title_{part_order}_{group_index}',
                    f'Questions {start_number}-{end_number}'
                ).strip(),
                instruction=request.POST.get(
                    f'group_instruction_{part_order}_{group_index}',
                    ''
                ).strip(),
                question_type=question_type,
                start_number=start_number,
                end_number=end_number,
                option_title=request.POST.get(
                    f'group_option_title_{part_order}_{group_index}',
                    ''
                ).strip(),
                word_limit=int(word_limit) if word_limit.isdigit() else None,
                order=group_position
            )

            option_indexes = request.POST.getlist(
                f'option_index_{part_order}_{group_index}'
            )

            for option_position, option_index in enumerate(option_indexes, start=1):
                label = request.POST.get(
                    f'option_label_{part_order}_{group_index}_{option_index}',
                    ''
                ).strip()

                text = request.POST.get(
                    f'option_text_{part_order}_{group_index}_{option_index}',
                    ''
                ).strip()

                if label or text:
                    ReadingGroupOption.objects.create(
                        group=group,
                        label=label,
                        text=text,
                        order=option_position
                    )

            for number in range(start_number, end_number + 1):
                question_text = request.POST.get(
                    f'question_text_{part_order}_{group_index}_{number}',
                    ''
                ).strip()

                correct_answer = request.POST.get(
                    f'correct_answer_{part_order}_{group_index}_{number}',
                    ''
                ).strip()

                if not question_text and not correct_answer:
                    continue

                question = Question.objects.create(
                    passage=passage,
                    group=group,
                    question_text=question_text,
                    correct_answer=correct_answer,
                    order=number
                )

                choice_indexes = request.POST.getlist(
                    f'choice_index_{part_order}_{group_index}_{number}'
                )

                for choice_position, choice_index in enumerate(choice_indexes, start=1):
                    label = request.POST.get(
                        f'choice_label_{part_order}_{group_index}_{number}_{choice_index}',
                        ''
                    ).strip()

                    text = request.POST.get(
                        f'choice_text_{part_order}_{group_index}_{number}_{choice_index}',
                        ''
                    ).strip()

                    is_correct = request.POST.get(
                        f'choice_correct_{part_order}_{group_index}_{number}_{choice_index}'
                    ) == 'on'

                    if label or text:
                        Choice.objects.create(
                            question=question,
                            label=label,
                            text=text,
                            is_correct=is_correct,
                            order=choice_position
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
        audio = request.FILES.get(f'part_audio_{part_order}')

        if image:
            part.image = image

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

            option_texts = [
                request.POST.get(
                    f'option_{number}_{option_order}',
                    ''
                ).strip()
                for option_order in range(1, 9)
            ]

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
        return render(
            request,
            'mock/reading_builder.html',
            {
                'mock': mock,
                'parts_data': get_reading_parts_data(mock),
            }
        )

    if mock.mock_type == 'listening':
        return render(
            request,
            'mock/mock_detail.html',
            {
                'mock': mock,
                'builder_type': 'listening',
                'builder_title': 'Listening Builder',
                'content_placeholder': 'listening matni, note, form, table yoki inline completion matnini shu yerga yozing...',
                'parts_data': get_listening_parts_data(mock),
                'part_count': 4,
            }
        )

    if mock.mock_type == 'writing':
        return render(
            request,
            'mock/mock_detail.html',
            {
                'mock': mock,
                'builder_type': 'writing',
                'builder_title': 'Writing Builder',
                'writing_tasks': get_writing_tasks_data(mock),
            }
        )

    return render(
        request,
        'mock/mock_detail.html',
        {
            'mock': mock,
            'builder_type': 'unknown',
        }
    )


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

    access = MockAccess.objects.filter(
        student=request.user,
        mock=mock
    ).first()

    if not access:
        return redirect('mock_list')

    if mock.mock_type == 'reading':
        return take_reading_mock(request, mock, access)

    if mock.mock_type == 'listening':
        return take_listening_mock(request, mock, access)

    if mock.mock_type == 'writing':
        return take_writing_mock(request, mock, access)

    return redirect('mock_list')


def take_reading_mock(request, mock, access):
    parts_data = get_reading_parts_data(mock)

    if request.method == 'POST':
        score = 0
        total_questions = 0

        StudentAnswer.objects.filter(
            student=request.user,
            mock=mock
        ).delete()

        for part_data in parts_data:
            for group in part_data['groups']:
                for question in group.questions.all():
                    total_questions += 1

                    student_answer = get_reading_student_answer(
                        request,
                        question
                    )

                    is_correct = check_reading_answer(
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

        access.is_completed = True
        access.save()

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

    return render(
        request,
        'mock/take_reading.html',
        {
            'mock': mock,
            'parts_data': parts_data,
            'answer_map': answer_map,
        }
    )


def take_listening_mock(request, mock, access):
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

        access.is_completed = True
        access.save()

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


def take_writing_mock(request, mock, access):
    tasks = WritingTask.objects.filter(
        mock=mock
    ).order_by('order')

    if request.method == 'POST':
        task1_answer = request.POST.get(
            'task1_answer',
            ''
        ).strip()

        task2_answer = request.POST.get(
            'task2_answer',
            ''
        ).strip()

        WritingSubmission.objects.update_or_create(
            student=request.user,
            mock=mock,
            defaults={
                'task1_answer': task1_answer,
                'task2_answer': task2_answer,
            }
        )

        access.is_completed = True
        access.save()

        return render(
            request,
            'mock/writing_submitted.html',
            {
                'mock': mock,
            }
        )

    return render(
        request,
        'mock/take_writing.html',
        {
            'mock': mock,
            'tasks': tasks,
        }
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
from django.db import models
from django.conf import settings


READING_QUESTION_TYPE_CHOICES = (
    ('paragraph_matching', 'Paragraph Matching'),
    ('tfng', 'True / False / Not Given'),
    ('ynng', 'Yes / No / Not Given'),
    ('matching_headings', 'Matching Headings'),
    ('matching_people', 'Matching People / Features'),
    ('matching_information', 'Matching Information'),
    ('matching_endings', 'Matching Sentence Endings'),
    ('mcq_single', 'Multiple Choice Single'),
    ('mcq_multi', 'Multiple Choice Multiple'),
    ('summary_completion', 'Summary / Note / Table Completion'),
    ('sentence_completion', 'Sentence Completion'),
    ('short_answer', 'Short Answer / Fill in the Blank'),
)

LISTENING_QUESTION_TYPE_CHOICES = (
    ('text', 'Text / Completion'),
    ('inline_completion', 'Inline Completion'),
    ('single_choice', 'Single Choice'),
    ('multiple_choice', 'Multiple Choice'),
    ('dropdown', 'Matching / Dropdown'),
    ('map_dropdown', 'Map / Diagram Dropdown'),
    ('table_completion', 'Table Completion'),
    ('table_dropdown', 'Table Dropdown Matching'),
)


class MockTest(models.Model):
    MOCK_TYPE_CHOICES = (
        ('reading', 'Reading'),
        ('listening', 'Listening'),
        ('writing', 'Writing'),
    )

    title = models.CharField(max_length=255)
    mock_type = models.CharField(
        max_length=20,
        choices=MOCK_TYPE_CHOICES,
        default='reading'
    )
    description = models.TextField(blank=True, null=True)
    duration_minutes = models.PositiveIntegerField(default=60)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_mocks'
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.mock_type}"


class ReadingPart(models.Model):
    mock = models.ForeignKey(
        MockTest,
        on_delete=models.CASCADE,
        related_name='reading_parts'
    )
    title = models.CharField(max_length=255)
    instruction = models.TextField(blank=True, null=True)
    order = models.PositiveIntegerField(default=1)

    start_number = models.PositiveIntegerField(default=1)
    end_number = models.PositiveIntegerField(default=13)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.mock.title} - Reading Part {self.order}"


class ReadingPassage(models.Model):
    part = models.ForeignKey(
        ReadingPart,
        on_delete=models.CASCADE,
        related_name='passages'
    )
    title = models.CharField(max_length=255)
    content = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.part.mock.title} - {self.title}"


class ReadingQuestionGroup(models.Model):
    part = models.ForeignKey(
        ReadingPart,
        on_delete=models.CASCADE,
        related_name='question_groups'
    )

    title = models.CharField(
        max_length=300,
        blank=True
    )

    instruction = models.TextField(blank=True)

    question_type = models.CharField(
        max_length=40,
        choices=READING_QUESTION_TYPE_CHOICES,
        default='tfng'
    )

    start_number = models.PositiveIntegerField(default=1)
    end_number = models.PositiveIntegerField(default=1)

    option_title = models.CharField(
        max_length=255,
        blank=True,
        help_text='Masalan: List of Headings, List of People, Paragraphs A-I'
    )

    word_limit = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='Completion yoki short answer uchun'
    )

    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['part__order', 'order', 'start_number']

    def __str__(self):
        return f"{self.part.mock.title} - {self.title or self.question_type}"


class ReadingGroupOption(models.Model):
    group = models.ForeignKey(
        ReadingQuestionGroup,
        on_delete=models.CASCADE,
        related_name='options'
    )

    label = models.CharField(max_length=20)
    text = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['order', 'label']

    def __str__(self):
        return f"{self.label} - {self.text[:40]}"


class Question(models.Model):
    passage = models.ForeignKey(
        ReadingPassage,
        on_delete=models.CASCADE,
        related_name='questions'
    )

    group = models.ForeignKey(
        ReadingQuestionGroup,
        on_delete=models.CASCADE,
        related_name='questions'
    )

    question_text = models.TextField(blank=True)

    correct_answer = models.CharField(
        max_length=255,
        blank=True
    )

    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.passage.part.mock.title} - Question {self.order}"


class Choice(models.Model):
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='choices'
    )

    label = models.CharField(max_length=20)
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['order', 'label']

    def __str__(self):
        return f"{self.label}. {self.text}"


class ListeningPart(models.Model):
    mock = models.ForeignKey(
        MockTest,
        on_delete=models.CASCADE,
        related_name='listening_parts'
    )
    title = models.CharField(max_length=255)
    instruction = models.TextField(blank=True, null=True)
    audio_file = models.FileField(upload_to='listening_audio/', blank=True, null=True)
    image = models.ImageField(upload_to='listening_images/', blank=True, null=True)
    content = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.mock.title} - Listening Part {self.order}"


class ListeningQuestion(models.Model):
    part = models.ForeignKey(
        ListeningPart,
        on_delete=models.CASCADE,
        related_name='questions'
    )
    question_text = models.TextField()
    question_type = models.CharField(
        max_length=30,
        choices=LISTENING_QUESTION_TYPE_CHOICES,
        default='text'
    )
    correct_answer = models.CharField(max_length=255, blank=True)
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.part.mock.title} - Listening Question {self.order}"


class ListeningQuestionChoice(models.Model):
    question = models.ForeignKey(
        ListeningQuestion,
        on_delete=models.CASCADE,
        related_name='choices'
    )
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.text


class WritingTask(models.Model):
    TASK_TYPE_CHOICES = (
        ('task1', 'Task 1'),
        ('task2', 'Task 2'),
    )

    mock = models.ForeignKey(
        MockTest,
        on_delete=models.CASCADE,
        related_name='writing_tasks'
    )
    task_type = models.CharField(
        max_length=20,
        choices=TASK_TYPE_CHOICES,
        default='task1'
    )
    title = models.CharField(max_length=255)
    instruction = models.TextField(blank=True)
    image = models.ImageField(upload_to='writing_images/', blank=True, null=True)
    minimum_words = models.PositiveIntegerField(default=150)
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.mock.title} - Writing {self.title}"


class MockAccess(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='mock_accesses'
    )
    mock = models.ForeignKey(
        MockTest,
        on_delete=models.CASCADE,
        related_name='student_accesses'
    )
    given_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='given_mock_accesses'
    )
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'mock')

    def __str__(self):
        return f"{self.student.username} - {self.mock.title}"


class MockResult(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='mock_results'
    )
    mock = models.ForeignKey(
        MockTest,
        on_delete=models.CASCADE,
        related_name='results'
    )
    score = models.PositiveIntegerField(default=0)
    total_questions = models.PositiveIntegerField(default=0)
    finished_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.username} - {self.mock.title} - {self.score}"


class StudentAnswer(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='student_answers'
    )
    mock = models.ForeignKey(
        MockTest,
        on_delete=models.CASCADE,
        related_name='student_answers'
    )
    question_number = models.PositiveIntegerField()
    answer = models.TextField(blank=True)
    is_correct = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'mock', 'question_number')

    def __str__(self):
        return f"{self.student.username} - {self.mock.title} - {self.question_number}"


class WritingSubmission(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='writing_submissions'
    )
    mock = models.ForeignKey(
        MockTest,
        on_delete=models.CASCADE,
        related_name='writing_submissions'
    )
    task1_answer = models.TextField(blank=True)
    task2_answer = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    task1_score = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    task2_score = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    overall_band = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)

    class Meta:
        unique_together = ('student', 'mock')

    def __str__(self):
        return f"{self.student.username} - {self.mock.title} Writing"
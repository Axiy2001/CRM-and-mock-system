from django.db import models
from django.conf import settings


QUESTION_TYPE_CHOICES = (
    ('text', 'Text Answer'),
    ('multiple', 'Multiple Choice A/B/C'),
    ('true_false', 'TRUE / FALSE / NOT GIVEN'),
    ('matching', 'Matching'),
    ('map_labeling', 'Map / Diagram Labeling'),
    ('sentence_completion', 'Sentence Completion'),
    ('note_completion', 'Note Completion'),
    ('table_completion', 'Table Completion'),
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

    def __str__(self):
        return f"{self.mock.title} - Reading Part {self.order}"


class ReadingPassage(models.Model):
    part = models.ForeignKey(
        ReadingPart,
        on_delete=models.CASCADE,
        related_name='passages'
    )

    title = models.CharField(max_length=255)
    content = models.TextField()
    order = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.part.mock.title} - {self.title}"


class Question(models.Model):
    passage = models.ForeignKey(
        ReadingPassage,
        on_delete=models.CASCADE,
        related_name='questions'
    )

    question_text = models.TextField()

    question_type = models.CharField(
        max_length=30,
        choices=QUESTION_TYPE_CHOICES,
        default='text'
    )

    correct_answer = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.passage.part.mock.title} - Question {self.order}"


class Choice(models.Model):
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='choices'
    )

    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text


class ListeningPart(models.Model):
    mock = models.ForeignKey(
        MockTest,
        on_delete=models.CASCADE,
        related_name='listening_parts'
    )

    title = models.CharField(max_length=255)
    instruction = models.TextField(blank=True, null=True)

    audio_file = models.FileField(
        upload_to='listening_audio/',
        blank=True,
        null=True
    )

    content = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=1)

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
        choices=QUESTION_TYPE_CHOICES,
        default='text'
    )

    correct_answer = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.part.mock.title} - Listening Question {self.order}"


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
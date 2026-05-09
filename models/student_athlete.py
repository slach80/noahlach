"""
Student/Athlete/Player Model

Reusable for any child/participant entity linked to a parent/client:
- Sports: Player/Athlete
- Tutoring: Student
- Music: Student
- Therapy: Dependent (if applicable)
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

class Player(models.Model):
    """
    Child profile linked to parent/client.

    Rename to: Student, Athlete, Participant, Dependent, Child
    """

    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
        ('N', 'Prefer not to say'),
    ]

    # Link to parent/client
    client = models.ForeignKey('clients.Client', on_delete=models.CASCADE, related_name='players')

    # Basic info
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)

    # Contact (if old enough to have own phone/email)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=17, blank=True)

    # Profile
    profile_picture = models.ImageField(upload_to='players/', blank=True, null=True)
    bio = models.TextField(blank=True)

    # Medical/Safety (important for liability)
    medical_conditions = models.TextField(
        blank=True,
        help_text="Allergies, asthma, diabetes, etc."
    )
    medications = models.TextField(blank=True)
    dietary_restrictions = models.TextField(blank=True)

    # Performance/Progress tracking
    skill_level = models.CharField(
        max_length=20,
        choices=[
            ('beginner', 'Beginner'),
            ('intermediate', 'Intermediate'),
            ('advanced', 'Advanced'),
            ('elite', 'Elite'),
        ],
        default='beginner'
    )
    notes = models.TextField(
        blank=True,
        help_text="Coach/instructor notes on progress, behavior, strengths"
    )

    # Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['client', 'first_name']
        indexes = [
            models.Index(fields=['client', 'is_active']),
            models.Index(fields=['last_name', 'first_name']),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def age(self):
        """Calculate current age."""
        today = timezone.now().date()
        born = self.date_of_birth
        return today.year - born.year - ((today.month, today.day) < (born.month, born.day))

    @property
    def upcoming_bookings_count(self):
        """Count of upcoming sessions."""
        from bookings.models import Booking
        return Booking.objects.filter(
            player=self,
            scheduled_date__gte=timezone.now().date(),
            status__in=['pending', 'confirmed']
        ).count()


# CUSTOMIZATION EXAMPLES:

# 1. For tutoring platform - rename to Student and add education fields:
class Student(models.Model):
    """Student profile for tutoring platform."""
    parent = models.ForeignKey('clients.Parent', on_delete=models.CASCADE, related_name='students')

    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    date_of_birth = models.DateField()

    # Education-specific
    grade = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(12)],
        help_text="Current grade level (K=0, 1-12)"
    )
    school_name = models.CharField(max_length=200, blank=True)
    subjects_of_focus = models.TextField(
        blank=True,
        help_text="Math, English, Science, etc."
    )
    learning_style = models.CharField(
        max_length=20,
        choices=[
            ('visual', 'Visual'),
            ('auditory', 'Auditory'),
            ('kinesthetic', 'Kinesthetic'),
            ('reading', 'Reading/Writing'),
        ],
        blank=True
    )
    iep_504_plan = models.BooleanField(
        default=False,
        help_text="Has an Individualized Education Plan or 504 Plan"
    )
    accommodations = models.TextField(
        blank=True,
        help_text="Learning accommodations or special needs"
    )

    # Progress tracking
    current_gpa = models.DecimalField(
        max_digits=3, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(4)]
    )
    standardized_test_scores = models.JSONField(
        default=dict, blank=True,
        help_text='{"SAT": 1200, "ACT": 28}'
    )

    # Rest same as Player...


# 2. For music school - rename to MusicStudent:
class MusicStudent(models.Model):
    """Music student profile."""
    parent = models.ForeignKey('clients.Parent', on_delete=models.CASCADE, related_name='music_students')

    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    date_of_birth = models.DateField()

    # Music-specific
    instruments = models.CharField(
        max_length=200,
        help_text="Comma-separated list: Piano, Guitar, Violin"
    )
    primary_instrument = models.CharField(max_length=50)
    years_experience = models.IntegerField(default=0)
    practice_hours_per_week = models.IntegerField(null=True, blank=True)

    # Skill level per instrument
    skill_levels = models.JSONField(
        default=dict, blank=True,
        help_text='{"Piano": "intermediate", "Guitar": "beginner"}'
    )

    # Performance tracking
    recitals_attended = models.IntegerField(default=0)
    competitions_entered = models.IntegerField(default=0)
    awards = models.TextField(blank=True)

    # Equipment
    owns_instrument = models.BooleanField(default=False)
    needs_rental = models.BooleanField(default=False)

    # Rest same as Player...


# 3. For sports team management - extend Player with team fields:
class TeamPlayer(models.Model):
    """Player with team assignment."""
    client = models.ForeignKey('clients.Client', on_delete=models.CASCADE)

    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    date_of_birth = models.DateField()

    # Sports-specific
    team = models.ForeignKey(
        'teams.Team', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='players'
    )
    jersey_number = models.IntegerField(null=True, blank=True)
    position = models.CharField(max_length=50, blank=True)
    height = models.CharField(max_length=10, blank=True, help_text="e.g., 5'10\"")
    weight = models.IntegerField(null=True, blank=True, help_text="in pounds")

    # Athletic performance
    stats = models.JSONField(
        default=dict, blank=True,
        help_text='{"goals": 12, "assists": 8, "games_played": 20}'
    )

    # Eligibility
    physical_on_file = models.BooleanField(default=False)
    physical_expiration = models.DateField(null=True, blank=True)
    insurance_verified = models.BooleanField(default=False)

    # Rest same as Player...


# 4. For fitness/personal training - rename to TrainingClient:
class TrainingClient(models.Model):
    """Individual training client (can be adult, so no parent link)."""
    # Direct link to user (not via parent)
    user = models.OneToOneField('auth.User', on_delete=models.CASCADE)

    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')])

    # Fitness-specific
    fitness_goals = models.TextField(
        help_text="Weight loss, muscle gain, endurance, etc."
    )
    current_weight = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    goal_weight = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    body_fat_percentage = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)

    # Medical screening
    medical_clearance = models.BooleanField(default=False)
    injuries_history = models.TextField(blank=True)
    limitations = models.TextField(blank=True)

    # Progress tracking
    measurements = models.JSONField(
        default=dict, blank=True,
        help_text='{"chest": 40, "waist": 32, "bicep": 15}'
    )
    workout_history = models.JSONField(default=list, blank=True)

    # Rest same as Player...

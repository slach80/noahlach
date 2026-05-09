"""
Client/Parent Profile Model

Reusable for any client-based system:
- Sports: Parent/Guardian account
- Tutoring: Parent/Guardian
- Therapy: Primary contact
- Fitness: Client account
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator

class Client(models.Model):
    """
    Parent/Guardian/Primary Client account.

    Customization tips:
    - Rename to Parent, Guardian, Customer, Member as needed
    - Add/remove fields based on your domain
    - Adjust phone validator for international numbers
    """

    # OneToOne link to Django auth user
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='client_profile')

    # Contact info
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in format: '+999999999'. Up to 15 digits."
    )
    phone = models.CharField(validators=[phone_regex], max_length=17, blank=True)
    alternate_phone = models.CharField(validators=[phone_regex], max_length=17, blank=True)

    # Address (optional - useful for local services)
    address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=2, blank=True)
    zip_code = models.CharField(max_length=10, blank=True)

    # Emergency contact
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(validators=[phone_regex], max_length=17, blank=True)
    emergency_contact_relationship = models.CharField(max_length=50, blank=True)

    # Communication preferences
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    push_notifications = models.BooleanField(default=True)

    # Marketing
    marketing_emails = models.BooleanField(default=True)
    referral_code = models.CharField(max_length=20, unique=True, blank=True, null=True)
    referred_by = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='referrals'
    )

    # Account status
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True, help_text="Internal notes - not visible to client")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_booking_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['phone']),
            models.Index(fields=['referral_code']),
        ]

    def __str__(self):
        return self.user.get_full_name() or self.user.email

    @property
    def full_name(self):
        return self.user.get_full_name()

    @property
    def active_packages(self):
        """Get all active packages/memberships."""
        return self.packages.filter(is_active=True, expiration_date__gte=timezone.now().date())

    @property
    def has_active_package(self):
        return self.active_packages.exists()

    def get_total_sessions_remaining(self):
        """Sum of all remaining sessions across active packages."""
        return sum(pkg.sessions_remaining for pkg in self.active_packages)


# CUSTOMIZATION EXAMPLES:

# 1. For tutoring platform - rename and add education fields:
class Parent(models.Model):
    """Parent/Guardian for tutoring platform."""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=17)

    # Tutoring-specific
    preferred_tutor = models.ForeignKey('Tutor', on_delete=models.SET_NULL, null=True, blank=True)
    learning_environment = models.CharField(
        max_length=20,
        choices=[('in_home', 'In Home'), ('online', 'Online'), ('library', 'Library')],
        default='online'
    )
    school_district = models.CharField(max_length=100, blank=True)

    # Rest same as Client...


# 2. For fitness center - rename and add fitness fields:
class Member(models.Model):
    """Gym/Fitness member."""
    user = models.OneOneField(User, on_delete=models.CASCADE)

    # Fitness-specific
    membership_tier = models.CharField(
        max_length=20,
        choices=[('basic', 'Basic'), ('premium', 'Premium'), ('vip', 'VIP')],
        default='basic'
    )
    waiver_signed = models.BooleanField(default=False)
    waiver_signed_date = models.DateField(null=True, blank=True)
    medical_clearance = models.BooleanField(default=False)

    # Rest same as Client...


# 3. For therapy practice - rename and add clinical fields:
class Patient(models.Model):
    """Patient/client for therapy practice."""
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # Clinical-specific
    insurance_provider = models.CharField(max_length=100, blank=True)
    insurance_policy_number = models.CharField(max_length=50, blank=True)
    primary_concern = models.TextField(blank=True)
    referral_source = models.CharField(max_length=100, blank=True)

    # HIPAA compliance
    consent_to_treatment = models.BooleanField(default=False)
    consent_date = models.DateField(null=True, blank=True)

    # Rest same as Client...

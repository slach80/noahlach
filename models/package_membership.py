"""
Package/Membership/Subscription Model

Reusable for any session-based or time-based membership:
- Sports: Training packages (e.g., 10 sessions)
- Tutoring: Tutoring packages (e.g., 8 lessons)
- Music: Lesson bundles (e.g., 4 weeks)
- Fitness: Membership tiers (unlimited monthly)
- Therapy: Session bundles (e.g., 6 sessions)
"""

from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal

class Package(models.Model):
    """
    Package/tier definition (catalog of what can be purchased).

    Rename to: Plan, Membership, Bundle, PricingTier
    """

    PACKAGE_TYPE_CHOICES = [
        ('session_based', 'Session-Based (X sessions)'),
        ('time_based', 'Time-Based (Unlimited for X days)'),
        ('hybrid', 'Hybrid (X sessions OR X days)'),
    ]

    name = models.CharField(max_length=100)
    description = models.TextField()
    package_type = models.CharField(max_length=20, choices=PACKAGE_TYPE_CHOICES, default='session_based')

    # Pricing
    price = models.DecimalField(max_digits=8, decimal_places=2)
    sale_price = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True,
        help_text="Optional sale/promotional price"
    )

    # Session-based package
    sessions_included = models.IntegerField(
        default=0,
        help_text="Number of sessions included (0 for unlimited)"
    )

    # Time-based package
    duration_days = models.IntegerField(
        default=0,
        help_text="Validity period in days (0 for session-based only)"
    )

    # Features/benefits
    features = models.JSONField(
        default=list, blank=True,
        help_text='["Priority booking", "Unlimited group classes", "Free assessment"]'
    )

    # Status
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    display_order = models.IntegerField(default=0, help_text="Lower numbers appear first")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['display_order', 'price']

    def __str__(self):
        return f"{self.name} - ${self.price}"

    @property
    def effective_price(self):
        """Return sale price if set, otherwise regular price."""
        return self.sale_price if self.sale_price else self.price

    @property
    def price_per_session(self):
        """Calculate per-session cost."""
        if self.sessions_included > 0:
            return self.effective_price / self.sessions_included
        return Decimal('0.00')


class ClientPackage(models.Model):
    """
    Client's purchased package instance.

    Rename to: Membership, Subscription, ClientPlan, PurchasedBundle
    """

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('exhausted', 'Sessions Exhausted'),
        ('cancelled', 'Cancelled'),
    ]

    # Relationships
    client = models.ForeignKey('clients.Client', on_delete=models.CASCADE, related_name='packages')
    package = models.ForeignKey(Package, on_delete=models.PROTECT, related_name='client_purchases')

    # Tracking
    sessions_included = models.IntegerField()  # Snapshot from package at purchase time
    sessions_used = models.IntegerField(default=0)
    sessions_remaining = models.IntegerField()  # Calculated: included - used

    # Dates
    purchase_date = models.DateField(auto_now_add=True)
    activation_date = models.DateField(
        null=True, blank=True,
        help_text="When package was activated (can differ from purchase)"
    )
    expiration_date = models.DateField(
        help_text="Last day package is valid"
    )

    # Payment
    amount_paid = models.DecimalField(max_digits=8, decimal_places=2)
    payment_method = models.CharField(
        max_length=20,
        choices=[
            ('stripe', 'Credit Card'),
            ('cash', 'Cash'),
            ('check', 'Check'),
            ('comp', 'Complimentary'),
        ],
        default='stripe'
    )
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True)

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    is_active = models.BooleanField(default=True)

    # Auto-renewal (optional)
    auto_renew = models.BooleanField(default=False)
    stripe_subscription_id = models.CharField(max_length=255, blank=True)

    # Notes
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-purchase_date']
        indexes = [
            models.Index(fields=['client', 'is_active']),
            models.Index(fields=['expiration_date', 'is_active']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.client} - {self.package.name} ({self.sessions_remaining} left)"

    @property
    def is_valid(self):
        """Check if package is still usable."""
        if not self.is_active or self.status != 'active':
            return False
        if self.expiration_date < timezone.now().date():
            return False
        if self.package.package_type == 'session_based' and self.sessions_remaining <= 0:
            return False
        return True

    @property
    def usage_percentage(self):
        """Percentage of sessions used."""
        if self.sessions_included == 0:
            return 0
        return int((self.sessions_used / self.sessions_included) * 100)

    @property
    def days_remaining(self):
        """Days until expiration."""
        today = timezone.now().date()
        return (self.expiration_date - today).days

    def use_session(self):
        """Decrement available sessions."""
        if self.sessions_remaining <= 0:
            raise ValueError("No sessions remaining")
        self.sessions_used += 1
        self.sessions_remaining -= 1
        if self.sessions_remaining == 0:
            self.status = 'exhausted'
        self.save()

    def return_session(self):
        """Refund/return a session (e.g., on booking cancellation)."""
        self.sessions_used -= 1
        self.sessions_remaining += 1
        if self.status == 'exhausted':
            self.status = 'active'
        self.save()

    def check_expiration(self):
        """Update status if expired."""
        if self.expiration_date < timezone.now().date() and self.status == 'active':
            self.status = 'expired'
            self.is_active = False
            self.save()


# CUSTOMIZATION EXAMPLES:

# 1. For unlimited monthly membership (gym/fitness):
class Membership(models.Model):
    """Time-based unlimited membership."""
    member = models.ForeignKey('clients.Member', on_delete=models.CASCADE)
    tier = models.ForeignKey('plans.MembershipTier', on_delete=models.PROTECT)

    # Time-based only (no session tracking)
    start_date = models.DateField()
    end_date = models.DateField()

    # Recurring billing
    is_recurring = models.BooleanField(default=True)
    billing_cycle = models.CharField(
        max_length=20,
        choices=[('monthly', 'Monthly'), ('quarterly', 'Quarterly'), ('annual', 'Annual')],
        default='monthly'
    )
    next_billing_date = models.DateField()
    stripe_subscription_id = models.CharField(max_length=255)

    # Check-in tracking (not session limits)
    check_ins_this_month = models.IntegerField(default=0)

    # Benefits/access
    class_access = models.BooleanField(default=True)
    pool_access = models.BooleanField(default=False)
    guest_passes_remaining = models.IntegerField(default=0)

    status = models.CharField(
        max_length=20,
        choices=[('active', 'Active'), ('paused', 'Paused'), ('cancelled', 'Cancelled')],
        default='active'
    )


# 2. For tutoring bundles (prepaid lessons):
class TutoringPackage(models.Model):
    """Session-based tutoring bundle."""
    parent = models.ForeignKey('clients.Parent', on_delete=models.CASCADE)
    student = models.ForeignKey('clients.Student', on_delete=models.CASCADE)
    bundle = models.ForeignKey('packages.TutoringBundle', on_delete=models.PROTECT)

    lessons_included = models.IntegerField()
    lessons_used = models.IntegerField(default=0)
    lessons_remaining = models.IntegerField()

    # Subject-specific
    subject = models.CharField(
        max_length=50,
        choices=[('math', 'Math'), ('english', 'English'), ('science', 'Science'), ('test_prep', 'Test Prep')]
    )

    # Expiration (e.g., 6 months from purchase)
    purchase_date = models.DateField(auto_now_add=True)
    expiration_date = models.DateField()

    # Rollover option
    allow_rollover = models.BooleanField(
        default=False,
        help_text="Unused lessons can roll to next purchase"
    )


# 3. For music lessons (weekly recurring):
class LessonSubscription(models.Model):
    """Recurring weekly/monthly music lessons."""
    student = models.ForeignKey('clients.MusicStudent', on_delete=models.CASCADE)
    instrument = models.CharField(max_length=50)

    # Recurring schedule
    lessons_per_week = models.IntegerField(default=1)
    lesson_duration_minutes = models.IntegerField(default=60)
    weekly_rate = models.DecimalField(max_digits=6, decimal_places=2)

    # Schedule
    day_of_week = models.CharField(
        max_length=10,
        choices=[('monday', 'Monday'), ('tuesday', 'Tuesday'), ('wednesday', 'Wednesday'),
                 ('thursday', 'Thursday'), ('friday', 'Friday'), ('saturday', 'Saturday')]
    )
    time = models.TimeField()

    # Billing
    start_date = models.DateField()
    billing_cycle_day = models.IntegerField(
        default=1,
        help_text="Day of month to bill (1-31)"
    )
    stripe_subscription_id = models.CharField(max_length=255)

    # Pause/makeup lessons
    makeup_lessons_available = models.IntegerField(default=0)
    is_paused = models.BooleanField(default=False)
    pause_start_date = models.DateField(null=True, blank=True)
    pause_end_date = models.DateField(null=True, blank=True)

    status = models.CharField(
        max_length=20,
        choices=[('active', 'Active'), ('paused', 'Paused'), ('cancelled', 'Cancelled')],
        default='active'
    )

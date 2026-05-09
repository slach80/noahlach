# Client/Student/Athlete Components - Summary

Reusable Django models and templates for client-based systems with child profiles (students, athletes, patients, etc.).

## What's Included

### Models (`models/`)

1. **client_profile.py** - Parent/Guardian/Primary account
   - OneToOne → Django User
   - Contact info (phone, address, emergency contact)
   - Communication preferences (email/SMS/push)
   - Referral tracking
   - Active package tracking

2. **student_athlete.py** - Child/Participant profile
   - Linked to parent/client
   - Age, DOB, gender
   - Medical conditions, allergies, medications
   - Skill level tracking
   - Performance notes

3. **package_membership.py** - Session bundles or memberships
   - Session-based (10 sessions)
   - Time-based (unlimited for 30 days)
   - Hybrid (10 sessions OR 30 days)
   - Usage tracking
   - Auto-renewal support

### Dashboards (`dashboards/`)

1. **client_dashboard.html** - Parent portal view
2. **student_profile.html** - Individual student/athlete view

### Modules (`modules/`)

1. **sms_notifications.md** - Twilio SMS integration
   - Booking confirmations
   - 24-hour reminders
   - Cancellation alerts
   - Cost tracking
   - Opt-in/opt-out
   - TCPA compliance

## Use Cases

These components work for:

| Domain | Client = | Child = | Package = |
|--------|----------|---------|-----------|
| **Sports Training** | Parent | Athlete/Player | Training package (10 sessions) |
| **Tutoring** | Parent | Student | Lesson bundle (8 lessons) |
| **Music Lessons** | Parent | Music Student | Monthly lessons (4 weeks) |
| **Therapy** | Primary Contact | Patient/Dependent | Session bundle (6 sessions) |
| **Fitness** | Member | N/A (adult) | Membership (unlimited/month) |
| **Dance Studio** | Parent | Dancer | Class package (12 classes) |

## Model Relationships

```
User (Django auth)
  └── Client (OneToOne)
       ├── Player (ForeignKey, many)
       │    └── Booking (sessions attended)
       └── ClientPackage (ForeignKey, many)
            └── Package (catalog item)
```

## Customization Examples

### For Tutoring Platform

```python
# Rename
Client → Parent
Player → Student
Package → TutoringBundle

# Add fields
Student.grade = IntegerField()
Student.school_name = CharField()
Student.subjects_of_focus = TextField()
Student.iep_504_plan = BooleanField()
Student.current_gpa = DecimalField()
```

### For Music School

```python
# Rename
Client → Parent
Player → MusicStudent
Package → LessonSubscription

# Add fields
MusicStudent.instruments = CharField()
MusicStudent.primary_instrument = CharField()
MusicStudent.years_experience = IntegerField()
MusicStudent.recitals_attended = IntegerField()
```

### For Fitness Center

```python
# Rename
Client → Member
Player → (remove - adults)
Package → Membership

# Add fields
Member.membership_tier = CharField()  # basic/premium/vip
Member.waiver_signed = BooleanField()
Member.medical_clearance = BooleanField()
Membership.check_ins_this_month = IntegerField()
```

### For Therapy Practice

```python
# Rename
Client → Patient (direct user, no parent)
Player → (remove - adults)
Package → SessionBundle

# Add fields
Patient.insurance_provider = CharField()
Patient.insurance_policy_number = CharField()
Patient.primary_concern = TextField()
Patient.consent_to_treatment = BooleanField()
```

## Key Features

### Client Model
- Multiple child profiles per parent
- Emergency contact tracking
- Communication preferences (opt-in/out)
- Referral code system
- Package usage aggregation

### Student/Athlete Model
- Age calculation from DOB
- Medical/allergy tracking (liability protection)
- Skill level progression
- Coach/instructor notes
- Profile pictures

### Package Model
- Session-based (10 sessions)
- Time-based (30 days unlimited)
- Hybrid (whichever comes first)
- Usage percentage tracking
- Expiration management
- Auto-renewal via Stripe

## SMS Notifications (Twilio)

### Setup
1. Sign up at twilio.com
2. Purchase phone number ($1/month)
3. Add credentials to .env
4. Enable SMS_ENABLED=True

### Message Types
- Booking confirmation
- 24-hour reminder
- Cancellation alert
- Package expiring warning
- Payment received

### Cost
- $0.0079 per SMS (US)
- ~$8 per 1000 messages
- Budget tracking via SMSLog model

### Compliance
- ✅ Explicit opt-in required
- ✅ STOP keyword support
- ✅ 8 AM - 9 PM sending window
- ✅ Business name in messages

## File Structure

```
noahlach/
├── README.md                          # Overview
├── SUMMARY.md                         # This file
├── models/
│   ├── client_profile.py              # Parent/Guardian account
│   ├── student_athlete.py             # Student/Player profile
│   └── package_membership.py          # Session packages
├── dashboards/
│   ├── client_dashboard.html
│   └── student_profile.html
└── modules/
    └── sms_notifications.md           # Twilio integration
```

## Integration with Booking System

These models complement the booking system in `/home/slach/Projects/hustle`:

```python
# In Booking model (from hustle project)
class Booking(models.Model):
    client = ForeignKey('clients.Client')     # From noahlach
    player = ForeignKey('clients.Player')     # From noahlach
    client_package = ForeignKey('clients.ClientPackage')  # From noahlach
    
    # Rest from hustle booking system...
```

## Quick Start

1. Copy client_profile.py to your app
2. Copy student_athlete.py (rename as needed)
3. Copy package_membership.py
4. Adjust ForeignKey references
5. Run makemigrations + migrate
6. Create views for signup/profile management
7. Add Twilio for SMS (optional)

## Testing Checklist

- [ ] Create client account
- [ ] Add child/student profile
- [ ] Purchase package
- [ ] Use session from package
- [ ] Track package expiration
- [ ] Send SMS notification (if enabled)
- [ ] Update communication preferences
- [ ] Add referral code
- [ ] Calculate age from DOB
- [ ] Track medical conditions

## Production Checklist

- [ ] Enable SMS (Twilio credentials)
- [ ] Configure opt-in forms
- [ ] Set up STOP keyword handling
- [ ] Test SMS in production timezone
- [ ] Review medical info liability
- [ ] Set up package auto-expiration job
- [ ] Create parent signup flow
- [ ] Test child profile add/edit
- [ ] Verify referral tracking

## Common Patterns

### Parent Signup Flow
1. User creates account (allauth)
2. Create Client profile (OneToOne)
3. Add first child (Player/Student)
4. Purchase package
5. Book first session

### Child Management
- Parent can add multiple children
- Each child has own profile + stats
- Bookings link to specific child
- Package can be shared or per-child

### Package Usage
- Purchase creates ClientPackage instance
- Booking.confirm() decrements sessions_remaining
- Booking.cancel() returns session to package
- Expiration checked nightly (Celery task)

## Support

Template components extracted from production project. Customize for your domain. No warranty or ongoing support.

## License

Free to use and modify.

# SMS Notifications Module (Twilio)

Send booking confirmations, reminders, and alerts via SMS.

## Installation

```bash
pip install twilio
```

## Setup

### 1. Twilio Account
1. Sign up at https://www.twilio.com
2. Get Account SID + Auth Token
3. Purchase phone number ($1/month)
4. Verify test numbers (free tier)

### 2. Environment Variables

```bash
# .env
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+15551234567
SMS_ENABLED=True  # Toggle feature
```

### 3. Settings Configuration

```python
# settings.py
from environ import Env

env = Env()

# Twilio/SMS Config
SMS_ENABLED = env.bool('SMS_ENABLED', default=False)
TWILIO_ACCOUNT_SID = env('TWILIO_ACCOUNT_SID', default='')
TWILIO_AUTH_TOKEN = env('TWILIO_AUTH_TOKEN', default='')
TWILIO_PHONE_NUMBER = env('TWILIO_PHONE_NUMBER', default='')
```

## SMS Service

```python
# notifications/sms.py
from twilio.rest import Client
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class SMSService:
    """Handle SMS sending via Twilio."""
    
    def __init__(self):
        if settings.SMS_ENABLED:
            self.client = Client(
                settings.TWILIO_ACCOUNT_SID,
                settings.TWILIO_AUTH_TOKEN
            )
            self.from_number = settings.TWILIO_PHONE_NUMBER
        else:
            self.client = None
    
    def send_sms(self, to_number, message):
        """
        Send SMS message.
        
        Args:
            to_number: Phone in E.164 format (+15551234567)
            message: Text message (max 1600 chars)
        
        Returns:
            bool: True if sent, False otherwise
        """
        if not settings.SMS_ENABLED:
            logger.info(f'SMS disabled. Would send to {to_number}: {message}')
            return False
        
        try:
            # Validate phone format
            if not to_number.startswith('+'):
                to_number = f'+1{to_number}'  # Assume US if no country code
            
            msg = self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=to_number
            )
            
            logger.info(f'SMS sent to {to_number}. SID: {msg.sid}')
            return True
            
        except Exception as e:
            logger.error(f'SMS send failed to {to_number}: {str(e)}')
            return False
    
    def send_booking_confirmation(self, booking):
        """Send booking confirmation SMS."""
        message = f"""
Hi {booking.client.user.first_name}! Your session is confirmed:

{booking.session_type.name}
{booking.scheduled_date.strftime('%b %d')} at {booking.scheduled_time.strftime('%I:%M %p')}
Coach: {booking.coach.user.get_full_name()}

See you there!
""".strip()
        
        if booking.client.sms_notifications and booking.client.phone:
            return self.send_sms(booking.client.phone, message)
        return False
    
    def send_booking_reminder(self, booking):
        """Send 24-hour reminder."""
        message = f"""
Reminder: You have a session tomorrow!

{booking.session_type.name}
{booking.scheduled_date.strftime('%b %d')} at {booking.scheduled_time.strftime('%I:%M %p')}
Coach: {booking.coach.user.get_full_name()}
""".strip()
        
        if booking.client.sms_notifications and booking.client.phone:
            return self.send_sms(booking.client.phone, message)
        return False
    
    def send_cancellation_alert(self, booking):
        """Notify of cancellation."""
        message = f"""
Your session has been cancelled:

{booking.session_type.name}
{booking.scheduled_date.strftime('%b %d')} at {booking.scheduled_time.strftime('%I:%M %p')}

Please contact us to reschedule.
""".strip()
        
        if booking.client.sms_notifications and booking.client.phone:
            return self.send_sms(booking.client.phone, message)
        return False


# Singleton instance
sms_service = SMSService()
```

## Usage in Views

```python
# views.py
from notifications.sms import sms_service

def create_booking(request):
    # ... create booking ...
    
    # Send confirmation SMS
    sms_service.send_booking_confirmation(booking)
    
    return redirect('booking_success')
```

## Celery Task Integration

```python
# tasks.py
from celery import shared_task
from notifications.sms import sms_service
from bookings.models import Booking

@shared_task
def send_booking_confirmation_sms(booking_id):
    """Send confirmation SMS async."""
    booking = Booking.objects.get(pk=booking_id)
    sms_service.send_booking_confirmation(booking)

@shared_task
def send_24h_reminders():
    """Send reminders for sessions tomorrow."""
    from django.utils import timezone
    from datetime import timedelta
    
    tomorrow = timezone.now().date() + timedelta(days=1)
    
    bookings = Booking.objects.filter(
        scheduled_date=tomorrow,
        status='confirmed',
        client__sms_notifications=True
    ).select_related('client', 'coach', 'session_type')
    
    for booking in bookings:
        sms_service.send_booking_reminder(booking)
```

## Scheduled Reminders (Celery Beat)

```python
# In django admin or programmatically:
from django_celery_beat.models import PeriodicTask, CrontabSchedule

# Daily at 10 AM
schedule, _ = CrontabSchedule.objects.get_or_create(
    minute='0',
    hour='10',
    day_of_week='*',
    day_of_month='*',
    month_of_year='*',
)

PeriodicTask.objects.create(
    crontab=schedule,
    name='Send 24-hour reminders',
    task='myapp.tasks.send_24h_reminders',
)
```

## SMS Templates

```python
# notifications/sms_templates.py

def booking_confirmation(booking):
    return f"""Hi {booking.client.user.first_name}! Your {booking.session_type.name} session is confirmed for {booking.scheduled_date.strftime('%b %d')} at {booking.scheduled_time.strftime('%I:%M %p')}. See you there!"""

def reminder_24h(booking):
    return f"""Reminder: {booking.session_type.name} tomorrow at {booking.scheduled_time.strftime('%I:%M %p')} with {booking.coach.user.first_name}."""

def cancellation(booking):
    return f"""Your {booking.session_type.name} session on {booking.scheduled_date.strftime('%b %d')} has been cancelled. Contact us to reschedule."""

def rescheduled(old_booking, new_booking):
    return f"""Your session has been moved to {new_booking.scheduled_date.strftime('%b %d')} at {new_booking.scheduled_time.strftime('%I:%M %p')}."""

def package_expiring(client_package):
    return f"""Your {client_package.package.name} expires in 7 days. You have {client_package.sessions_remaining} sessions left."""

def payment_received(amount):
    return f"""Payment of ${amount} received. Thank you!"""
```

## Opt-In/Opt-Out

```python
# In Client model
class Client(models.Model):
    sms_notifications = models.BooleanField(default=False)
    
# In signup/profile form
<div class="form-check">
    <input type="checkbox" name="sms_notifications" id="id_sms_notifications">
    <label for="id_sms_notifications">
        Receive SMS reminders (msg & data rates may apply)
    </label>
</div>

# Opt-out link in SMS
message = f"{base_message}\n\nReply STOP to unsubscribe."
```

## Cost Management

### Pricing (as of 2024)
- **Outbound SMS**: $0.0079/message (US)
- **Phone number**: $1.00/month
- **Inbound SMS**: $0.0079/message

### Budget Tracking

```python
# models.py
class SMSLog(models.Model):
    """Track SMS sends for billing/analytics."""
    
    to_number = models.CharField(max_length=20)
    message = models.TextField()
    twilio_sid = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=20)
    cost = models.DecimalField(max_digits=6, decimal_places=4, default=0.0079)
    sent_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [models.Index(fields=['sent_at'])]

# Update service to log
def send_sms(self, to_number, message):
    msg = self.client.messages.create(...)
    
    SMSLog.objects.create(
        to_number=to_number,
        message=message,
        twilio_sid=msg.sid,
        status=msg.status,
    )
```

## Testing

### Test Phone Numbers (Free Tier)
1. Verify your personal number in Twilio console
2. Test with verified numbers (no charge)

### Mock in Development

```python
# settings.py
SMS_ENABLED = False  # Disable in dev

# sms.py logs instead of sending
if not settings.SMS_ENABLED:
    logger.info(f'[TEST SMS] To: {to_number}, Message: {message}')
    return True
```

### Unit Tests

```python
# tests.py
from unittest.mock import patch, MagicMock
from django.test import TestCase

class SMSTestCase(TestCase):
    @patch('notifications.sms.Client')
    def test_send_booking_confirmation(self, mock_client):
        mock_msg = MagicMock()
        mock_msg.sid = 'SM123'
        mock_client.return_value.messages.create.return_value = mock_msg
        
        booking = Booking.objects.create(...)
        result = sms_service.send_booking_confirmation(booking)
        
        self.assertTrue(result)
        mock_client.return_value.messages.create.assert_called_once()
```

## Compliance

### TCPA (US)
- ✅ Get explicit opt-in consent
- ✅ Provide opt-out mechanism (STOP keyword)
- ✅ Only send between 8 AM - 9 PM local time
- ✅ Identify your business in message

### Best Practices
- Keep messages under 160 chars when possible (1 segment = cheapest)
- Don't send promotional SMS without consent
- Honor opt-out requests immediately
- Include business name in first message

### Rate Limiting

```python
# Prevent SMS spam
from django.core.cache import cache

def send_sms(self, to_number, message):
    # Check rate limit (max 5 per hour per number)
    cache_key = f'sms_rate_{to_number}'
    count = cache.get(cache_key, 0)
    
    if count >= 5:
        logger.warning(f'SMS rate limit hit for {to_number}')
        return False
    
    # Send SMS...
    
    cache.set(cache_key, count + 1, 3600)  # 1 hour TTL
```

## Lessons Learned

1. **Test with real phones early** - Emulators don't catch carrier issues
2. **Character encoding matters** - Emojis/unicode = multiple segments
3. **Async is essential** - Don't block HTTP requests on SMS sends
4. **Log everything** - Track sends for debugging + billing reconciliation
5. **Respect timezones** - Convert to recipient's local time
6. **Provide web alternative** - Not everyone has SMS enabled
7. **Monitor deliverability** - Check Twilio logs for failed sends

## Production Checklist

- [ ] Upgrade to paid Twilio account
- [ ] Register toll-free number (better deliverability)
- [ ] Set up SMS webhooks (delivery receipts)
- [ ] Add rate limiting per user
- [ ] Implement opt-out handling
- [ ] Set up cost alerts in Twilio
- [ ] Test message templates with real users
- [ ] Add SMS analytics dashboard
- [ ] Document message frequency for users

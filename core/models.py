from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _

class CustomUser(AbstractUser):

    username = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        null=True,
        help_text=_("Optional username for the user."),
    )
    phone_number = models.CharField(
        max_length=15,
        blank=False,  # Changed to required for login
        null=False,   # Changed to required for login
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message=_("Phone number must be 9-15 digits, optionally starting with '+'."),
            )
        ],
        help_text=_("User's phone number, used as the primary login identifier (e.g., +1234567890)."),
    )
    selected_professional = models.CharField(
        max_length=100,
        blank=False,
        null=False,
        help_text=_("User's professional role or category."),
    )
    national_code = models.IntegerField(
        blank=True,
        null=True,
        help_text=_("User's national code."),
    )
    is_verified = models.BooleanField(
        default=False,
        help_text=_("Indicates whether the user's phone number is verified."),
    )
    verification_code = models.CharField(
        max_length=6,
        blank=True,
        null=True,
        help_text=_("Temporary code for SMS-based phone verification."),
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text=_("Timestamp when the user was created."),
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text=_("Timestamp when the user was last updated."),
    )

    USERNAME_FIELD = 'phone_number'  # Changed to use phone_number as the login field
    # S = ['email', 'first_name', 'last_name']  # Fields required during createsuperuser

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")
        db_table = "custom_user"
        indexes = [
            models.Index(fields=['phone_number']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['phone_number'],
                name='unique_phone_number',
                condition=models.Q(phone_number__isnull=False),
            ),
        ]

    def __str__(self):
        return self.phone_number or f"User {self.id}"

    # def clean(self):
    #     """
    #     Custom validation to ensure data integrity before saving.
    #     """
    #     super().clean()
    #     if self.phone_number and not self.phone_number.strip():
    #         self.phone_number = None
    #     if self.email:
    #         self.email = self.email.lower().strip()

    def save(self, *args, **kwargs):
        """
        Override save to normalize fields and ensure consistency.
        """
        self.clean()
        super().save(*args, **kwargs)

    # @property
    # def full_name(self):
    #     """
    #     Return the user's full name based on first_name and last_name.
    #     """
    #     return f"{self.first_name} {self.last_name}".strip() or self.phone_number
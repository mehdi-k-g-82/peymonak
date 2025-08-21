import django_filters
from django.contrib.auth import get_user_model
from django.db import models
from component.skill import SKILL
from component.provinces import PROVINCES
from register_ad.models import register_ad
import logging

logger = logging.getLogger(__name__)

User = get_user_model()

COOPERATION_KIND = [
    ('فرد', 'فرد'),
    ('شرکت', 'شرکت')
]

PROFESSIONAL_CHOICES = [
    ('Constructor', 'سازنده'),
    ('Contractor', 'پیمانکار'),
    ('Worker', 'کارگر'),
]

class RegisterAdFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(lookup_expr='icontains')
    user_name = django_filters.CharFilter(method='filter_by_all_fields', label='جستجو')
    skill = django_filters.ChoiceFilter(choices=SKILL, lookup_expr='iexact')
    province = django_filters.ChoiceFilter(choices=PROVINCES, lookup_expr='iexact')
    city = django_filters.CharFilter(lookup_expr='iexact')
    cooperation_kind = django_filters.ChoiceFilter(choices=COOPERATION_KIND, lookup_expr='iexact')
    created_at__gte = django_filters.DateFilter(field_name='created_at', lookup_expr='gte', label='از تاریخ')
    created_at__lte = django_filters.DateFilter(field_name='created_at', lookup_expr='lte', label='تا تاریخ')
    selected_professional = django_filters.CharFilter(method='filter_by_professional', label='حرفه')

    class Meta:
        model = register_ad
        fields = ['title', 'user_name', 'skill', 'province', 'city', 'cooperation_kind', 'created_at__gte', 'created_at__lte', 'selected_professional']

    def filter_by_all_fields(self, queryset, name, value):
        logger.debug(f"Filtering by user_name with value: {value}")
        search_terms = value.split() if value else []
        if not search_terms:
            return queryset

        combined_query = models.Q()
        for term in search_terms:
            term_query = (
                models.Q(title__icontains=term) |
                models.Q(user__username__icontains=term) |
                models.Q(user__name__icontains=term) |
                models.Q(province__icontains=term) |
                models.Q(city__icontains=term)
            )
            combined_query &= term_query

        return queryset.filter(combined_query)

    def filter_by_professional(self, queryset, name, value):
        logger.debug(f"Filtering by selected_professional with value: {value}")
        if not value:
            return queryset
        professional_values = value.split(',')
        valid_values = [choice[0] for choice in PROFESSIONAL_CHOICES]
        professional_values = [v for v in professional_values if v in valid_values]
        if not professional_values:
            return queryset
        return queryset.filter(user__selected_professional__in=professional_values)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        logger.debug(f"Received query parameters: {self.data}")

    @property
    def qs(self):
        parent = super().qs
        ordering = self.request.GET.get('ordering', '-created_at')
        logger.debug(f"Applying ordering: {ordering}")
        logger.debug(f"Filtered queryset count: {parent.count()}")
        return parent.order_by(ordering)
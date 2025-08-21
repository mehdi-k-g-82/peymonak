from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from provinces.modules.get_provinces_of_file_txt import Get_Provinces_of_File
from .models import Province
from django.db.models import F
from django.db import transaction
from django.db.utils import IntegrityError

# Load provinces once when the module loads
get_provinces_of_file = Get_Provinces_of_File()


@api_view(['GET'])
def check_province(request):
    province_name = request.query_params.get('name', '').strip()

    if not province_name:
        return Response(
            {"error": "name parameter is required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    is_valid = province_name in get_provinces_of_file.PROVINCES
    response_data = {
        "valid": is_valid,
        "province": province_name
    }

    if is_valid:
        try:
            with transaction.atomic():
                # add visited count
                updated = Province.objects.filter(
                    name=province_name
                ).update(
                    visited_count=F('visited_count') + 1
                )

                # If no records were updated, create a new one
                if updated == 0:
                    Province.objects.create(
                        name=province_name,
                        visited_count=1
                    )

        except IntegrityError:
            # Handle race condition case
            Province.objects.filter(
                name=province_name
            ).update(
                visited_count=F('visited_count') + 1
            )

    return Response(response_data)


"""
پیشنهاد کردن استانها برای بخش جست و جو
    مثال: /api/check/suggestions/?name=تهران
"""


@api_view(['GET'])
def province_suggestions(request):
    get_provinces_of_file = Get_Provinces_of_File()
    query = request.GET.get('q', '')
    suggestions = [p for p in get_provinces_of_file.PROVINCES if query in p]
    return Response({'suggestions': suggestions})

import django_filters
from .models import *
from django.db.models import Avg

class PropertyFilter(django_filters.FilterSet):
    """
    Property ke liye custom filters.
    """

    # 1. 'city' (शहर) के लिए फ़िल्टर (Exact match, case-insensitive)
    # ?city=Jaipur
    city = django_filters.CharFilter(field_name='city', lookup_expr='iexact')

    # 2. 'property_type' (प्रॉपर्टी टाइप) के लिए फ़िल्टर
    # ?property_type=villa
    property_type = django_filters.CharFilter(field_name='property_type', lookup_expr='iexact')

    # 3. 'max_guests' (गेस्ट) के लिए फ़िल्टर (Greater than or equal to)
    # ?guests=4 (4 ya 4 se zyada guest)
    guests = django_filters.NumberFilter(field_name='max_guests', lookup_expr='gte')

    # 4. 'min_price' (कम से कम कीमत)
    # ?min_price=5000
    min_price = django_filters.NumberFilter(field_name='base_price', lookup_expr='gte')

    # 5. 'max_price' (ज़्यादा से ज़्यादा कीमत)
    # ?max_price=10000
    max_price = django_filters.NumberFilter(field_name='base_price', lookup_expr='lte')

    # --- YEH NAYA FILTER ADD KAREIN (Neighbourhood) ---
    # ?area=vaishali
    area = django_filters.CharFilter(field_name='area', lookup_expr='icontains')

    # --- YEH NAYA FILTER ADD KAREIN (Rating) ---
    # ?min_rating=4
    min_rating = django_filters.NumberFilter(field_name="average_rating", lookup_expr='gte')

    # 6. 'amenities' (सुविधाएँ) के लिए फ़िल्टर
    # ?amenities=1&amenities=3 (Wi-Fi aur Pool dono chahiye)
    amenities = django_filters.ModelMultipleChoiceFilter(
        field_name='amenities__name', # Naam se filter karein
        to_field_name='name',
        queryset=Amenity.objects.all(),
        conjoined=True, # 'conjoined=True' ka matlab 'AND' hai (sari amenities honi chahiye)
    )

    certifications = django_filters.ModelMultipleChoiceFilter(
        field_name='certifications__name',
        to_field_name='name',
        queryset=Certification.objects.all(),
        conjoined=True,
    )

    views = django_filters.ModelMultipleChoiceFilter(
        field_name='views__name',
        to_field_name='name',
        queryset=ViewType.objects.all(),
        conjoined=True,
    )

    class Meta:
        model = Property
        # 'fields' list batati hai ki filterset ko kin fields par kaam karna hai
        fields = ['city', 'property_type', 'guests', 'min_price', 'max_price', 'amenities','area', 'min_rating', 'certifications', 'views']
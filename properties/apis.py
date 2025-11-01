#api views file 
from rest_framework import generics, permissions, filters
from .models import *
from .serializers import *
from .permission import IsVendor, IsOwner
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django_filters.rest_framework import DjangoFilterBackend
from .filters import PropertyFilter
from users.permissions import IsAdminRole # importing isAdmin role for property accept/reject feature from "users"
from django.db.models import Count, Avg, Q
from drf_spectacular.utils import extend_schema, OpenApiTypes, OpenApiResponse
from rest_framework import serializers


class DestinationResponseSerializer(serializers.Serializer):
    city = serializers.CharField()
    state = serializers.CharField()
    count = serializers.IntegerField()

class PropertyTypeResponseSerializer(serializers.Serializer):
    value = serializers.CharField()
    label = serializers.CharField()

# --- (MAIN) View 1: Property List View (Sari properties dikhane ke liye) ---

class PropertyListView(generics.ListAPIView):
    """
    API view to list all *APPROVED* properties.
    filtering (city, price, area...) aur Sorting (price, rating) ko support karta hai.
    """
    serializer_class = PropertyListSerializer
    permission_classes = [permissions.AllowAny]
    
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter] # (FIX 3) OrderingFilter add karein
    filterset_class = PropertyFilter
    
    ordering_fields = ['base_price', 'average_rating', 'created_at'] 
    # --------------------------

    def get_queryset(self):
        """
        Queryset for approved property
        """
        # (FIX 5)
        return Property.objects.filter(
            status=Property.PropertyStatus.APPROVED
        ).annotate(
            average_rating=Avg('reviews__rating', filter=Q(reviews__isnull=False), default=0.0)
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({'request': self.request})
        return context
    
# --- (MAIN) View 2: Property Detail View (Ek property dikhane ke liye) ---

class PropertyDetailView(generics.RetrieveAPIView):
    """
    API view to show details of a single property.
    Ise bhi koi bhi (bina login) access kar sakta hai.
    """
    queryset = Property.objects.all()
    serializer_class = PropertyDetailSerializer # 'Detail' wala serializer istemal karo
    permission_classes = [permissions.AllowAny]
    lookup_field = 'slug' # URL mein 'id' (ya 'pk') se property ko dhundhega

    def get_serializer_context(self):
        """
        Serializer ko 'request' object pass karta hai.
        (Taki 'is_in_wishlist' field user ko check kar sake)
        """
        context = super().get_serializer_context()
        context.update({'request': self.request})
        return context
    
# --- (MAIN) View 3: Property Create View (Vendor ke liye) ---

class PropertyCreateView(generics.CreateAPIView):
    """
    API view for Vendors to create a new property.
    Sirf 'Vendor' (jo login hai) hi ise access kar sakta hai.
    """
    queryset = Property.objects.all()
    serializer_class = PropertyCreateSerializer
    # --- YEH ZAROORI HAI ---
    # Pehle check karo ki user login hai, fir check karo ki woh Vendor hai
    permission_classes = [permissions.IsAuthenticated, IsVendor]

    def perform_create(self, serializer):
        """
        Property ko save karte waqt 'owner' ko set karein.
        """
        # 'owner' field ko zabardasti (forcefully) login kiye hue user par set karein
        serializer.save(owner=self.request.user)


# --- (MAIN) View 4: Property Manage View (Edit/Delete ke liye) ---

class PropertyManageView(generics.RetrieveUpdateDestroyAPIView):
    """
    API view for a Vendor to GET, UPDATE, or DELETE their *own* property.
    """
    queryset = Property.objects.all()
    serializer_class = PropertyUpdateSerializer # 'Update' wala serializer
    lookup_field = 'slug' # URL se 'id' lega
    
    # --- YEH ZAROORI HAI ---
    # User login hona chahiye AUR property ka maalik (owner) hona chahiye
    permission_classes = [permissions.IsAuthenticated, IsOwner]


# --- (MAIN) View 5: Wishlist Toggle View (Guest ke liye) ---

class ToggleWishlistView(APIView):
    """
    API view for Guests to add or remove a property from their wishlist.
    """
    # Sirf login kiye hue user hi ise access kar sakte hain
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, slug, *args, **kwargs):
        # 1. Property ko URL ke 'id' se get karo
        try:
            property_obj = Property.objects.get(slug=slug)
        except Property.DoesNotExist:
            return Response({'error': 'Property not found.'}, status=status.HTTP_404_NOT_FOUND)
            
        # 2. Logged-in user ko get karo
        user = request.user
        
        # 3. Check karo ki user 'guest' hai (Vendors/Admins ki wishlist nahi hoti)
        if user.role != 'guest':
            return Response(
                {'error': 'Only Guests can have a wishlist.'}, 
                status=status.HTTP_403_FORBIDDEN
            )

        # 4. Check karo ki property pehle se wishlist mein hai ya nahi
        if user.wishlist.filter(id=property_obj.id).exists():
            # Agar hai, to remove karo
            user.wishlist.remove(property_obj)
            message = 'Removed from wishlist'
        else:
            # Agar nahi hai, to add karo
            user.wishlist.add(property_obj)
            message = 'Added to wishlist'
            
        return Response({'message': message}, status=status.HTTP_200_OK)

    
''' class WishlistListView(generics.ListAPIView):
    """
    API to list all properties in the logged-in user's wishlist.
    (Used for /dashboard/wishlist route)
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PropertyListSerializer
    
    def get_queryset(self):
        # Logged-in user ki 'wishlist' field se properties nikalna
        user = self.request.user
        return user.wishlist.all().order_by('-created_at')

    def get_serializer_context(self):
        # Wishlist serializer ko 'request' object pass karna zaroori hai
        context = super().get_serializer_context()
        context.update({'request': self.request})
        return context '''
    

class VendorPropertyListView(generics.ListAPIView):
    """
    API view for a Vendor to list ONLY their *own* properties.
    """
    serializer_class = PropertyListSerializer # 'Card' wala serializer istemal karenge
    # Sirf login aur Vendor role wale hi access kar sakte hain
    permission_classes = [permissions.IsAuthenticated, IsVendor]

    def get_queryset(self):
        """
        Yeh function queryset ko badalta hai.
        Property.objects.all() ki jagah,
        yeh sirf logged-in user ki properties ko filter karta hai.
        """
        user = self.request.user
        return Property.objects.filter(owner=user)
    
    def get_serializer_context(self):
        # 'is_in_wishlist' ke liye request pass karna
        context = super().get_serializer_context()
        context.update({'request': self.request})
        return context
    
class AdminPropertyListView(generics.ListAPIView):
    """
    Admin ke liye: Platform ki saari properties ki list.
    (Pending, Approved, Rejected sab)
    """
    queryset = Property.objects.all().order_by('-created_at') # Sabse nayi upar
    serializer_class = AdminPropertyListSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminRole]
    # Hum yahaan 'PropertyFilter' ka istemal nahi kar rahe hain,
    # lekin admin dashboard mein search/filter ke liye add kar sakte hain.

class AdminApprovePropertyView(APIView):
    """
    Admin ke liye: Ek 'pending' property ko 'approve' karna.
    """
    permission_classes = [permissions.IsAuthenticated, IsAdminRole]

    def patch(self, request, slug, *args, **kwargs):
        try:
            prop = Property.objects.get(slug=slug)
        except Property.DoesNotExist:
            return Response({'error': 'Property not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        prop.status = Property.PropertyStatus.APPROVED
        prop.save()
        
        # (Optional) Yahaan Vendor ko email bhej sakte hain ki property approve ho gayi
        
        return Response({'message': 'Property approved successfully.'}, status=status.HTTP_200_OK)

class AdminRejectPropertyView(APIView):
    """
    Admin ke liye: Ek 'pending' property ko 'reject' karna.
    """
    permission_classes = [permissions.IsAuthenticated, IsAdminRole]

    def patch(self, request, slug, *args, **kwargs):
        try:
            prop = Property.objects.get(slug=slug)
        except Property.DoesNotExist:
            return Response({'error': 'Property not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        prop.status = Property.PropertyStatus.REJECTED
        prop.save()
        
        # (Optional) Yahaan Vendor ko email bhej sakte hain
        
        return Response({'message': 'Property rejected.'}, status=status.HTTP_200_OK)

class AdminManagePropertyView(generics.DestroyAPIView):
    """
    Admin ke liye: Ek property ko delete karna.
    (Yeh wahi view hai jo Vendor istemal karta hai, 
     lekin hum ise 'IsAdminRole' ke saath bhi istemal kar sakte hain
     ya ek alag view bana sakte hain. Alag banana behtar hai.)
    """
    queryset = Property.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsAdminRole] # Sirf Admin
    lookup_field = 'slug'


class CategoryListView(generics.ListAPIView):
    """
    API to list all available property categories.
    (Used for /categories route and filters)
    """
    queryset = Category.objects.all().order_by('name')
    serializer_class = SimpleCategorySerializer
    permission_classes = [permissions.AllowAny] # Koi bhi dekh sakta hai

class AmenityListView(generics.ListAPIView):
    """
    API to list all available amenities.
    (Used for property forms and filters)
    """
    queryset = Amenity.objects.all().order_by('name')
    serializer_class = SimpleAmenitySerializer
    permission_classes = [permissions.AllowAny]


class DestinationListView(APIView):
    """
    API to list all unique cities/destinations where APPROVED properties are available
    along with the total count of properties in that city.
    """
    permission_classes = [permissions.AllowAny]
    
#    @extend_schema(responses=DestinationResponseSerializer(many=True))
    def get(self, request, format=None):
        # 1. Sirf 'APPROVED' properties ko filter karein
        # 2. 'city' field ke hisab se group karein
        # 3. Har group ka count nikalen (annotation)
        cities_with_count = (
            Property.objects
            .filter(status=Property.PropertyStatus.APPROVED)
            .values('city', 'state') # State bhi zaroori hai
            .annotate(count=Count('city')) # Count nikalna
            .order_by('-count') # Sabse zyada properties wale city ko pehle dikhayen
        )
        
        # Output: JSON format mein list of objects return karein
        # [{'city': 'Lonavala', 'state': 'Maharashtra', 'count': 108}, ...]
        return Response(cities_with_count)
    

class AreaListView(APIView):
    """
    API to list all unique Areas (Neighbourhoods) where APPROVED properties are available.
    (Used for /search filter dropdown)
    """
    permission_classes = [permissions.AllowAny]

#    @extend_schema(responses=OpenApiResponse(response=[OpenApiTypes.STR]))
    def get(self, request, format=None):
        # Database se saare unique 'area' values nikalna
        areas = (
            Property.objects
            .filter(status=Property.PropertyStatus.APPROVED)
            .values_list('area', flat=True) # Sirf area ka naam nikalna
            .distinct()
            .order_by('area')
        )
        return Response(list(areas))

class PropertyTypeListView(APIView):
    """
    API to list all unique Property Types available.
    (Used for /search filter dropdown)
    """
    permission_classes = [permissions.AllowAny]

#    @extend_schema(responses=PropertyTypeResponseSerializer(many=True))
    def get(self, request, format=None):
        # Property model se 'PropertyType' choices ko nikalna
        types = Property.PropertyType.choices
        # Output: [{'value': 'farmhouse', 'label': 'Farmhouse'}, ...]
        type_list = [{'value': value, 'label': label} for value, label in types]
        return Response(type_list)
    

class CertificationListView(generics.ListAPIView):
    """
    API to list all available certifications.
    (Used for property forms and filters)
    """
    queryset = Certification.objects.all().order_by('name')
    serializer_class = SimpleCertificationSerializer
    permission_classes = [permissions.AllowAny]


class ViewTypeListView(generics.ListAPIView):
    """
    API to list all available View Types (e.g., Beach View).
    """
    queryset = ViewType.objects.all().order_by('name')
    serializer_class = SimpleViewTypeSerializer
    permission_classes = [permissions.AllowAny]
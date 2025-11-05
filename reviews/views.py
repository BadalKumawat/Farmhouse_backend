from rest_framework import generics, permissions, status , serializers
from rest_framework.response import Response
from .models import Review
from properties.models import Property
from .serializers import *
from .permissions import HasCompletedBooking
from users.permissions import IsAdminRole

class PropertyReviewListView(generics.ListAPIView):
    '''
    API to list all the review for the particular specific property 
    '''

    serializer_class= ReviewListSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        slug = self.kwargs.get('slug')
        return Review.objects.filter(property__slug=slug).order_by('-created_at')
    

class ReviewCreateView(generics.CreateAPIView):
    '''
    API for user to create new review for a property 
    '''

    queryset=Review.objects.all()
    serializer_class = ReviewCreateSerializer
    permission_classes = [permissions.IsAuthenticated,HasCompletedBooking]


    def get_permissions_object(self):
        slug=self.kwargs.get('slug')
        try:
            property_obj = Property.objects.get(slug=slug)
        except Property.DoesNotExist:
            return None
        
    def perform_create(self, serializer):
        # 1. URL se Property object ko get karein
        slug = self.kwargs.get('slug')
        try:
            property_obj = Property.objects.get(slug=slug)
        except Property.DoesNotExist:
            # (Waise permission check ise pehle hi pakad lega, but safety ke liye)
            raise serializers.ValidationError({'error': 'Property not found.'})

        # 2. Permission check karein (kya booking 'completed' thi?)
        self.check_object_permissions(self.request, property_obj)

        # 3. Check karein ki user pehle hi review post kar chuka hai
        if Review.objects.filter(user=self.request.user, property=property_obj).exists():
            raise serializers.ValidationError({'error': 'You have already reviewed this property.'})

        # 4. Serializer ko 'user' aur 'property' ke saath save karein
        serializer.save(user=self.request.user, property=property_obj)
    

# --- Feature 3: Vendor Dashboard Reviews ---
class VendorReviewListView(generics.ListAPIView):
    """
    API for a Vendor to see all reviews for *all* their properties.
    """
    serializer_class = ReviewListSerializer
    permission_classes = [permissions.IsAuthenticated] # (IsVendor bhi add kar sakte hain)

    def get_queryset(self):
        user = self.request.user
        # Sirf woh reviews jo vendor ki properties par hain
        return Review.objects.filter(property__owner=user).order_by('-created_at')
    


# --- Admin API ---
class AdminReviewListView(generics.ListAPIView):
    """
    Admin ke liye: Platform ke saare reviews.
    """
    queryset = Review.objects.all().order_by('-created_at')
    serializer_class = ReviewListSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminRole]



class AdminManageReviewView(generics.DestroyAPIView):
    """
    Admin ke liye: Ek review ko delete karna.
    """
    queryset = Review.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsAdminRole]
    lookup_field = 'id'
        
        

class ContactMessageCreateView(generics.CreateAPIView):
    """
    API to send a message via the contact form.
    """
    queryset = ContactMessage.objects.all()
    serializer_class = ContactMessageSerializer
    permission_classes = [permissions.AllowAny]
    
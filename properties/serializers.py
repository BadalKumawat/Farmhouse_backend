#serializers file
from rest_framework import serializers
from .models import *
from reviews.models import Review # Rating calculate karne ke liye
from django.db.models import Avg # Average nikalne ke liye
from django.utils import timezone
from datetime import timedelta
from users.serializers import UserProfileSerializer, AdminUserListSerializer
from users.models import CustomUser



# --- helper serializers ---

class SimpleViewTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ViewType
        fields = ['id', 'name']

class SimpleCertificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Certification
        fields = ['id', 'name']

class SimpleCategorySerializer(serializers.ModelSerializer):
    """
    Categories ki list dikhane ke liye
    """
    class Meta:
        model = Category
        fields = ['id', 'name']

class SimpleAmenitySerializer(serializers.ModelSerializer):
    """
    Amenities ki list dikhane ke liye
    """
    class Meta:
        model = Amenity
        fields = ['id', 'name']

class AmenitySerializer(serializers.ModelSerializer):
    """
    Sirf Amenity (suvidha) ka naam dikhane ke liye
    """
    class Meta:
        model = Amenity
        fields = ['id', 'name']

class PropertyImageSerializer(serializers.ModelSerializer):
    """
    Sirf property ki image URL dikhane ke liye
    """
    class Meta:
        model = PropertyImage
        fields = ['id', 'image']


# --- (MAIN) Serializer 1: List Serializer (Card ke liye) ---

class PropertyListSerializer(serializers.ModelSerializer):
    """
    Property card (list view) ke liye serializer.
    Ismein kam data aur calculated data hoga.
    """
    
    # --- Calculated Fields (Jo model mein nahi hain) ---
    
    # 1. Pehli Image (Main Image)
    main_image = serializers.SerializerMethodField()
    
    # 2. Average Rating
    average_rating = serializers.SerializerMethodField()
    
    # 3. 'Guest Favourite' Badge
    is_guest_favourite = serializers.SerializerMethodField()
    
    # 4. 'New' Badge
    is_new = serializers.SerializerMethodField()
    
    # 5. 'Wishlist' (Heart) Icon
    is_in_wishlist = serializers.SerializerMethodField()

    views = SimpleViewTypeSerializer(many=True, read_only=True)
    
    certifications = SimpleCertificationSerializer(many=True, read_only=True)

    class Meta:
        model = Property
        # Yeh fields hum 'card' par dikhayenge
        fields = [
            'id',
            'title',
            'city',
            'state',
            'base_price',
            'main_image',       # Calculated
            'average_rating',   # Calculated
            'is_guest_favourite', # Calculated
            'bedrooms',
            'max_guests',
            'views',
            'certifications',
            'is_new',           # Calculated
            'is_in_wishlist',   # Calculated
            'slug'
        ]

    # --- In Calculated Fields ke functions ---

    def get_main_image(self, obj):
        # 'obj' yahaan 'Property' model hai
        first_image = obj.images.first() # PropertyImage model se pehli image
        if first_image:
            # Agar image hai, to uska URL bhejo
            request = self.context.get('request')
            return request.build_absolute_uri(first_image.image.url)
        return None # Agar koi image nahi hai

    def get_average_rating(self, obj):
        # 'reviews' (related_name) ka istemal karke average nikalo
        avg = obj.reviews.aggregate(Avg('rating')).get('rating__avg')
        if avg:
            return round(avg, 2) # 4.888 ko 4.89 kar dega
        return 0 # Agar koi review nahi hai

    def get_is_guest_favourite(self, obj):
        # 'average_rating' field yahaan available nahi hai, 
        # isliye humein use dobara calculate karna hoga
        avg_rating = self.get_average_rating(obj)
        return avg_rating is not None and avg_rating >= 4.8

    def get_is_new(self, obj):
        # Check karo agar property pichle 30 dino mein bani hai
        return obj.created_at > (timezone.now() - timedelta(days=30))

    def get_is_in_wishlist(self, obj):
        user = self.context.get('request').user
        if user and user.is_authenticated:
            # Check karo ki yeh property 'user' ki 'wishlist' (jo model mein banayi thi) mein hai ya nahi
            return user.wishlist.filter(id=obj.id).exists()
        return False # Agar user login nahi hai
    

class PropertyDetailSerializer(serializers.ModelSerializer):
    """
    Property ke 'detail page' ke liye serializer.
    Ismein sab kuch hoga: images, amenities, owner, etc.
    """
    
    # --- Nested Serializers (Judi hui fields) ---
    
    # 1. Owner ki details dikhane ke liye
    # (Hum 'UserProfileSerializer' ka istemal kar rahe hain jo 'users' app mein banaya tha)
    owner = UserProfileSerializer(read_only=True)
    
    # 2. Saari images dikhane ke liye
    # (related_name='images' aur 'PropertyImageSerializer' ka istemal kar rahe hain)
    images = PropertyImageSerializer(many=True, read_only=True)
    
    # 3. Saari amenities dikhane ke liye
    # ('AmenitySerializer' ka istemal kar rahe hain)
    amenities = AmenitySerializer(many=True, read_only=True)
    
    # 4. To show all the view option 
    views = SimpleViewTypeSerializer(many=True, read_only=True)
    
    
    # --- Calculated Fields (Jo model mein nahi hain) ---
    
    # 1. Average Rating
    average_rating = serializers.SerializerMethodField()
    
    # 2. Total Reviews
    total_reviews = serializers.SerializerMethodField()
    
    # 3. 'Wishlist' (Heart) Icon
    is_in_wishlist = serializers.SerializerMethodField()

    class Meta:
        model = Property
        # Hum 'Property' model se saari fields dikhayenge
        fields = [
            'id', 'owner', 'title', 'property_type',
            'state', 'city', 'area', 'pin_code', 'google_maps_location',
            'short_description', 'full_description',
            'base_price', 'weekend_price', 'extra_guest_charge',
            'cleaning_fee', 'service_fee_percent',
            'check_in_time', 'check_out_time',
            'bedrooms', 'bathrooms', 'max_guests',
            'created_at',
            
            # --- Nested aur Calculated fields ---
            'images',           # Nested
            'amenities',        # Nested
            'certifications',
            'views',
            'average_rating',   # Calculated
            'total_reviews',    # Calculated
            'is_in_wishlist',   # Calculated
        ]
        
    # --- In Calculated Fields ke functions ---

    def get_average_rating(self, obj):
        avg = obj.reviews.aggregate(Avg('rating')).get('rating__avg')
        if avg:
            return round(avg, 2)
        return 0

    def get_total_reviews(self, obj):
        # 'reviews' (related_name) ka istemal karke count nikalo
        return obj.reviews.count()

    def get_is_in_wishlist(self, obj):
        user = self.context.get('request').user
        if user and user.is_authenticated:
            return user.wishlist.filter(id=obj.id).exists()
        return False
    

class WishlistListSerializer(serializers.ModelSerializer):
    """
    User ki apni wishlist items dikhane ke liye.
    """
    # Yahaan hum PropertyListSerializer ko istemal karenge
    # Taki saari Property ki details aur calculated fields (rating) mil jaye
    property = PropertyListSerializer(read_only=True)

    class Meta:
        # Hum CustomUser model ki 'wishlist' field ko target kar rahe hain
        model = CustomUser.wishlist.through 
        fields = ['property'] # Hum sirf property object dikhayenge


# --- (MAIN) Serializer 3: Create/Edit Property Serializer (Likne ke liye) ---

class PropertyCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating (and updating) a new property by a Vendor.
    """
    
    # --- Nested Fields (Data lene ke liye) ---

    views = serializers.PrimaryKeyRelatedField(
        queryset=ViewType.objects.all(),
        many=True,
        required=False
    )

    certifications = serializers.PrimaryKeyRelatedField(
        queryset=Certification.objects.all(),
        many=True,
        required=False
    )
    
    # 1. Amenities (List of IDs)
    # Frontend se [1, 5, 8] jaisi IDs ki list lega
    amenities = serializers.PrimaryKeyRelatedField(
        queryset=Amenity.objects.all(),
        many=True,
        required=False # Zaroori nahi hai
    )
    
    # 2. Images (List of Files)
    # Yeh field model mein nahi hai, ise hum 'create' method mein handle karenge
    images = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True, # Yeh field sirf data lene ke liye hai, dikhane ke liye nahi
        required=True
    )

    class Meta:
        model = Property
        # 'owner' ko chhodkar lagbhag sabhi fields jo Vendor dega
        fields = [
            'title', 'property_type',
            'state', 'city', 'area', 'pin_code', 'google_maps_location',
            'short_description', 'full_description',
            'base_price', 'weekend_price', 'extra_guest_charge',
            'cleaning_fee', 'service_fee_percent',
            'check_in_time', 'check_out_time',
            'bedrooms', 'bathrooms', 'max_guests',
            
            # --- Nested Fields ---
            'amenities', # IDs ki list
            'certifications',
            'views',
            'images',     # Files ki list
            'slug'
        ]
        

    def create(self, validated_data):
        """
        Property banate waqt Images ko alag se handle karein
        """
        # 1. 'images' data ko validated_data se nikal lein
        images_data = validated_data.pop('images')
        
        # 2. 'amenities' data ko bhi nikal lein
        amenities_data = validated_data.pop('amenities', [])

        # 3.
        certifications_data = validated_data.pop('certifications', [])

        # 4.
        views_data = validated_data.pop('views', [])

        # 6. 
        property_obj = Property.objects.create(**validated_data)
        
        # 7. Amenities ko property se link karein
        property_obj.amenities.set(amenities_data)

        # 8.
        property_obj.certifications.set(certifications_data)

        # 9.
        property_obj.views.set(views_data)

        # 10. Ab har image ke liye 'PropertyImage' object banayein
        for image_data in images_data:
            PropertyImage.objects.create(property=property_obj, image=image_data)
            
        return property_obj
    

class PropertyUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating (editing) an existing property.
    Images are not required here.
    """

    certifications = serializers.PrimaryKeyRelatedField(
        queryset=Certification.objects.all(),
        many=True,
        required=False
    )
    views = serializers.PrimaryKeyRelatedField(
        queryset=ViewType.objects.all(),
        many=True,
        required=False
    )
    
    amenities = serializers.PrimaryKeyRelatedField(
        queryset=Amenity.objects.all(),
        many=True,
        required=False # Edit karte waqt zaroori nahi
    )
    
    images = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True,
        required=False # Edit karte waqt zaroori nahi
    )

    class Meta:
        model = Property
        # 'owner' ko chhodkar sabhi fields
        fields = [
            'title', 'property_type',
            'state', 'city', 'area', 'pin_code', 'google_maps_location',
            'short_description', 'full_description',
            'base_price', 'weekend_price', 'extra_guest_charge',
            'cleaning_fee', 'service_fee_percent',
            'check_in_time', 'check_out_time',
            'bedrooms', 'bathrooms', 'max_guests',
            'amenities',
            'certifications',
            'views',
            'images'
        ]

    def update(self, instance, validated_data):
        """
        Update karte waqt Images aur Amenities ko handle karein.
        """
        # 'instance' woh purani property hai jise hum edit kar rahe hain
        
        # 1. Images (Agar nayi images aayi hain)
        if 'images' in validated_data:
            images_data = validated_data.pop('images')
            # Purani images delete karein (optional, lekin achha hai)
            instance.images.all().delete()
            # Nayi images create karein
            for image_data in images_data:
                PropertyImage.objects.create(property=instance, image=image_data)
        
        # 2. Amenities (Agar nayi list aayi hai)
        if 'amenities' in validated_data:
            amenities_data = validated_data.pop('amenities')
            instance.amenities.set(amenities_data)

        # 3.
        if 'certifications' in validated_data: # <-- ADD THIS BLOCK
            certifications_data = validated_data.pop('certifications')
            instance.certifications.set(certifications_data)

        # 4.
        if 'views' in validated_data: # <-- YEH NAYA BLOCK ADD KAREIN
            views_data = validated_data.pop('views')
            instance.views.set(views_data)


        # 5. Baaki fields ko default tareeke se update karein
        return super().update(instance, validated_data)
    




class AdminPropertyListSerializer(serializers.ModelSerializer):
    """
    Admin dashboard mein Properties ki list dikhane ke liye.
    (image_54539d.jpg ke hisab se)
    """
    # Category ka naam dikhane ke liye
    category = serializers.CharField(source='category.name', read_only=True)
    # Owner ka naam dikhane ke liye
    owner = serializers.CharField(source='owner.full_name', read_only=True)
    
    class Meta:
        model = Property
        fields = [
            'id', 
            'slug', 
            'title', 
            'category', # Category ka naam
            'base_price', 
            'cleaning_fee',
            'service_fee_percent',
            'status',   # 'pending', 'approved'
            'owner'     # Owner ka naam
        ]
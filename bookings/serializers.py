from rest_framework import serializers, filters
from .models import Booking
from properties.models import Property
from properties.serializers import PropertyListSerializer
from users.serializers import UserProfileSerializer
from payments.models import Payment

class BookingCreateSerializer(serializers.ModelSerializer):
    ''' 
    Serializers for creating new booking 
    '''
    property_slug = serializers.SlugField(write_only=True)

    class Meta:
        model = Booking
        fields = [
            'property_slug',
            'check_in_date',
            'check_out_date',
            'guests_count',
            'payment_method'
        ]
    
    def validate(self,data):

        # 1. for chaecking property is valid or not
        try:
            property_obj = Property.objects.get(
                slug=data['property_slug'],
                status=Property.PropertyStatus.APPROVED
            )
        except Property.DoesNotExist:
            raise serializers.ValidationError("Approved Property with this slug doesnot exist")
        
        # 2. Dates check check_in date must be before check-out date
        if data['check_in_date'] >= data['check_out_date']:
            raise serializers.ValidationError("check-out date must be after check-in date.") 
        
        # 3. Checking for Availabilty avoid two booking for same property
        existing_bookings = Booking.objects.filter(
            property=property_obj,
            status__in= ['pending','confirmed'],
            check_in_date__lt=data['check_out_date'],
            check_out_date__gt=data['check_out_date']        
            ).exists()
        
        if existing_bookings:
            raise serializers.ValidationError("These dates are not available for this property.")
        
        # 4. Cheacking for BlackOut dates 
        blackout = property_obj.blackout_dates.filter(
            date__range=[data['check_in_date'], data['check_out_date']]
        ).exists()
            
        if blackout:
            raise serializers.ValidationError("Booking is not avalibale for the Selected Dates ")

        total_nights = (data['check_out_date'] - data['check_in_date']).days
        base_price = property_obj.base_price * total_nights
        cleaning_fee = property_obj.cleaning_fee or 0
        service_fee_percent = property_obj.service_fee_percent or 0
        service_fee = (base_price * service_fee_percent) / 100
        total_price = base_price+cleaning_fee+service_fee

        # Data ko 'create' method ke liye save karein
        data['property'] = property_obj
        data['total_nights'] = total_nights
        data['price_per_night'] = property_obj.base_price
        data['cleaning_fee'] = cleaning_fee
        data['service_fee'] = service_fee
        data['total_price'] = total_price
        
        return data
    
    def create(self, validated_data):
        # removing th property_slug because it is not in booking model 
        validated_data.pop('property_slug',None)

        user = self.context['request'].user   #taking usr from request
        booking = Booking.objects.create(user=user, **validated_data)

        # Jaise hi booking bani, ek 'Pending' payment banayein
        Payment.objects.create(
            booking=booking,
            amount=booking.total_price,
            payment_method=booking.payment_method,
            status=Payment.PaymentStatus.PENDING # Default 'Pending'
        )

        # notification logic for admin and vendor

        try:
            property_obj = booking.property
            vendor = property_obj.owner
            
            # --- 1. Admin ko notification bhejein ---
            settings_obj = SiteSettings.objects.first()
            if settings_obj and settings_obj.notify_new_booking:
                admin_subject = f"New Booking Received: {property_obj.title}"
                admin_message = f"A new booking has been made by {user.full_name} for {property_obj.title} from {booking.check_in_date} to {booking.check_out_date}."
                admin_email = config('ADMIN_EMAIL', default=None)
                if admin_email:
                    send_mail(admin_subject, admin_message, settings.DEFAULT_FROM_EMAIL, [admin_email])
            
            # --- 2. Vendor ko notification bhejein ---
            if vendor.notify_new_bookings:
                vendor_subject = f"You have a new booking for {property_obj.title}!"
                vendor_message = f"Hi {vendor.first_name},\n\nA new booking has been made for your property, {property_obj.title}.\nGuest: {user.full_name}\nDates: {booking.check_in_date} to {booking.check_out_date}\nEarnings: ~₹{booking.total_price}"
                send_mail(vendor_subject, vendor_message, settings.DEFAULT_FROM_EMAIL, [vendor.email])
                
        except Exception as e:
            print(f"Error sending booking notification email: {e}")

        return booking


class BookingListSerializer(serializers.ModelSerializer):
    ''' 
    Guest or Vendor k my Booking Page k Liye 
    '''

    property = PropertyListSerializer(read_only=True)   # property ki card details dikhaane ka kaaam 

    class Meta:
        model = Booking
        fields = [
            'id', 'property', 'check_in_date', 'check_out_date', 
            'status', 'total_price', 'guests_count'
        ]

class BookingDetailSerializer(BookingListSerializer):
    """
    Booking ki poori detail dikhane ke liye (Guest aur Vendor)
    """
    # Hum 'price_breakdown' ko manually add kar rahe hain
    price_breakdown = serializers.SerializerMethodField()
    
    class Meta(BookingListSerializer.Meta):
        fields = BookingListSerializer.Meta.fields + [
            'price_per_night', 'cleaning_fee', 'service_fee',
            'total_nights', 'payment_method', 'booked_at',
            'price_breakdown'
        ]
        
    def get_price_breakdown(self, obj):
        return {
            'Base Price': f"₹{obj.price_per_night} x {obj.total_nights} nights",
            'Cleaning Fee': f"₹{obj.cleaning_fee}",
            'Service Fee': f"₹{obj.service_fee}",
            'Total': f"₹{obj.total_price}"
        }
    
class AdminBookingListSerializer(BookingListSerializer):
    """
    Admin Dashboard ke liye Booking List
    """
    # Admin ko user ki detail bhi dikhani hai
    user = UserProfileSerializer(read_only=True)
    
    class Meta(BookingListSerializer.Meta):
        # 'user' field ko 'property' ke saath replace karein
        fields = [
            'id', 'property', 'user', 'check_in_date', 'check_out_date', 
            'status', 'total_price'
        ]


class VendorBookingUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for Vendor to update booking status.
    (Vendor sirf 'confirm' ya 'cancel' kar sakta hai)
    """
    class Meta:
        model = Booking
        fields = ['status']
        extra_kwargs = {
            'status': {'choices': [
                Booking.BookingStatus.CONFIRMED, 
                Booking.BookingStatus.CANCELLED
            ]}
        }

class AdminBookingUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for Admin to update booking status.
    (Admin koi bhi status set kar sakta hai)
    """
    class Meta:
        model = Booking
        fields = ['status']
        # Admin ke paas saare options hain
        extra_kwargs = {
            'status': {'choices': Booking.BookingStatus.choices}
        }


class BookingReportSerializer(serializers.Serializer):
    '''
    Serializer for generating Booking Report
    '''
    total_bookings_in_range = serializers.IntegerField()

    total_revenue_in_range = serializers.DecimalField(max_digits=12, decimal_places=2)

    booking_over_time=serializers.ListField(
        child=serializers.DictField(),
        required=False
    )
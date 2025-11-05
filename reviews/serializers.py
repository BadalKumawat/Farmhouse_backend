from rest_framework import serializers
from .models import *
from users.models import CustomUser


class ReviewListSerializer(serializers.ModelSerializer):
    '''
    Srializer to list reviews on the propert detail page 
    '''

    user_name = serializers.CharField(source = 'user.full_name', read_only = True)
    user_image = serializers.ImageField(source='users.profile_picture', read_only=True)
    user_city = serializers.CharField(source='user.city',read_only=True)

    class Meta:
        model = Review
        fields= [
            'id','rating','comment','created_at','user_name','user_image','user_city'
        ]


class ReviewCreateSerializer(serializers.ModelSerializer):
    '''
    Serializer to create new review ffor guest user 
    '''

    class Meta:
        model = Review 
        fields = ['rating','comment']

    def validate(self, data):
        if not (1 <= data['rating'] <= 5):
            raise serializers.ValidationError('Rating must be between 1 and 5.')
        return data
    
class ContactMessageSerializer(serializers.ModelSerializer):
    """
    Serializer for the POST request to the contact form.
    """
    class Meta:
        model = ContactMessage
        fields = ['full_name', 'email', 'phone_number', 'subject', 'message']
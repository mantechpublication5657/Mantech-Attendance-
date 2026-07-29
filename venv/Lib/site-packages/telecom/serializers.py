from rest_framework import serializers


class SendOTPSerializer(serializers.Serializer):
    """
    This class handle data validation for send otp .
    """
    telecom = serializers.CharField()
    channel = serializers.CharField()

    def validate_channel(self, value):
        if not value in ['sms', 'email']:
            raise serializers.ValidationError(
                "channel must be 'sms' or 'email'.")
        return value


class VerifyOTPSerializer(serializers.Serializer):
    """
    This class handle data validation verify otp APIs.
    """
    telecom = serializers.CharField()
    code = serializers.CharField(min_length=6, max_length=6)


class SendSMSSerializer(serializers.Serializer):
    """
    This class handle data validation notify user.
    """
    body = serializers.CharField()
    telecom = serializers.CharField()
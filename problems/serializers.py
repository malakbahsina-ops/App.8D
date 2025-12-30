from rest_framework import serializers
from .models import Problem, ProblemAttachment, RootCause, Action
from users.serializers import UserSerializer

class ProblemAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProblemAttachment
        fields = '__all__'

class RootCauseSerializer(serializers.ModelSerializer):
    class Meta:
        model = RootCause
        fields = '__all__'

class ActionSerializer(serializers.ModelSerializer):
    assigned_to_details = UserSerializer(source='assigned_to', read_only=True)
    problem_details = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Action
        fields = '__all__'

    def get_problem_details(self, obj):
        p = obj.problem
        if not p:
            return None
        return {
            'id': p.id,
            'title': p.title,
            'current_step': p.current_step,
            'status': p.status,
        }

class ProblemSerializer(serializers.ModelSerializer):
    created_by_details = UserSerializer(source='created_by', read_only=True)
    leader_details = UserSerializer(source='leader', read_only=True)
    members_details = UserSerializer(source='members', many=True, read_only=True)
    
    d2_validated_by_details = UserSerializer(source='d2_validated_by', read_only=True)
    immediate_actions_validated_by_details = UserSerializer(source='immediate_actions_validated_by', read_only=True)
    rca_validated_by_details = UserSerializer(source='rca_validated_by', read_only=True)
    final_report_validated_by_details = UserSerializer(source='final_report_validated_by', read_only=True)
    
    # Nested data for read
    attachments = ProblemAttachmentSerializer(many=True, read_only=True)
    root_causes = RootCauseSerializer(many=True, read_only=True)
    actions = ActionSerializer(many=True, read_only=True)

    class Meta:
        model = Problem
        fields = '__all__'
        read_only_fields = [
            'created_by', 
            'created_at', 
            'updated_at',
            'd2_validated_by',
            'immediate_actions_validated_by',
            'rca_validated_by',
            'final_report_validated_by'
        ]

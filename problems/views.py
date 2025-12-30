from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Problem, Action, RootCause, ProblemAttachment
from .serializers import ProblemSerializer, ActionSerializer, RootCauseSerializer, ProblemAttachmentSerializer
from django.contrib.auth import get_user_model
from notifications.models import Notification

from .utils import generate_8d_pdf
from django.http import HttpResponse

class ProblemViewSet(viewsets.ModelViewSet):
    queryset = Problem.objects.all().order_by('-created_at')
    serializer_class = ProblemSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'])
    def dashboard_stats(self, request):
        from django.db.models import Count, Avg, F
        from django.db.models.functions import ExtractMonth
        from django.utils import timezone
        
        qs = self.get_queryset()

        # Filters from query params
        plant = request.query_params.get('plant')
        workshop = request.query_params.get('workshop_name')
        line = request.query_params.get('line_name')

        if plant:
            qs = qs.filter(plant=plant)
        if workshop:
            qs = qs.filter(workshop_name__icontains=workshop)
        if line:
            qs = qs.filter(line_name__icontains=line)

        # 1. Open Problems
        open_problems = qs.filter(status='OPEN').count()

        # 2. Problems without closing date (Status OPEN)
        no_close_date = qs.filter(status='OPEN').count()

        # 3. No pilot assigned (and OPEN)
        no_pilot = qs.filter(leader__isnull=True, status='OPEN').count()

        # 4. Average closing time (days)
        avg_duration = qs.filter(status='CLOSED', closed_at__isnull=False).aggregate(
            avg_diff=Avg(F('closed_at') - F('created_at'))
        )['avg_diff']
        
        avg_days = 0
        if avg_duration:
            avg_days = round(avg_duration.total_seconds() / (3600 * 24))

        # 5. Monthly evolution (Current Year)
        current_year = timezone.now().year
        monthly_data = (
            qs.filter(created_at__year=current_year)
            .annotate(month=ExtractMonth('created_at'))
            .values('month')
            .annotate(count=Count('id'))
            .order_by('month')
        )
        
        # Initialize with 0
        data_monthly_dict = {m: 0 for m in range(1, 13)}
        for entry in monthly_data:
            data_monthly_dict[entry['month']] = entry['count']
            
        formatted_monthly = [
            {'name': 'Jan', 'value': data_monthly_dict[1]},
            {'name': 'Fév', 'value': data_monthly_dict[2]},
            {'name': 'Mar', 'value': data_monthly_dict[3]},
            {'name': 'Apr', 'value': data_monthly_dict[4]},
            {'name': 'May', 'value': data_monthly_dict[5]},
            {'name': 'Jun', 'value': data_monthly_dict[6]},
            {'name': 'Jul', 'value': data_monthly_dict[7]},
            {'name': 'Aug', 'value': data_monthly_dict[8]},
            {'name': 'Sep', 'value': data_monthly_dict[9]},
            {'name': 'Oct', 'value': data_monthly_dict[10]},
            {'name': 'Nov', 'value': data_monthly_dict[11]},
            {'name': 'Déc', 'value': data_monthly_dict[12]},
        ]

        return Response({
            'open_problems': open_problems,
            'no_close_date': no_close_date,
            'no_pilot': no_pilot,
            'avg_close_time': avg_days,
            'monthly_evolution': formatted_monthly
        })

    @action(detail=False, methods=['get'])
    def analytics_stats(self, request):
        from django.db.models import Count
        
        qs = self.get_queryset()
        
        # 1. Status Distribution
        status_dist = qs.values('status').annotate(count=Count('id'))
        
        # 2. Level Distribution
        level_dist = qs.values('level').annotate(count=Count('id'))
        
        # 3. Root Causes Pareto
        # We need root causes linked to problems in the queryset
        root_causes = RootCause.objects.filter(problem__in=qs).values('category').annotate(count=Count('id')).order_by('-count')
        
        return Response({
            'status_distribution': list(status_dist),
            'level_distribution': list(level_dist),
            'root_cause_distribution': list(root_causes)
        })

    @action(detail=True, methods=['get'])
    def download_report(self, request, pk=None):
        problem = self.get_object()
        
        # Check permissions: Only Manager and Responsable can download
        if request.user.role not in ['MANAGER', 'RESPONSABLE']:
            return Response(
                {"detail": "Seuls les Managers et Responsables peuvent générer le rapport PDF."}, 
                status=status.HTTP_403_FORBIDDEN
            )
            
        # Check status: Only when problem is closed (D8 finished)
        if problem.status != 'CLOSED':
             return Response(
                {"detail": "Le rapport PDF ne peut être généré que lorsque toutes les étapes 8D sont terminées (Clôturé)."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        pdf_buffer = generate_8d_pdf(problem)
        response = HttpResponse(pdf_buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="rapport_8d_{problem.id}.pdf"'
        return response

    def get_queryset(self):
        from django.db.models import Q
        qs = super().get_queryset().order_by('-created_at')
        user = getattr(self.request, 'user', None)
        if not user or not user.is_authenticated:
            return qs
        if str(getattr(user, 'role', '')).upper().startswith('RESPONSABLE'):
            # Afficher les problèmes assignés au Responsable via actions
            # ou où il est membre explicitement
            return qs.filter(
                Q(members=user) | Q(actions__assigned_to=user)
            ).distinct().order_by('-created_at')
        return qs

    def perform_create(self, serializer):
        problem = serializer.save(created_by=self.request.user)
        User = get_user_model()
        
        # Determine the TEAM context
        # 1. If Creator is in a team (Operator/Supervisor/etc.)
        # 2. If Creator is Team Leader of a team
        
        target_team = None
        
        if self.request.user.role == 'TEAM_LEADER':
            target_team = self.request.user.led_teams.first()
            if target_team:
                problem.leader = self.request.user
        else:
            # Assume user is a member of some team (Operator, etc.)
            # Pick the first team they belong to
            target_team = self.request.user.teams.first()
            if target_team and target_team.leader:
                problem.leader = target_team.leader
        
        if target_team:
            # Populate members from the Team
            for member in target_team.members.all():
                problem.members.add(member)
            # Ensure leader is in members (if not already)
            if target_team.leader:
                 problem.members.add(target_team.leader)
            
            problem.save()
            
            # NOTIFICATIONS
            # If created by Leader -> Notify Supervisors OF THAT TEAM
            if self.request.user.role == 'TEAM_LEADER':
                team_supervisors = target_team.members.filter(role='SUPERVISOR')
                for sup in team_supervisors:
                    Notification.objects.create(
                        recipient=sup,
                        message=f"Nouveau problème signalé par le Team Leader: {problem.title}",
                        problem=problem
                    )
            # If created by Operator (or other member) -> Notify Leader OF THAT TEAM
            elif self.request.user.role == 'OPERATOR':
                 if target_team.leader:
                    Notification.objects.create(
                        recipient=target_team.leader,
                        message=f"Nouveau problème signalé par l'opérateur {self.request.user.username}",
                        problem=problem
                    )
        else:
            # Fallback if no team structure found (should not happen with full seed)
            pass

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        before_d2 = instance.d2_validated_by_id
        before_immediate = instance.immediate_actions_validated_by_id
        before_rca = instance.rca_validated_by_id
        before_final = instance.final_report_validated_by_id
        
        # Check if we are validating D2 (Supervisor action)
        if 'd2_validated' in request.data and request.data['d2_validated'] is True:
            # Manually set the validator to current user (Supervisor)
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            instance.d2_validated_by = request.user
            # Automatically advance step to D3 if at D2
            if instance.current_step == 'D2':
                instance.current_step = 'D3'
            instance.save()
            response = Response(serializer.data)
        else:
            response = super().partial_update(request, *args, **kwargs)
            # IMPORTANT: Refresh instance to reflect changes made by super().partial_update (e.g. current_step)
            instance.refresh_from_db()

        # Check for D0 -> D2 transition (Team Leader Validation)
        if 'current_step' in request.data and request.data['current_step'] == 'D2':
             if request.user.role in ['TEAM_LEADER', 'LEADER']:
                 # Notify Supervisors ONLY if D2 content is being submitted (e.g. d2_what is present)
                 # or if we want to notify that D0 is done and D2 started? 
                 # User wants notification when D2 is FILLED and SUBMITTED.
                 
                 is_filling_d2 = 'd2_what' in request.data
                 
                 if is_filling_d2:
                     # Notify Supervisors involved in the problem (Team Members)
                     supervisors = instance.members.filter(role='SUPERVISOR')
                     # Fallback if no supervisor in members (unlikely with proper teams)
                     if not supervisors.exists():
                         supervisors = get_user_model().objects.filter(role='SUPERVISOR', is_active=True)
                     
                     for sup in supervisors:
                         Notification.objects.create(
                             recipient=sup,
                             message=f"Nouvelle analyse QQOQCCP (D2) à valider pour: {instance.title}",
                             problem=instance
                         )

                 target_team = request.user.led_teams.first()
                 if target_team:
                     instance.leader = request.user
                     for member in target_team.members.all():
                         instance.members.add(member)
                     if target_team.leader:
                         instance.members.add(target_team.leader)
                     instance.save()
        
        # Check for D0 -> D3 transition (Legacy/Direct)
        if 'current_step' in request.data and request.data['current_step'] == 'D3':
             if request.user.role in ['TEAM_LEADER', 'MANAGER', 'LEADER']:
                 target_team = request.user.led_teams.first()
                 if target_team:
                     instance.leader = request.user
                     for member in target_team.members.all():
                         instance.members.add(member)
                     if target_team.leader:
                         instance.members.add(target_team.leader)
                     instance.save()
                 
                 # NOTIFY SUPERVISORS (Fix for Supervisor Notifications)
                 # When TL submits D2, step becomes D3. We must notify Supervisors.
                 supervisors = instance.members.filter(role='SUPERVISOR')
                 if not supervisors.exists():
                     supervisors = get_user_model().objects.filter(role='SUPERVISOR', is_active=True)
                 
                 for sup in supervisors:
                     Notification.objects.create(
                         recipient=sup,
                         message=f"Nouveau problème à traiter (D2 soumis): {instance.title}",
                         problem=instance
                     )
        
        instance.refresh_from_db()
        User = get_user_model()
        
        # Notify Team Leader when Supervisor validates D2
        if before_d2 is None and instance.d2_validated_by_id:
            # 1. Notify TL
            if instance.leader:
                Notification.objects.create(
                    recipient=instance.leader,
                    message="Votre analyse QQOQCCP (D2) a été validée par le Superviseur",
                    problem=instance
                )
            elif instance.created_by:
                 Notification.objects.create(
                    recipient=instance.created_by,
                    message="Votre analyse QQOQCCP (D2) a été validée par le Superviseur",
                    problem=instance
                )
            
            # 2. Notify Responsable (Targeted: Same Team as Supervisor) + Restrict access
            supervisor_teams = instance.d2_validated_by.teams.all()
            target_responsables = []
            for team in supervisor_teams:
                team_respos = list(team.members.filter(role='RESPONSABLE', is_active=True))
                target_responsables.extend(team_respos)
            primary_resp = target_responsables[0] if target_responsables else None
            if primary_resp:
                # Ensure only this Responsable is marked as involved for treatment
                instance.members.add(primary_resp)
                for m in instance.members.filter(role='RESPONSABLE').exclude(id=primary_resp.id):
                    instance.members.remove(m)
                Notification.objects.create(
                    recipient=primary_resp,
                    message=f"Actions immédiates définies par le Superviseur pour: {instance.title}",
                    problem=instance
                )
        
        if before_immediate is None and instance.immediate_actions_validated_by_id:
            # Notify Supervisors involved in the problem (Team Members)
            supervisors = instance.members.filter(role='SUPERVISOR')
            # Fallback if no supervisor in members (unlikely with proper teams)
            if not supervisors.exists():
                 supervisors = get_user_model().objects.filter(role='SUPERVISOR', is_active=True)
            
            for sup in supervisors:
                Notification.objects.create(
                    recipient=sup,
                    message="Actions immédiates validées par le Responsable",
                    problem=instance
                )
        if before_rca is None and instance.rca_validated_by_id:
            # Notify Responsables involved
            responsables = instance.members.filter(role__startswith='RESPONSABLE')
            for resp in responsables:
                Notification.objects.create(
                    recipient=resp,
                    message="Confirmation de l'analyse des causes racines par le Manager",
                    problem=instance
                )
        if before_final is None and instance.final_report_validated_by_id:
            # Notify Responsables involved
            responsables = instance.members.filter(role__startswith='RESPONSABLE')
            for resp in responsables:
                Notification.objects.create(
                    recipient=resp,
                    message="Rapport 8D final validé par le Manager",
                    problem=instance
                )
        
        # Check if Responsable submitted D4/D5 (Step moved to D5 or D6)
        # Assuming moving to D6 means D4/D5 are done and ready for validation
        if 'current_step' in request.data and request.data['current_step'] in ['D5', 'D6'] and str(getattr(request.user, 'role', '')).upper().startswith('RESPONSABLE'):
             if not instance.members.filter(id=request.user.id).exists():
                 return Response({'detail': "Accès refusé: ce problème n'est pas assigné à vous."}, status=status.HTTP_403_FORBIDDEN)
             managers = User.objects.filter(role='MANAGER', is_active=True)
             for manager in managers:
                 Notification.objects.create(
                     recipient=manager,
                     message=f"Analyse (Causes & Actions) soumise par le Responsable pour: {instance.title}",
                     problem=instance
                 )
             
             # Notify Assigned Users for Corrective Actions
             if request.data['current_step'] == 'D6':
                 # Re-fetch instance to ensure we have latest actions if they were just added
                 # Although related manager usually hits DB, safer to be sure or just use the relation
                 corrective_actions = instance.actions.filter(action_type='CORRECTIVE', assigned_to__isnull=False)
                 for action_item in corrective_actions:
                     if action_item.assigned_to:
                         Notification.objects.create(
                             recipient=action_item.assigned_to,
                             message=f"Nouvelle action corrective assignée: {action_item.description} (Délai: {action_item.due_date})",
                             problem=instance
                         )

        return response

    @action(detail=True, methods=['post'])
    def advance_step(self, request, pk=None):
        problem = self.get_object()
        # Logic to validate and advance step
        # For simplicity, just update the field from body
        next_step = request.data.get('next_step')
        if next_step:
            problem.current_step = next_step
            problem.save()
            return Response({'status': 'Step updated'})
        return Response({'error': 'No step provided'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        problem = self.get_object()
        problem.status = 'CLOSED'
        problem.current_step = 'D8'
        problem.final_report_validated_by = request.user
        problem.save()
        User = get_user_model()
        
        # Notify Leaders in Team
        leaders = problem.members.filter(role='TEAM_LEADER')
        if not leaders.exists() and problem.leader:
             Notification.objects.create(recipient=problem.leader, message="Rapport 8D clôturé par le Manager", problem=problem)
        for leader in leaders:
            Notification.objects.create(
                recipient=leader,
                message="Rapport 8D clôturé par le Manager",
                problem=problem
            )
            
        # Notify Responsables in Team
        responsables = problem.members.filter(role__startswith='RESPONSABLE')
        for resp in responsables:
            Notification.objects.create(
                recipient=resp,
                message="Rapport 8D final validé et clôturé",
                problem=problem
            )
        return Response({'status': 'Problem closed'})

    @action(detail=True, methods=['post'])
    def reject_final(self, request, pk=None):
        problem = self.get_object()
        # Only Manager can reject at D8
        if request.user.role != 'MANAGER':
            return Response({'error': 'Seul le manager peut rejeter en D8'}, status=status.HTTP_403_FORBIDDEN)
        # Mark final decision as rejected (stay OPEN at D8)
        problem.current_step = 'D8'
        problem.status = 'OPEN'
        problem.final_report_validated_by = request.user
        problem.save()
        
        # Notify involved parties (Team members only)
        User = get_user_model()
        responsables = problem.members.filter(role__startswith='RESPONSABLE')
        for resp in responsables:
            Notification.objects.create(
                recipient=resp,
                message="Rapport 8D final rejeté par le Manager",
                problem=problem
            )
        leaders = problem.members.filter(role='TEAM_LEADER')
        for leader in leaders:
            Notification.objects.create(
                recipient=leader,
                message="Rapport 8D final rejeté par le Manager",
                problem=problem
            )
        return Response({'status': 'Final validation rejected'})

    @action(detail=True, methods=['post'])
    def submit_d7_validation(self, request, pk=None):
        problem = self.get_object()
        if not str(getattr(request.user, 'role', '')).upper().startswith('RESPONSABLE'):
             return Response({'error': 'Seul le responsable peut soumettre pour validation'}, status=status.HTTP_403_FORBIDDEN)
        
        if problem.current_step != 'D7':
            return Response({'error': f"Le problème doit être à l'étape D7 (actuellement {problem.current_step}). Validez d'abord les actions correctives."}, status=status.HTTP_400_BAD_REQUEST)

        # Notify Managers (Team Members)
        managers = problem.members.filter(role='MANAGER')
        if not managers.exists():
             managers = get_user_model().objects.filter(role='MANAGER', is_active=True)
        
        for m in managers:
            Notification.objects.create(
                recipient=m,
                message=f"Validation des actions préventives (D7) demandée pour: {problem.title}",
                problem=problem
            )
        return Response({'status': 'Validation demandée envoyée au Manager'})

    @action(detail=True, methods=['post'])
    def validate_d7(self, request, pk=None):
        problem = self.get_object()
        if request.user.role != 'MANAGER':
            return Response({'error': 'Seul le manager peut valider D7'}, status=status.HTTP_403_FORBIDDEN)
        
        # Mark D7 as done -> Advance to D8
        problem.current_step = 'D8'
        problem.save()

        # Update Preventive Actions to VERIFIED
        problem.actions.filter(action_type='PREVENTIVE', status='DONE').update(status='VERIFIED')
        
        # Notify Responsable
        responsables = problem.members.filter(role='RESPONSABLE')
        for resp in responsables:
             Notification.objects.create(
                recipient=resp,
                message=f"Actions préventives (D7) validées par le Manager. Problème passé à D8.",
                problem=problem
            )
            
        return Response({'status': 'D7 validé, passage à D8'})

class ActionViewSet(viewsets.ModelViewSet):
    queryset = Action.objects.all()
    serializer_class = ActionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params
        assigned_to = params.get('assigned_to')
        action_type = params.get('action_type')
        status_q = params.get('status')
        problem_id = params.get('problem')
        if assigned_to:
            qs = qs.filter(assigned_to_id=assigned_to)
        if action_type:
            qs = qs.filter(action_type=action_type)
        if status_q:
            qs = qs.filter(status=status_q)
        if problem_id:
            qs = qs.filter(problem_id=problem_id)
        return qs.order_by('-created_at')

    def perform_create(self, serializer):
        problem_id = self.request.data.get('problem')
        if problem_id:
            try:
                problem = Problem.objects.get(id=problem_id)
            except Problem.DoesNotExist:
                return super().perform_create(serializer)
            # Restreindre la création aux Responsables impliqués:
            # - Membre du problème OU
            # - Assigné à au moins une action du problème
            user = self.request.user
            is_responsable_role = str(getattr(user, 'role', '')).upper().startswith('RESPONSABLE')
            if is_responsable_role:
                is_member = problem.members.filter(id=user.id).exists()
                is_assigned_on_problem = problem.actions.filter(assigned_to_id=user.id).exists()
                if not (is_member or is_assigned_on_problem):
                    from rest_framework.exceptions import PermissionDenied
                    raise PermissionDenied("Accès refusé: vous devez être impliqué dans ce problème (membre ou assigné à une action).")
        action = serializer.save()
        # Notify assigned user immediately
        if action.assigned_to:
            Notification.objects.create(
                recipient=action.assigned_to,
                message=f"Nouvelle action {action.get_action_type_display().lower()} assignée: {action.description}",
                problem=action.problem
            )
        
        # Notify Manager if Preventive Action (D7) is created
        if action.action_type == 'PREVENTIVE':
            managers = get_user_model().objects.filter(role='MANAGER', is_active=True)
            for m in managers:
                Notification.objects.create(
                    recipient=m,
                    message=f"Nouvelle action préventive proposée (D7): {action.description}",
                    problem=action.problem
                )

    def perform_update(self, serializer):
        obj = serializer.instance
        problem = getattr(obj, 'problem', None)
        old_status = obj.status
        if problem and str(getattr(self.request.user, 'role', '')).upper().startswith('RESPONSABLE'):
            # Autoriser le Responsable à mettre à jour si:
            # - il est l'assigné de cette action, OU
            # - il est membre du problème, OU
            # - il est assigné à au moins une action du même problème (ex: actions correctives précédentes)
            is_assigned_user = (obj.assigned_to_id == self.request.user.id)
            is_problem_member = problem.members.filter(id=self.request.user.id).exists()
            is_assigned_on_problem = problem.actions.filter(assigned_to_id=self.request.user.id).exists()
            if not (is_assigned_user or is_problem_member or is_assigned_on_problem):
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("Accès refusé: vous devez être impliqué (assigné/membre) dans ce problème.")
        updated = serializer.save()
        # Notify manager when corrective action is verified
        if old_status != updated.status and updated.status == 'VERIFIED' and updated.action_type == 'CORRECTIVE':
            managers = get_user_model().objects.filter(role='MANAGER', is_active=True)
            for m in managers:
                Notification.objects.create(
                    recipient=m,
                    message=f"Action corrective vérifiée: {updated.description}",
                    problem=updated.problem
                )
            
            # Check if all corrective actions are verified to advance Step to D7 (completing D6)
            if updated.problem:
                corrective_actions = updated.problem.actions.filter(action_type='CORRECTIVE')
                if corrective_actions.exists() and not corrective_actions.exclude(status='VERIFIED').exists():
                    # All corrective actions are verified
                    # Only advance if we are currently at D6
                    if updated.problem.current_step == 'D6':
                        updated.problem.current_step = 'D7'
                        updated.problem.save()
                        # Notify Manager that D6 is complete
                        for m in managers:
                            Notification.objects.create(
                                recipient=m,
                                message=f"Toutes les actions correctives sont vérifiées. Problème passé à l'étape D7: {updated.problem.title}",
                                problem=updated.problem
                            )

class RootCauseViewSet(viewsets.ModelViewSet):
    queryset = RootCause.objects.all()
    serializer_class = RootCauseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        problem_id = self.request.data.get('problem')
        if problem_id:
            try:
                problem = Problem.objects.get(id=problem_id)
            except Problem.DoesNotExist:
                return super().perform_create(serializer)
            if str(getattr(self.request.user, 'role', '')).upper().startswith('RESPONSABLE') and not problem.members.filter(id=self.request.user.id).exists():
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("Accès refusé: ce problème n'est pas assigné à vous.")
        serializer.save()

    def perform_update(self, serializer):
        obj = serializer.instance
        problem = getattr(obj, 'problem', None)
        if problem and str(getattr(self.request.user, 'role', '')).upper().startswith('RESPONSABLE'):
            if not problem.members.filter(id=self.request.user.id).exists():
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("Accès refusé: ce problème n'est pas assigné à vous.")
        serializer.save()
class ProblemAttachmentViewSet(viewsets.ModelViewSet):
    queryset = ProblemAttachment.objects.all()
    serializer_class = ProblemAttachmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        # Ensure problem is linked if passed in data
        serializer.save()

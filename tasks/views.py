from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Task
from .serializers import TaskSerializer
from .utils import TaskUtils

class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer

    @action(detail=False, methods=['get'])
    def prioritized(self, request):
        """Get tasks sorted by priority score"""
        tasks = self.get_queryset()
        serializer = self.get_serializer(tasks, many=True)
        sorted_tasks = TaskUtils.sort_tasks_by_priority(serializer.data)
        return Response(sorted_tasks)

    @action(detail=False, methods=['get'])
    def overdue(self, request):
        """Get overdue tasks"""
        tasks = self.get_queryset()
        serializer = self.get_serializer(tasks, many=True)
        overdue_tasks = TaskUtils.get_overdue_tasks(serializer.data)
        return Response(overdue_tasks)

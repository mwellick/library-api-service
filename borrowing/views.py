from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from .serializers import (
    BorrowingSerializer,
    BorrowingListSerializer,
    BorrowingRetrieveSerializer
)
from .models import Borrowing


class BorrowingViewSet(ModelViewSet):
    queryset = Borrowing.objects.all()
    serializer_class = BorrowingSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        queryset = self.queryset
        if not self.request.user.is_superuser:
            queryset = self.queryset.filter(user=self.request.user)
        if self.action in ("list", "retrieve"):
            return queryset.select_related("book", "user")
        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return BorrowingListSerializer
        elif self.action == "retrieve":
            return BorrowingRetrieveSerializer
        return BorrowingSerializer

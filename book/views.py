from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import (
    IsAuthenticated,
    IsAdminUser,
    AllowAny
)
from drf_spectacular.utils import (
    extend_schema_view,
    extend_schema
)
from .models import Book
from .serializers import (
    BookSerializer,
    BookListSerializer,
    BookRetrieveSerializer
)


@extend_schema_view(
    create=extend_schema(
        summary="Add a book",
        description="Admin can add a book"
    ),
    retrieve=extend_schema(
        summary="Get a detailed info about specific book",
        description="Admin and authenticated user can get a detailed info about book",
    ),
    update=extend_schema(
        summary="Update info about specific book",
        description="Admin can update information about specific book",
    ),
    partial_update=extend_schema(
        summary="Partial update of specific book",
        description="Admin can make a partial update of specific book",
    ),
    destroy=extend_schema(
        summary="Delete a book",
        description="Admin can delete book from book inventory",
    ),
)
class BookViewSet(ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            permission_classes = [IsAdminUser]
        elif self.action == "list":
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        if self.action in ["create", "update", "retrieve", "partial_update", "destroy"]:
            return BookRetrieveSerializer
        elif self.action == "list":
            return BookListSerializer
        return BookSerializer

    @extend_schema(
        methods=["GET"],
        summary="Get list of all books",
        description="Everyone can get a list of all available books",

    )
    def list(self, request, *args, **kwargs):
        return super().list(request,*args,**kwargs)
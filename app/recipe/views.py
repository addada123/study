from django.shortcuts import render
from drf_spectacular.utils import (
    extend_schema_view,
    extend_schema,
    OpenApiParameter,
    OpenApiTypes,
)
from rest_framework import (viewsets,
                            mixins,
                            status)

from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.pagination import LimitOffsetPagination

from core.models import (
    Recipe,
    Tag,
    Ingredient,
    Like
)
from recipe import serializers


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                'assigned_only',
                OpenApiTypes.INT, enum=[0, 1],
                description='Filter by items assigned to recipes.',
            ),
            OpenApiParameter(
                'limit',
                OpenApiTypes.INT,
                description='Number of items per page.',
                required=False
            ),
            OpenApiParameter(
                'offset',
                OpenApiTypes.INT,
                description='Starting index for pagination.',
                required=False
            ),
        ]
    )
)
class BaseRecipeAttrViewSet(mixins.DestroyModelMixin,
                            mixins.UpdateModelMixin,
                            mixins.ListModelMixin,
                            viewsets.GenericViewSet
                            ):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    pagination_class = LimitOffsetPagination


    def get_queryset(self):
        assigned_only = bool(
            int(self.request.query_params.get('assigned_only', 0))
        )
        queryset = self.queryset
        if assigned_only:
            queryset = queryset.filter(recipe__isnull=False)

        queryset =  queryset.filter(
            user=self.request.user
        ).order_by('-name').distinct()
        return queryset

@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                'title',
                OpenApiTypes.STR,
                description='Query by name',
                required=False,
            ),
            OpenApiParameter(
                'created_at',
                OpenApiTypes.DATETIME,
                description='Filter by creation date',
                required=False,
            ),
            OpenApiParameter(
                'tags',
                OpenApiTypes.STR,
                description='Comma separated list of tag IDs to filter',
            ),
            OpenApiParameter(
                'ingredients',
                OpenApiTypes.STR,
                description='Comma separated list of ingredient IDs to filter',
            ),
            OpenApiParameter(
                'limit',
                OpenApiTypes.INT,
                description='Number of items per page.',
                required=False
            ),
            OpenApiParameter(
                'offset',
                OpenApiTypes.INT,
                description='Starting index for pagination.',
                required=False
            ),
        ]
    )
)
class RecipeViewSet(viewsets.ModelViewSet):
    """View for manage recipe APIs."""
    serializer_class = serializers.RecipeDetailSerializer
    queryset = Recipe.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticatedOrReadOnly]

    def _params_to_ints(self, qs):
        return [int(str_id) for str_id in qs.split(',')]

    def get_queryset(self):
        tags = self.request.query_params.get('tags')
        ingredients = self.request.query_params.get('ingredients')
        created_at = self.request.query_params.get('created_at')
        likes_count = self.request.query_params.get('likes_count')
        title = self.request.query_params.get('title')

        queryset = self.queryset
        if tags:
            tag_ids = self._params_to_ints(tags)
            queryset = queryset.filter(tags__id__in=tag_ids)
        if ingredients:
            ingredient_ids = self._params_to_ints(ingredients)
            queryset = queryset.filter(ingredients__id__in=ingredient_ids)
        if created_at:
            queryset = queryset.filter(created_at=created_at)
        if likes_count:
            queryset = queryset.filter(likes_count=likes_count)
        if title:
            queryset = queryset.filter(title__icontains=title)

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return serializers.RecipeSerializer
        elif self.action == 'upload_image':
            return serializers.RecipeImageSerializer
        return self.serializer_class

    def perform_create(self, serializer):
        recipe = serializer.save(user=self.request.user)
        return recipe

    def upload_image(self, request, pk=None):
        recipe = self.get_object()
        serializer = self.get_serializer(recipe, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TagViewSet(BaseRecipeAttrViewSet):
    serializer_class = serializers.TagSerializer
    queryset = Tag.objects.all()


class IngredientViewSet(BaseRecipeAttrViewSet):
    serializer_class = serializers.IngredientSerializer
    queryset = Ingredient.objects.all()

class LikeViewSet(mixins.CreateModelMixin,
                  mixins.DestroyModelMixin,
                  viewsets.GenericViewSet
):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.LikeSerializer
    queryset = Like.objects.all()

    def create(self, request, *args, **kwargs):
        recipe_id = request.data.get('recipe')
        try:
            recipe = Recipe.objects.get(id=recipe_id)
        except Recipe.DoesNotExist:
            return Response({'error': 'Recipe not found'}, status=status.HTTP_404_NOT_FOUND)

        user = request.user  # Get the currently authenticated user
        like, created = Like.objects.get_or_create(recipe=recipe, user=user)
        if created:
            recipe.likes_count.add(like)
            recipe.save()
            return Response({'message': 'Recipe liked successfully'}, status=status.HTTP_201_CREATED)
        else:
            return Response({'error': 'You have already liked this recipe'}, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        recipe_id = kwargs['pk']
        try:
            recipe = Recipe.objects.get(id=recipe_id)
        except Recipe.DoesNotExist:
            return Response({'error': 'Recipe not found'}, status=status.HTTP_404_NOT_FOUND)

        user = request.user

        try:
            like = Like.objects.get(recipe=recipe, user=user)
            if like is not None:
                recipe.likes_count.remove(like)  # Remove the like from the recipe's likes_count relationship
                like.delete()  # Delete the like object
                return Response({'message': 'Recipe like removed successfully'}, status=status.HTTP_200_OK)
            else:
                # If the like already existed
                return Response({'error': 'You have not liked this recipe'}, status=status.HTTP_400_BAD_REQUEST)
        except Like.DoesNotExist:
            return Response({'error': 'You have not liked this recipe'}, status=status.HTTP_400_BAD_REQUEST)


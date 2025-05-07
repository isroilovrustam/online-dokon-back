from rest_framework.generics import ListAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from shop.models import Shop
from .serializers import ShopCheckSerializer, ShopSerializer


class ShopListAPIView(ListAPIView):
    queryset = Shop.objects.all()
    serializer_class = ShopSerializer


class ShopDetailAPIView(generics.RetrieveAPIView):
    queryset = Shop.objects.all()
    serializer_class = ShopSerializer
    lookup_field = 'shop_code'


class ShopByCodeCheckAPIView(APIView):
    def get(self, request, shop_code, *args, **kwargs):
        try:
            shop = Shop.objects.get(shop_code=shop_code)
            if shop.is_active:
                serializer = ShopCheckSerializer(shop)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response({"detail": "Do'kon aktiv emas."}, status=status.HTTP_400_BAD_REQUEST)
        except Shop.DoesNotExist:
            return Response({"detail": "Do'kon topilmadi."}, status=status.HTTP_404_NOT_FOUND)


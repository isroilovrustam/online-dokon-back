from rest_framework.generics import ListAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from shop.models import Shop, ShopAddress
from .serializers import ShopCheckSerializer, ShopSerializer, ShopGetSerializer, ShopGetAddressSerializer


#
class ShopListAPIView(ListAPIView):
    queryset = Shop.objects.all()
    serializer_class = ShopGetAddressSerializer


class ShopAddressDeleteAPIView(APIView):
    def delete(self, request, pk):
        try:
            address = ShopAddress.objects.get(pk=pk, shop__owner=request.user)
            address.delete()
            return Response({"detail": "Manzil muvaffaqiyatli o'chirildi."}, status=status.HTTP_204_NO_CONTENT)
        except ShopAddress.DoesNotExist:
            return Response({"detail": "Bunday manzil topilmadi."}, status=status.HTTP_404_NOT_FOUND)


class ShopDetailAPIView(generics.RetrieveUpdateAPIView):
    queryset = Shop.objects.all()
    lookup_field = 'shop_code'
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return ShopGetSerializer
        return ShopSerializer

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        data = request.data.copy()
        addresses_data = data.pop('addresses', None)

        serializer = self.get_serializer(instance, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # Manzillarni alohida qo‘shamiz (o‘chirmaymiz, faqat yangilarini qo‘shamiz)
        if addresses_data:
            for address in addresses_data:
                ShopAddress.objects.create(shop=instance, **address)

        return Response(self.get_serializer(instance).data, status=status.HTTP_200_OK)


# class ShopByCodeCheckAPIView(APIView):
#     def get(self, request, shop_code, *args, **kwargs):
#         try:
#             shop = Shop.objects.get(shop_code=shop_code)
#             if shop.is_active:
#                 serializer = ShopCheckSerializer(shop)
#                 return Response(serializer.data, status=status.HTTP_200_OK)
#             else:
#                 return Response({"detail": "Do'kon aktiv emas."}, status=status.HTTP_400_BAD_REQUEST)
#         except Shop.DoesNotExist:
#             return Response({"detail": "Do'kon topilmadi."}, status=status.HTTP_404_NOT_FOUND)

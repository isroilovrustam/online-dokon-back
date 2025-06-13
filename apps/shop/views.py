from rest_framework.generics import ListAPIView, CreateAPIView, UpdateAPIView, DestroyAPIView, \
    RetrieveUpdateDestroyAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from shop.models import Shop, ShopAddress, Basket
from .serializers import ShopCheckSerializer, ShopSerializer, ShopGetSerializer, BasketSerializer, BasketGetSerializer, \
    BasketPathSerializer
from django.db import transaction


class BasketCreateView(CreateAPIView, ):
    queryset = Basket.objects.all()
    serializer_class = BasketSerializer


class BasketListView(ListAPIView):
    serializer_class = BasketGetSerializer

    def get_queryset(self):
        return Basket.objects.filter(user__telegram_id=self.kwargs['telegram_id'],
                                     shop__shop_code=self.kwargs['shop_code'])


class BasketUpdateView(RetrieveUpdateDestroyAPIView):
    queryset = Basket.objects.all()
    serializer_class = BasketPathSerializer
    lookup_field = 'id'  # modeldagi field nomi
    lookup_url_kwarg = 'basket_id'  # URLdagi nom

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        new_quantity = request.data.get('quantity')

        if new_quantity is not None and int(new_quantity) == 0:
            instance.delete()
            return Response({"detail": "Mahsulot savatchadan o‘chirildi."}, status=status.HTTP_204_NO_CONTENT)

        return super().update(request, *args, **kwargs)


class ShopListAPIView(ListAPIView):
    serializer_class = ShopGetSerializer
    queryset = Shop.objects.all()


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

    @transaction.atomic
    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        data = request.data.copy()
        addresses_data = data.pop('addresses', None)

        serializer = self.get_serializer(instance, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # Manzillarni alohida boshqaramiz (mavjudini yangilaymiz, yangi bo‘lsa yaratamiz)
        if addresses_data:
            for address_data in addresses_data:
                address_id = address_data.get('id')
                if address_id:
                    # Agar ID bor bo‘lsa, mavjud manzilni yangilaymiz
                    try:
                        address = ShopAddress.objects.get(id=address_id, shop=instance)
                        for attr, value in address_data.items():
                            setattr(address, attr, value)
                        address.save()
                    except ShopAddress.DoesNotExist:
                        continue  # noto‘g‘ri ID kelsa, tashlab ketamiz
                else:
                    # ID bo‘lmasa – yangi manzil yaratamiz
                    ShopAddress.objects.create(shop=instance, **address_data)

        return Response(self.get_serializer(instance).data, status=status.HTTP_200_OK)


class ShopByCodeCheckAPIView(APIView):
    def get(self, request, shop_code, *args, **kwargs):
        shop = Shop.objects.filter(shop_code=shop_code).first()
        if shop is None:
            return Response({"detail": "Do'kon topilmadi."}, status=status.HTTP_404_NOT_FOUND)

        if not shop.is_active:
            return Response({"detail": "Do'kon aktiv emas."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = ShopCheckSerializer(shop)
        return Response(serializer.data, status=status.HTTP_200_OK)

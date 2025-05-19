from django.db.models import Q
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny

from botuser.models import BotUser
from rest_framework.generics import ListAPIView, RetrieveAPIView, CreateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
import requests
from config import settings
from .models import Product, ProductColor, ProductTaste, ProductVolume, ProductSize, ProductCategory, ProductVariant
from .serializers import ProductSerializer, ProductSizeSerializer, ProductVolumeSerializer, ProductColorSerializer, \
    ProductTasteSerializer, ProductCategorySerializer, ProductGetSerializer, ProductVariantSerializer
from shop.models import Basket
from botuser.models import FavoriteProduct, UserAddress, Order, OrderItem
from django.shortcuts import get_object_or_404


class ProductCategoryCreateAPIView(CreateAPIView):
    queryset = ProductCategory.objects.all()
    serializer_class = ProductCategorySerializer


class ProductColorCreateAPIView(CreateAPIView):
    queryset = ProductColor.objects.all()
    serializer_class = ProductColorSerializer


class ProductSizeCreateAPIView(CreateAPIView):
    queryset = ProductSize.objects.all()
    serializer_class = ProductSizeSerializer


class ProductTasteCreateAPIView(CreateAPIView):
    queryset = ProductTaste.objects.all()
    serializer_class = ProductTasteSerializer


class ProductVolumeCreateAPIView(CreateAPIView):
    queryset = ProductVolume.objects.all()
    serializer_class = ProductVolumeSerializer


class ProductVolumeListAPIView(ListAPIView):
    serializer_class = ProductVolumeSerializer

    def get_queryset(self):
        return ProductVolume.objects.filter(shop__shop_code=self.kwargs['shop_code'])

    lookup_url_kwarg = 'shop_code'


class ShopSizeListAPIView(ListAPIView):
    serializer_class = ProductSizeSerializer

    def get_queryset(self):
        return ProductSize.objects.filter(shop__shop_code=self.kwargs['shop_code'])

    lookup_url_kwarg = 'shop_code'


class ProductSizeListAPIView(ListAPIView):
    serializer_class = ProductSizeSerializer
    queryset = ProductSize.objects.all()

    def get(self, request, *args, **kwargs):
        ls = list()
        color_id = self.request.GET.get('color_id')
        qs = ProductVariant.objects.filter(product_id=self.kwargs['product_id']).select_related('size').distinct(
            'size')
        if color_id:
            qs = qs.filter(color_id=color_id)
        for q in qs:
            ls.append(ProductSizeSerializer(q.size).data)
        return Response(ls)

    lookup_url_kwarg = 'product_id'


class ShopColorListAPIView(ListAPIView):
    serializer_class = ProductColorSerializer

    def get_queryset(self):
        return ProductColor.objects.filter(shop__shop_code=self.kwargs['shop_code'])

    lookup_url_kwarg = 'shop_code'


class ProductColorListAPIView(ListAPIView):
    serializer_class = ProductColorSerializer
    queryset = ProductColor.objects.all()

    def get(self, request, *args, **kwargs):
        ls = list()
        qs = ProductVariant.objects.filter(product_id=self.kwargs['product_id']).select_related('color').distinct(
            'color')
        for q in qs:
            ls.append(ProductColorSerializer(q.color).data)
        return Response(ls)

    lookup_url_kwarg = 'product_id'


class ProductTasteListAPIView(ListAPIView):
    serializer_class = ProductTasteSerializer

    def get_queryset(self):
        return ProductTaste.objects.filter(shop__shop_code=self.kwargs['shop_code'])

    lookup_url_kwarg = 'shop_code'


class ProductCategoryListAPIView(ListAPIView):
    serializer_class = ProductCategorySerializer

    def get_queryset(self):
        return ProductCategory.objects.filter(shop__shop_code=self.kwargs['shop_code'])

    lookup_url_kwarg = 'shop_code'


class ProductListAPIView(ListAPIView):
    serializer_class = ProductGetSerializer

    def get_queryset(self):
        shop_code = self.kwargs.get('shop_code')  # ✅ To‘g‘ri nom
        qs = Product.objects.filter(shop__shop_code=shop_code, shop__is_active=True).order_by('-created_at')
        name = self.request.GET.get('name')
        cat = self.request.GET.get('cat')
        if cat:
            qs = qs.filter(category_id=cat)
        if name:
            qs = qs.filter(Q(product_name_uz__icontains=name) | Q(product_name_ru__icontains=name))
        return qs


class ProductCreateAPIView(CreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


class ProductDetailView(RetrieveAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductGetSerializer
    lookup_field = 'pk'


class CreateBasketAPIView(APIView):
    def post(self, request, *args, **kwargs):
        telegram_id = request.data.get('telegram_id')
        product_variant_id = request.data.get('product_variant_id')
        quantity = request.data.get('quantity', 1)

        try:
            quantity = int(quantity)
            if quantity <= 0:
                raise ValueError
        except (ValueError, TypeError):
            return Response({"detail": "Quantity must be a positive integer."}, status=status.HTTP_400_BAD_REQUEST)

        if not product_variant_id:
            return Response({"detail": "Product ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            product_variant = ProductVariant.objects.get(pk=product_variant_id, product__shop__is_active=True)
        except ProductVariant.DoesNotExist:
            return Response({"detail": "Product not found or inactive."}, status=status.HTTP_404_NOT_FOUND)

        try:
            user = BotUser.objects.get(telegram_id=telegram_id)
        except BotUser.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        # basket_item, created = Basket.objects.get_or_create(
        #     user=user,
        #     product_variant=product_variant,
        #     shop=product_variant.product.shop,
        #     defaults={'quantity': quantity}
        # )
        #
        # if not created:
        #     basket_item.quantity += quantity
        #     basket_item.save()

        baskets = Basket.objects.filter(user=user, product_variant=product_variant)

        if baskets.exists():
            basket = baskets.first()
            if int(quantity) == 0:
                basket.delete()
            else:
                basket.quantity = quantity
                basket.save()
        else:
            basket = Basket.objects.create(
                product_variant=product_variant,
                user=user,
                quantity=quantity
            )

        return Response({"basket_count": basket.quantity})

        # return Response({"basket_id": basket_item.id}, status=status.HTTP_201_CREATED)


class BasketListAPIView(ListAPIView):
    serializer_class = ProductVariantSerializer
    queryset = Basket.objects.all()

    def get(self, request, shop_code, telegram_id):
        if not shop_code and not telegram_id:
            return Response("gg")
        print(shop_code, telegram_id)
        qs = Basket.objects.filter(shop__shop_code=shop_code, user__telegram_id=telegram_id).select_related(
            'product_variant')
        ls = list()
        for b in qs:
            print(ls)
            ls.append(ProductVariantSerializer(b.product_variant).data)
        return Response(ls, status=status.HTTP_200_OK)


class DeleteBasketAPIView(APIView):
    def delete(self, request, *args, **kwargs):
        try:
            basket_item = Basket.objects.get(id=self.kwargs['pk'])
            basket_item.delete()
        except Basket.DoesNotExist:
            return Response({"detail": "Basket item not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response({"detail": "Basket item deleted."}, status=status.HTTP_204_NO_CONTENT)


class FavoriteProductAPIView(APIView):
    def post(self, request, *args, **kwargs):
        product_id = request.data.get('product_id')
        telegram_id = request.data.get('telegram_id')

        if not product_id:
            return Response({"detail": "Product ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        if not telegram_id:
            return Response({"detail": "Telegram ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            product = Product.objects.get(pk=product_id)
        except Product.DoesNotExist:
            return Response({"detail": "Product not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            user = BotUser.objects.get(telegram_id=telegram_id)
        except BotUser.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        favorite, created = FavoriteProduct.objects.get_or_create(user=user, product=product)

        if created:
            return Response({"detail": "Product added to favorites."}, status=status.HTTP_201_CREATED)

        return Response({"detail": "Product is already in favorites."}, status=status.HTTP_200_OK)


class FavoriteListAPIView(ListAPIView):
    serializer_class = ProductGetSerializer
    queryset = FavoriteProduct.objects.all()

    def get(self, request, shop_code, telegram_id):
        qs = FavoriteProduct.objects.filter(user__telegram_id=telegram_id, shop__shop_code=shop_code).select_related(
            'product')
        ls = list()
        for i in qs:
            ls.append(ProductGetSerializer(i.product).data)
        return Response(ls, status=status.HTTP_200_OK)


class FavoriteProductDeleteAPIView(APIView):
    def delete(self, request, *args, **kwargs):
        try:
            favorite = FavoriteProduct.objects.get(id=self.kwargs['pk'])
            favorite.delete()
            return Response({"detail": "Product removed from favorites."}, status=status.HTTP_204_NO_CONTENT)
        except FavoriteProduct.DoesNotExist:
            return Response({"detail": "Product not found in favorites."}, status=status.HTTP_404_NOT_FOUND)


def send_telegram_order_message(shop, order):
    bot_token = settings.BOT_B_TOKEN
    chat_id = shop.telegram_group  # shop orqali aniqlaysiz

    text = (
        f"🛍 Yangi buyurtma!\n"
        f"📦 Buyurtma ID: {order.id}\n"
        f"👤 Foydalanuvchi: {order.user.full_name} ({order.user.phone_number})\n"
        f"📍 Manzil: {order.address.address}\n"
        f"💰 Umumiy summa: {order.total_price} so'm\n\n"
        f"🧾 Buyurtma tarkibi:\n"
    )

    for item in order.items.all():
        text += f" - {item.product.name} x {item.quantity} = {item.price} so'm\n"

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text
    }

    requests.post(url, data=payload)


class CreateOrderAPIView(APIView):
    """
    Create an order with the given items and address.
    Request body should contain:
    {
        "items": [
            {"product_id": 1, "quantity": 2},
            {"product_id": 2, "quantity": 1}
        ],
        "address_id": 1,
        "telegram_id": 1
    }
    """

    def post(self, request, *args, **kwargs):
        user = request.data.get('telegram_id')
        items = request.data.get('items')  # List of items with product_id and quantity
        address_id = request.data.get('address_id')

        if not items or not isinstance(items, list):
            return Response({"detail": "Items are required and must be a list."}, status=status.HTTP_400_BAD_REQUEST)

        if not address_id:
            return Response({"detail": "Address ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            address = UserAddress.objects.get(pk=address_id, user=user)
        except UserAddress.DoesNotExist:
            return Response({"detail": "Address not found."}, status=status.HTTP_404_NOT_FOUND)
        try:
            user = BotUser.objects.get(telegram_id=user)
        except BotUser.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        order = Order.objects.create(user=user, address=address, total_price=0)
        shop = None
        total_price = 0
        for item in items:
            product_id = item.get('product_id')
            quantity = item.get('quantity', 1)

            if not product_id or not isinstance(quantity, int) or quantity <= 0:
                return Response({"detail": "Each item must have a valid product_id and quantity."},
                                status=status.HTTP_400_BAD_REQUEST)

            try:
                product = Product.objects.get(pk=product_id, shop__is_active=True)
                shop = product.shop
            except Product.DoesNotExist:
                return Response({"detail": f"Product with ID {product_id} not found or inactive."},
                                status=status.HTTP_404_NOT_FOUND)

            order_item = OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                price=product.price * quantity
            )
            total_price += order_item.price

        order.total_price = total_price
        order.save()

        # ✅ TELEGRAM XABAR YUBORILADI:
        try:
            send_telegram_order_message(shop, order)
        except Exception as e:
            print(f"Telegramga xabar yuborishda xatolik: {e}")

        return Response({"order_id": order.id, "total_price": order.total_price}, status=status.HTTP_201_CREATED)

from rest_framework import status
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
import requests
from config import settings
from .models import Product
from .serializers import ProductSerializer
from shop.models import Basket
from botuser.models import FavoriteProduct, UserAddress, Order, OrderItem


class ProductListAPIView(ListAPIView):
    serializer_class = ProductSerializer

    def get_queryset(self):
        shop_code = self.kwargs.get('shop_code')  # ✅ To‘g‘ri nom
        return Product.objects.filter(shop__shop_code=shop_code, shop__is_active=True)


class ProductDetailView(RetrieveAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    lookup_field = 'pk'


class CreateBasketAPIView(APIView):
    def post(self, request, *args, **kwargs):
        user = request.user
        product_id = request.data.get('product_id')
        quantity = request.data.get('quantity', 1)

        if not product_id:
            return Response({"detail": "Product ID is required."}, status=status.HTTP_400_BAD_REQUEST)
        if not isinstance(quantity, int) or quantity <= 0:
            return Response({"detail": "Quantity must be a positive integer."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            product = Product.objects.get(pk=product_id, shop__is_active=True)
        except Exception as e:
            return Response({"detail": "Product not found or inactive.", "error": e}, status=status.HTTP_404_NOT_FOUND)

        basket_item, created = Basket.objects.get_or_create(
            user_id=user.id,
            product=product,
            shop=product.shop,
            defaults={'quantity': quantity}
        )
        if not created:
            basket_item.quantity += quantity
            basket_item.save()

        return Response({"basket_id": basket_item.id}, status=status.HTTP_201_CREATED)


class DeleteBasketAPIView(APIView):
    def post(self, request, *args, **kwargs):
        user = request.user
        basket_id = request.data.get('basket_id')
        quantity = 1

        if not basket_id:
            return Response({"detail": "Basket ID is required."}, status=status.HTTP_400_BAD_REQUEST)
        if not isinstance(quantity, int) or quantity <= 0:
            return Response({"detail": "Quantity must be a positive integer."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            basket_item = Basket.objects.get(pk=basket_id, user=user)
        except Basket.DoesNotExist:
            return Response({"detail": "Basket item not found."}, status=status.HTTP_404_NOT_FOUND)

        if basket_item.quantity > quantity:
            basket_item.quantity -= quantity
            basket_item.save()
        else:
            basket_item.delete()
        return Response({"detail": "Basket item deleted."}, status=status.HTTP_204_NO_CONTENT)


class FavoriteProductAPIView(APIView):

    def post(self, request, *args, **kwargs):
        user = request.user
        product_id = request.data.get('product_id')

        if not product_id:
            return Response({"detail": "Product ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            product = Product.objects.get(pk=product_id)
        except Product.DoesNotExist:
            return Response({"detail": "Product not found."}, status=status.HTTP_404_NOT_FOUND)

        favorite, created = FavoriteProduct.objects.get_or_create(user=user, product=product)
        if created:
            return Response({"detail": "Product added to favorites."}, status=status.HTTP_201_CREATED)
        return Response({"detail": "Product is already in favorites."}, status=status.HTTP_200_OK)

    def delete(self, request, *args, **kwargs):
        user = request.user
        product_id = request.data.get('product_id')

        if not product_id:
            return Response({"detail": "Product ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            favorite = FavoriteProduct.objects.get(user=user, product_id=product_id)
            favorite.delete()
            return Response({"detail": "Product removed from favorites."}, status=status.HTTP_204_NO_CONTENT)
        except FavoriteProduct.DoesNotExist:
            return Response({"detail": "Product not found in favorites."}, status=status.HTTP_404_NOT_FOUND)


def send_telegram_order_message(order):
    bot_token = settings.BOT_B_TOKEN
    chat_id = order.shop.telegram_group  # shop orqali aniqlaysiz

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
        "address_id": 1
    }
    """

    def post(self, request, *args, **kwargs):
        user = request.user
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

        order = Order.objects.create(user=user, address=address, total_price=0)

        total_price = 0
        for item in items:
            product_id = item.get('product_id')
            quantity = item.get('quantity', 1)

            if not product_id or not isinstance(quantity, int) or quantity <= 0:
                return Response({"detail": "Each item must have a valid product_id and quantity."},
                                status=status.HTTP_400_BAD_REQUEST)

            try:
                product = Product.objects.get(pk=product_id, shop__is_active=True)
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
            send_telegram_order_message(order)
        except Exception as e:
            print(f"Telegramga xabar yuborishda xatolik: {e}")


        return Response({"order_id": order.id, "total_price": order.total_price}, status=status.HTTP_201_CREATED)

from django.db.models import Q
from rest_framework import status
from rest_framework.exceptions import ValidationError
import json
from urllib.parse import quote
from botuser.models import BotUser
from rest_framework.generics import ListAPIView, RetrieveAPIView, CreateAPIView, UpdateAPIView, DestroyAPIView, \
    RetrieveUpdateDestroyAPIView, get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView
import requests
from config.settings import BOT_B_TOKEN
from .models import Product, ProductColor, ProductTaste, ProductVolume, ProductSize, ProductCategory, ProductVariant, \
    ProductImage
from .serializers import ProductSerializer, ProductSizeSerializer, ProductVolumeSerializer, ProductColorSerializer, \
    ProductTasteSerializer, ProductCategorySerializer, ProductGetSerializer, ProductVariantSerializer, \
    ProductImageSerializer, ProductPatchSerializer, ProductVariantPostSerializer, OrderSerializer, \
    OrderStatusUpdateSerializer, ProductGetCategorySerializer, ProductCreateImageSerializer
from shop.models import Basket, Shop
from botuser.models import FavoriteProduct, UserAddress, Order, OrderItem


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
    serializer_class = ProductGetCategorySerializer

    def get_queryset(self):
        return ProductCategory.objects.filter(shop__shop_code=self.kwargs['shop_code'])

    lookup_url_kwarg = 'shop_code'


class ProductListAPIView(ListAPIView):
    serializer_class = ProductGetSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        telegram_id = self.request.query_params.get("telegram_id")
        if telegram_id:
            try:
                user = BotUser.objects.get(telegram_id=telegram_id)
                context['user'] = user
            except BotUser.DoesNotExist:
                context['user'] = None
        return context

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

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        telegram_id = self.request.query_params.get("telegram_id")
        user = BotUser.objects.filter(telegram_id=telegram_id).first() if telegram_id else None

        if user:
            for product_data in response.data:
                product_id = product_data['id']
                favorite = FavoriteProduct.objects.filter(user=user, product_id=product_id).first()
                product_data['favorite_id'] = favorite.id if favorite else None
        else:
            for product_data in response.data:
                product_data['favorite_id'] = None

        return Response(response.data, status=status.HTTP_200_OK)


from rest_framework.generics import CreateAPIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from decimal import Decimal, InvalidOperation
import logging

logger = logging.getLogger(__name__)


class ProductCreateAPIView(CreateAPIView):
    """
    Creates a new product with images and variants from FormData.

    Handles multipart form data with nested arrays for images and variants.
    Expected FormData structure:
    - Basic fields: shop, category, product_name_uz, etc.
    - Images: images[0][image], images[1][image], etc.
    - Variants: variants[0][color], variants[0][price], etc.
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def create(self, request, *args, **kwargs):
        """Handle product creation with images and variants from FormData"""
        try:
            with transaction.atomic():
                logger.info("=== Starting product creation ===")
                logger.info(f"Request data keys: {list(request.data.keys())}")
                logger.info(f"Request files keys: {list(request.FILES.keys())}")

                # Log all form data for debugging
                for key, value in request.data.items():
                    logger.info(f"Form data - {key}: {value}")

                # Create product with basic data
                product_data = self._extract_product_data(request.data)
                logger.info(f"Extracted product data: {product_data}")

                product_serializer = self.get_serializer(data=product_data)
                product_serializer.is_valid(raise_exception=True)
                product = product_serializer.save()

                logger.info(f"Product created with ID: {product.id}")

                # Handle images
                images_created = self._create_product_images(request, product)
                logger.info(f"Created {images_created} images")

                # Handle variants
                variants_created = self._create_product_variants(request.data, product)
                logger.info(f"Created {variants_created} variants")

                # Return success response with product details
                response_serializer = ProductSerializer(product)
                return Response({
                    'success': True,
                    'message': 'Product created successfully',
                    'product': response_serializer.data
                }, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Unexpected error during product creation: {str(e)}")
            return Response({
                'success': False,
                'error': 'An error occurred while creating the product',
                'details': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    def _extract_product_data(self, data):
        """Extract basic product fields from request data"""
        prepayment = data.get('prepayment_amount', '')

        # Convert prepayment to decimal if provided
        prepayment_decimal = None
        if prepayment and str(prepayment).strip():
            try:
                prepayment_decimal = Decimal(str(prepayment))
            except (InvalidOperation, ValueError):
                logger.warning(f"Invalid prepayment amount: {prepayment}")

        return {
            'shop': data.get('shop'),
            'category': self._get_int_or_none(data, 'category'),
            'product_name_uz': data.get('product_name_uz', ''),
            'product_name_ru': data.get('product_name_ru', ''),
            'description_uz': data.get('description_uz', ''),
            'description_ru': data.get('description_ru', ''),
            'prepayment_amount': prepayment_decimal
        }

    def _create_product_images(self, request, product):
        """Create product images from FormData files"""
        files = request.FILES
        image_index = 0
        images_created = 0

        # Look for files with pattern images[0][image], images[1][image], etc.
        while f'images[{image_index}][image]' in files:
            try:
                image_file = files[f'images[{image_index}][image]']
                ProductImage.objects.create(
                    product=product,
                    image=image_file
                )
                images_created += 1
                logger.info(f"Created image {image_index} for product {product.id}")
            except Exception as e:
                logger.error(f"Error creating image {image_index}: {str(e)}")

            image_index += 1

        return images_created

    def _create_product_variants(self, data, product):
        """Create product variants from FormData"""
        variant_index = 0
        variants_created = 0

        # Look for variant data with pattern variants[0][field], variants[1][field], etc.
        while f'variants[{variant_index}][price]' in data:
            try:
                variant_data = self._extract_variant_data(data, variant_index)
                logger.info(f"Extracted variant {variant_index} data: {variant_data}")

                # Create variant only if price is provided and valid
                if variant_data['price'] is not None:
                    ProductVariant.objects.create(product=product, **variant_data)
                    variants_created += 1
                    logger.info(f"Created variant {variant_index} for product {product.id}")
                else:
                    logger.warning(f"Skipping variant {variant_index} - no valid price")

            except Exception as e:
                logger.error(f"Error creating variant {variant_index}: {str(e)}")

            variant_index += 1

        return variants_created

    def _extract_variant_data(self, data, index):
        """Extract variant data for a specific index"""
        return {
            'color_id': self._get_int_or_none(data, f'variants[{index}][color]'),
            'size_id': self._get_int_or_none(data, f'variants[{index}][size]'),
            'volume_id': self._get_int_or_none(data, f'variants[{index}][volume]'),
            'taste_id': self._get_int_or_none(data, f'variants[{index}][taste]'),
            'price': self._get_decimal_or_none(data, f'variants[{index}][price]'),
            'discount_price': self._get_decimal_or_none(data, f'variants[{index}][discount_price]'),
            'discount_percent': self._get_int_or_none(data, f'variants[{index}][discount_percent]'),
            'stock': self._get_int_or_none(data, f'variants[{index}][stock]', default=0),
            'is_active': self._get_boolean(data, f'variants[{index}][is_active]', default=True)
        }

    def _get_int_or_none(self, data, key, default=None):
        """Safely convert form data to integer"""
        value = data.get(key)
        if value and str(value).strip():
            try:
                return int(value)
            except (ValueError, TypeError):
                logger.warning(f"Invalid integer value for {key}: {value}")
        return default

    def _get_decimal_or_none(self, data, key, default=None):
        """Safely convert form data to decimal"""
        value = data.get(key)
        if value and str(value).strip():
            try:
                return Decimal(str(value))
            except (InvalidOperation, ValueError, TypeError):
                logger.warning(f"Invalid decimal value for {key}: {value}")
        return default

    def _get_boolean(self, data, key, default=True):
        """Safely convert form data to boolean"""

        value = data.get(key, default)
        if isinstance(value, str):
            return value.lower() in ['true', '1', 'yes', 'on']
        return bool(value)


class ProductDetailView(RetrieveAPIView, UpdateAPIView, DestroyAPIView):
    queryset = Product.objects.all()
    lookup_field = 'pk'

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return ProductGetSerializer
        return ProductPatchSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        telegram_id = self.request.query_params.get('telegram_id')
        user = None
        if telegram_id:
            user = BotUser.objects.filter(telegram_id=telegram_id).first()

        context.update({
            'request': self.request,
            'telegram_id': telegram_id,
            'user': user  # serializer ichida get_quantity va get_me_favorite ishlashi uchun
        })
        return context


class CreateBasketAPIView(APIView):
    """
    Foydalanish:
    {
      "telegram_id": "123456789",
      "product_variant_id": 42,
      "quantity": 3
    }
    """

    def post(self, request, *args, **kwargs):
        telegram_id = request.data.get('telegram_id')
        product_variant_id = request.data.get('product_variant_id')
        quantity = request.data.get('quantity', 1)

        # 1. Tekshiruvlar
        try:
            quantity = int(quantity)
            if quantity <= 0:
                return Response({"detail": "Quantity must be a positive integer."}, status=400)
        except (ValueError, TypeError):
            return Response({"detail": "Quantity must be a valid integer."}, status=400)

        if not telegram_id or not product_variant_id:
            return Response({"detail": "telegram_id and product_variant_id are required."}, status=400)

        # 2. Variant va userni topamiz
        try:
            product_variant = ProductVariant.objects.get(pk=product_variant_id, product__shop__is_active=True)
        except ProductVariant.DoesNotExist:
            return Response({"detail": "Product not found or inactive."}, status=404)
        shop = product_variant.product.shop
        if not shop:
            return Response({"detail": "Product's shop is not defined."}, status=400)

        try:
            user = BotUser.objects.get(telegram_id=telegram_id)
        except BotUser.DoesNotExist:
            return Response({"detail": "User not found."}, status=404)

        # 3. Basketni olish yoki yaratish
        basket, created = Basket.objects.get_or_create(
            user=user,
            product_variant=product_variant,
            shop=shop,  # <== SHOP ni qo‘shish kerak
            defaults={'quantity': quantity}
        )

        if not created:
            basket.quantity = quantity
            basket.save()

        return Response({
            "message": "Basket updated" if not created else "Basket created",
            "basket_quantity": basket.quantity
        }, status=200)


class UpdateBasketQuantityAPIView(APIView):
    """
    Foydalainsh:
    {
      "telegram_id": "123456789",
      "product_variant_id": 42,
      "action": "add"  // yoki "remove"
    }
    """

    def post(self, request, *args, **kwargs):
        telegram_id = request.data.get('telegram_id')
        product_variant_id = request.data.get('product_variant_id')
        action = request.data.get('action')  # "add" yoki "remove"

        if not all([telegram_id, product_variant_id, action]):
            return Response({"detail": "telegram_id, product_variant_id and action are required."}, status=400)

        if action not in ['add', 'remove']:
            return Response({"detail": "Invalid action. Use 'add' or 'remove'."}, status=400)

        try:
            product_variant = ProductVariant.objects.get(pk=product_variant_id, product__shop__is_active=True)
        except ProductVariant.DoesNotExist:
            return Response({"detail": "Product variant not found or inactive."}, status=404)

        try:
            user = BotUser.objects.get(telegram_id=telegram_id)
        except BotUser.DoesNotExist:
            return Response({"detail": "User not found."}, status=404)

        try:
            basket = Basket.objects.get(user=user, product_variant=product_variant)
        except Basket.DoesNotExist:
            if action == 'add':
                basket = Basket.objects.create(user=user, product_variant=product_variant, quantity=1)
                return Response({"quantity": basket.quantity, "message": "Item added to basket."}, status=200)
            else:
                return Response({"detail": "Item not in basket."}, status=404)

        # Update quantity
        if action == 'add':
            basket.quantity += 1
            basket.save()
            return Response({"quantity": basket.quantity, "message": "Item quantity increased."}, status=200)

        elif action == 'remove':
            if basket.quantity <= 1:
                basket.delete()
                return Response({"quantity": 0, "message": "Item removed from basket."}, status=200)
            else:
                basket.quantity -= 1
                basket.save()
                return Response({"quantity": basket.quantity, "message": "Item quantity decreased."}, status=200)


class BasketListAPIView(ListAPIView):
    """
    Foydalanish: GET /basket/{my-shop-code}/?telegram_id=123456789
    """
    serializer_class = ProductVariantSerializer
    queryset = Basket.objects.all()

    def get(self, request, shop_code):
        telegram_id = request.query_params.get('telegram_id')
        if not shop_code or not telegram_id:
            return Response({"detail": "shop_code and telegram_id are required."}, status=400)

        basket_items = Basket.objects.filter(
            shop__shop_code=shop_code,
            user__telegram_id=telegram_id
        ).select_related('product_variant', 'product_variant__product')

        product_variants = [b.product_variant for b in basket_items]

        serializer = self.serializer_class(product_variants, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


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
        qs = FavoriteProduct.objects.filter(
            user__telegram_id=telegram_id,
            product__shop__shop_code=shop_code
        ).select_related('product__shop')
        user = BotUser.objects.filter(telegram_id=telegram_id).first()

        ls = []
        for i in qs:
            serializer = ProductGetSerializer(i.product, context={'user': user, "request": request})
            data = serializer.data
            data['favorite_id'] = i.id  # ✅ qo‘shimcha qator
            ls.append(data)
        return Response(ls, status=status.HTTP_200_OK)


class FavoriteProductDeleteAPIView(APIView):
    def delete(self, request, *args, **kwargs):
        telegram_id = request.query_params.get('telegram_id')  # ✅ So‘rovdan olish

        if not telegram_id:
            return Response({"detail": "Telegram ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = BotUser.objects.get(telegram_id=telegram_id)
        except BotUser.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            favorite = FavoriteProduct.objects.get(id=self.kwargs['pk'], user=user)
            favorite.delete()
            return Response({"detail": "Product removed from favorites."}, status=status.HTTP_200_OK)
        except FavoriteProduct.DoesNotExist:
            return Response({"detail": "Product not found in favorites."}, status=status.HTTP_404_NOT_FOUND)


def send_telegram_order_message(shop, order):
    if not shop.telegram_group:
        print("Do'konning Telegram guruhi belgilanmagan.")
        return

    chat_id = shop.telegram_group
    lang = order.user.language  # 'uz' yoki 'ru'

    if lang == 'ru':
        text = f"""
🛒 <b>НОВЫЙ ПОРЯДОК!</b>
━━━━━━━━━━━━━━━

👤 <b>Покупатель:</b> {order.user.full_name}
🆔 <b>Юзернейм:</b> {order.user.telegram_username}
📍 <b>Адрес:</b> {order.address}
🔗 <a href='https://yandex.com/maps/?text={quote(order.address)}'>Посмотреть адрес на карте</a>
🧾 <b>Номер заказа:</b> <code>#{order.id}</code>
🕒 <b>Дата заказа:</b> {order.created_at.strftime('%Y-%m-%d %H:%M')}
💬 <b>Комментарий:</b> {order.comment}

━━━━━━━━━━━━━━━
🛍️ <b>ТОВАРЫ В ЗАКАЗЕ:</b>\n
"""
    else:
        text = f"""
🛒 <b>YANGI ZAKAZ!</b>
━━━━━━━━━━━━━━━

👤 <b>Buyurtmachi:</b> {order.user.full_name}
🆔 <b>Username:</b> {order.user.telegram_username}
📍 <b>Manzil:</b> {order.address}
🔗 <a href='https://yandex.com/maps/?text={quote(order.address)}'>Manzilni xaritada ko‘rish</a>
🧾 <b>Buyurtma raqami:</b> <code>#{order.id}</code>
🕒 <b>Buyurtma vaqti:</b> {order.created_at.strftime('%Y-%m-%d %H:%M')}
💬 <b>Izoh:</b> {order.comment}

━━━━━━━━━━━━━━━
🛍️ <b>BUYURTMADAGI MAHSULOTLAR:</b>\n
"""
    total_prepayment = 0  # Jami oldindan to'lovni yig'ish uchun
    for i, item in enumerate(order.items.all(), 1):
        product = item.product_variant.product
        prepayment = (product.prepayment_amount or 0) * item.quantity
        total_prepayment += prepayment

        if lang == 'ru':
            text += f"<code>#{i}️</code> <b>{product.product_name_ru}</b> x <b>{item.quantity}</b> <b>\nЦена:</b> {int(item.product_variant.price) * item.quantity}\n<b>Цвет:</b> {item.product_variant.color.color_ru}, <b>Размер:</b> {item.product_variant.size.size}\n"
        else:
            text += f"<code>#{i}️</code> <b>{product.product_name_uz}</b> x <b>{item.quantity}</b> <b>\nNarxi:</b> {int(item.product_variant.price) * item.quantity}\n<b>Rangi:</b> {item.product_variant.color.color_uz}  <b>Razmeri:</b> {item.product_variant.size.size}\n"
    if lang == 'uz':
        text += f"""\n
━━━━━━━━━━━━━━━
💵 <b>JAMI: {order.total_price:,} so'm</b>
Oldindan to'lov: {total_prepayment}
━━━━━━━━━━━━━━━

"""
    elif lang == 'ru':
        text += f"""\n
━━━━━━━━━━━━━━━
💵 <b>ИТОГО: {order.total_price:,} сум</b>
Предоплата: {total_prepayment}
━━━━━━━━━━━━━━━
"""

    url = f"https://api.telegram.org/bot{BOT_B_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }

    response = requests.post(url, json=payload)
    if response.status_code != 200:
        print("Telegram xabar yuborishda xatolik:", response.text)


def send_telegram_user_message(shop, order):
    user = order.user
    if not user.telegram_id:
        print("Foydalanuvchining Telegram ID si mavjud emas.")
        return

    chat_id = user.telegram_id
    lang = user.language  # 'uz' yoki 'ru'

    if lang == 'ru':
        text = f"""
🎉 <b>ЗАКАЗ УСПЕШНО ОФОРМЛЕН!</b>
━━━━━━━━━━━━━━━

🧾 <b>Номер заказа:</b> <code>#{order.id}</code>
👤 <b>Ф.И.О:</b> {order.user.full_name}
📍 <b>Адрес:</b> {order.address}
💵 <b>Общая сумма:</b> <b>{order.total_price} сум</b>
🕒 <b>Дата заказа:</b> {order.created_at.strftime('%Y-%m-%d %H:%M')}
💬 <b>Комментарий:</b> {order.comment}

━━━━━━━━━━━━━━━
🛍️ <b>ТОВАРЫ В ЗАКАЗЕ:</b>\n
"""
    else:
        text = f"""
🎉 <b>BUYURTMA MUVAFFAQIYATLI RASMIYLASHTRILDI!</b>
━━━━━━━━━━━━━━━

📋 <b>BUYURTMA TAFSILOTLARI:</b>
🧾 <b>Buyurtma raqami:</b> <code>#{order.id}</code>
👤 <b>F.I.O:</b> {order.user.full_name}
📍 <b>Manzil:</b> {order.address}
💵 <b>Umumiy narx:</b> <b>{order.total_price} so'm</b>
🕒 <b>Buyurtma vaqti:</b> {order.created_at.strftime('%Y-%m-%d %H:%M')}
💬 <b>Izoh:</b> {order.comment}

━━━━━━━━━━━━━━━
🛍️ <b>BUYURTMADAGI MAHSULOTLAR:</b>\n
"""
    total_prepayment = 0
    for i, item in enumerate(order.items.all(), 1):
        product = item.product_variant.product
        prepayment = (product.prepayment_amount or 0) * item.quantity
        total_prepayment += prepayment
        if lang == 'ru':
            text += f"<code>#{i}️</code> <b>{product.product_name_ru}</b> x <b>{item.quantity}</b> <b>\nЦена:</b> {int(item.product_variant.price) * item.quantity}\n<b>Цвет:</b> {item.product_variant.color.color_ru}, <b>Размер:</b> {item.product_variant.size.size}\n"
        else:
            text += f"<code>#{i}️</code> <b>{product.product_name_uz}</b> x <b>{item.quantity}</b> <b>\nNarxi:</b> {int(item.product_variant.price) * item.quantity}\n<b>Rangi:</b> {item.product_variant.color.color_uz}  <b>Razmeri:</b> {item.product_variant.size.size}\n"
    if total_prepayment and total_prepayment > 0:
        if lang == 'ru':
            text += (
                "\n⚠️ <b>ВНИМАНИЕ!</b>\n"
                f"🔒 <b>По этому заказу предусмотрена предоплата.</b>\n"
                f"💵 <b>Сумма предоплаты:</b> <b>{total_prepayment} сум</b>\n"
                "✅ <i>Заказ будет принят после подтверждения предоплаты.</i>\n"
            )
            button_text = "💳 Внести предоплату"
        else:
            text += (
                "\n⚠️ <b>DIQQAT!</b>\n"
                f"🔒 <b>Ushbu buyurtma uchun oldindan to‘lov mavjud.</b>\n"
                f"💵 <b>Oldindan to‘lov miqdori:</b> <b>{total_prepayment} so'm</b>\n"
                "✅ <i>Buyurtma to‘lov tasdiqlangandan so‘ng qabul qilinadi.</i>\n"
            )
            button_text = "💳 Oldindan to‘lov qilish"
    else:
        if lang == 'ru':
            text += (
                "\n📬 <b>Ваш заказ был отправлен в магазин!</b>\n"
                "💬 В ближайшее время мы сообщим, когда заказ будет принят.\n"
                "🤝 Спасибо, что вы с нами! 😊"
            )
            button_text = "💳 Внести предоплату"
        elif lang == 'uz':
            text += (
                "\n📬 <b>Buyurtmangiz do‘konga yuborildi!</b>\n"
                "💬 Tez orada buyurtmangiz qabul qilinganligi haqida sizga xabar beramiz.\n"
                "🤝 Biz bilan bo‘lganingiz uchun tashakkur! 😊"
            )
            button_text = "💳 Oldindan to‘lov qilish"

    reply_markup = {
        "inline_keyboard": [[
            {
                "text": button_text,
                "callback_data": f"to'lov:{order.id}",
            }
        ]]
    }

    url = f"https://api.telegram.org/bot{BOT_B_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "reply_markup": json.dumps(reply_markup)
    }

    response = requests.post(url, json=payload)
    if response.status_code != 200:
        print("Telegram xabar yuborishda xatolik:", response.text)


class CreateOrderAPIView(APIView):

    def post(self, request, *args, **kwargs):
        user = request.data.get('telegram_id')
        items = request.data.get('items')  # List of items with product_id and quantity
        address_id = request.data.get('address_id')
        comment = request.data.get('comment')
        total_price = request.data.get('total_price')
        if not items or not isinstance(items, list):
            return Response({"detail": "Items are required and must be a list."}, status=status.HTTP_400_BAD_REQUEST)

        if not address_id:
            return Response({"detail": "Address ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        if total_price is None:
            return Response({"detail": "total_price is required."}, status=status.HTTP_400_BAD_REQUEST)

        # total_price validatsiyasi
        try:
            total_price = float(total_price)
        except (TypeError, ValueError):
            return Response({"detail": "Total price must be a valid number."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            address = UserAddress.objects.get(pk=address_id, user=user)
        except UserAddress.DoesNotExist:
            return Response({"detail": "Address not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            user = BotUser.objects.get(telegram_id=user)
        except BotUser.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        order = Order.objects.create(user=user, address=address.full_address, comment=comment, total_price=0)
        shop = None
        for item in items:
            basket_id = item.get('basket_id')
            try:
                basket = Basket.objects.get(id=basket_id)
                shop = basket.product_variant.product.shop
            except Product.DoesNotExist:
                return Response({"detail": f"Basket with ID {basket_id} not found or inactive."},
                                status=status.HTTP_404_NOT_FOUND)

            OrderItem.objects.create(
                order=order,
                product_variant=basket.product_variant,
                quantity=basket.quantity,
            )
            # total_price += int(basket.product_variant.price) * basket.quantity
            basket.delete()
        order.total_price = total_price
        order.save()

        # ✅ TELEGRAM XABAR YUBORILADI:
        try:
            send_telegram_order_message(shop, order)
        except Exception as e:
            print(f"Telegramga xabar yuborishda xatolik: {e}")

        # return Response({"order_id": order.id, "total_price": order.total_price}, status=status.HTTP_201_CREATED)

        # ✅ TELEGRAM XABAR YUBORILADI:
        try:
            send_telegram_user_message(shop, order)
        except Exception as e:
            print(f"Telegramga xabar yuborishda xatolik: {e}")

        return Response({"order_id": order.id, "total_price": order.total_price}, status=status.HTTP_201_CREATED)


class OrderUserListAPIView(APIView):
    def get(self, request, *args, **kwargs):
        telegram_id = request.query_params.get('telegram_id')
        if not telegram_id:
            raise ValidationError({'telegram_id': 'required'})

        user = get_object_or_404(BotUser, telegram_id=telegram_id)
        orders = Order.objects.filter(user=user,
                                      items__product_variant__product__shop=user.active_shop).distinct().order_by(
            '-created_at')
        serializer = OrderSerializer(orders, many=True)

        return Response(serializer.data)


class OrderDetailAPIView(RetrieveAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    # lookup_field = 'id'  # Bu standart, `pk` ham bo‘lishi mumkin

    def get(self, request, *args, **kwargs):
        telegram_id = request.query_params.get('telegram_id')
        if not telegram_id:
            raise ValidationError({'telegram_id': 'required'})

        user = get_object_or_404(BotUser, telegram_id=telegram_id)

        order = self.get_object()
        if order.user != user:
            raise ValidationError({'detail': 'Siz faqat o`zingizning buyurtmangizni ko`rishingiz mumkin.'})

        serializer = self.get_serializer(order)
        return Response(serializer.data)


def get_status_list():
    translations = {
        'new': {'uz': 'Yangi', 'ru': 'Новый'},
        'confirmed': {'uz': 'Tasdiqlandi', 'ru': 'Подтвержден'},
        'shipped': {'uz': 'Jo‘natildi', 'ru': 'Отправлен'},
        'delivered': {'uz': 'Yetkazildi', 'ru': 'Доставлен'},
        'cancelled': {'uz': 'Bekor qilindi', 'ru': 'Отменен'},
    }

    return [
        {
            'key': key,
            'uz': translations[key]['uz'],
            'ru': translations[key]['ru'],
        }
        for key, _ in Order.STATUS_CHOICES
    ]


class OrderListByShopCodeAPIView(APIView):
    def get(self, request, *args, **kwargs):
        shop_code = request.query_params.get('shop_code')
        if not shop_code:
            raise ValidationError({'shop_code': 'required'})
        shop = get_object_or_404(Shop, shop_code=shop_code)
        orders = Order.objects.filter(items__product_variant__product__shop=shop).distinct().order_by('-created_at')
        serializer = OrderSerializer(orders, many=True)
        return Response({
            "orders": serializer.data,
            "statuses": get_status_list()
        })


class OrderShopDetailAPIView(RetrieveAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    lookup_field = 'pk'


class OrderStatusUpdateAPIView(UpdateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderStatusUpdateSerializer
    lookup_field = 'pk'

    def update(self, request, *args, **kwargs):
        # 1. Buyurtmani olish
        order = self.get_object()
        old_status = order.status

        # 2. Serializer orqali statusni validatsiya qilish
        serializer = self.get_serializer(order, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        # 3. Statusni yangilash
        new_status = serializer.validated_data.get('status')
        serializer.save()

        # 4. Agar status o‘zgargan bo‘lsa, foydalanuvchiga Telegram xabar yuborish
        if old_status != new_status:
            self.send_status_update_message(order)

        return Response({"detail": "Buyurtma holati muvaffaqiyatli yangilandi."}, status=status.HTTP_200_OK)

    def send_status_update_message(self, order):
        user = order.user
        chat_id = user.telegram_id
        lang = user.language  # 'uz' yoki 'ru'

        if not chat_id:
            print("❗️ Foydalanuvchining Telegram ID si mavjud emas.")
            return

        # 1. Status nomini tilga qarab tarjima qilish
        STATUS_TRANSLATIONS = {
            'uz': {
                'new': 'Yangi',
                'confirmed': 'Tasdiqlandi',
                'shipped': 'Jo‘natildi',
                'delivered': 'Yetkazildi',
                'cancelled': 'Bekor qilindi',
            },
            'ru': {
                'new': 'Новый',
                'confirmed': 'Подтверждён',
                'shipped': 'Отправлен',
                'delivered': 'Доставлен',
                'cancelled': 'Отменён',
            }
        }

        status_display = STATUS_TRANSLATIONS.get(lang, {}).get(order.status, order.status)

        # Foydalanuvchining tiliga qarab matnni tanlaymiz
        if lang == 'ru':
            text = f"""
📦 <b>Ваш заказ обновлён!</b>

🧾 <b>Номер заказа:</b> #{order.id}
📍 <b>Адрес:</b> {order.address or "Не указан"}
🆕 <b>Новый статус:</b> {status_display}
        """
        else:
            text = f"""
📦 <b>Sizning buyurtmangiz yangilandi!</b>

🧾 <b>Buyurtma raqami:</b> #{order.id}
📍 <b>Manzil:</b> {order.address or "Ko‘rsatilmagan"}
🆕 <b>Yangi holat:</b> {status_display}
        """

        url = f"https://api.telegram.org/bot{BOT_B_TOKEN}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML"
        }

        try:
            response = requests.post(url, json=payload)
            if response.status_code != 200:
                print("❌ Telegram xabarda xatolik:", response.text)
        except Exception as e:
            print(f"❌ Telegramga xabar yuborishda xatolik: {e}")


class ProductImageCreateView(CreateAPIView):
    queryset = ProductImage.objects.all()
    serializer_class = ProductCreateImageSerializer


class ProductImageDeleteView(DestroyAPIView):
    queryset = ProductImage.objects.all()
    serializer_class = ProductImageSerializer


class ProductVariantCreateView(CreateAPIView):
    queryset = ProductVariant.objects.all()
    serializer_class = ProductVariantPostSerializer


class ProductVariantDeleteView(RetrieveUpdateDestroyAPIView):
    queryset = ProductVariant.objects.all()
    serializer_class = ProductVariantPostSerializer

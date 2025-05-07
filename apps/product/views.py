from rest_framework.generics import ListAPIView, RetrieveAPIView
from .models import Product
from .serializers import ProductSerializer


class ProductListAPIView(ListAPIView):
    serializer_class = ProductSerializer

    def get_queryset(self):
        shop_code = self.kwargs.get('shop_code')  # ✅ To‘g‘ri nom
        return Product.objects.filter(shop__shop_code=shop_code, shop__is_active=True)

class ProductDetailView(RetrieveAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    lookup_field = 'pk'


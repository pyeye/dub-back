from rest_framework import serializers

from .models import Sale, SaleImage, CategorySale, CollectionSale, ProductSale, SALE_TYPES


class SaleImageSerializer(serializers.ModelSerializer):

    class Meta:
        model = SaleImage
        fields = ('pk', 'src')


class BaseSaleSerializer(serializers.ModelSerializer):

    def validate_details(self, value):
        sale_type = value.get('type', None)
        if sale_type is None or not sale_type:
            raise serializers.ValidationError('Выберите тип акции')

        if sale_type not in SALE_TYPES:
            raise serializers.ValidationError('Неверный тип акции')

        try:
            if not value[value['type']]:
                raise serializers.ValidationError('Заполните значение акции')
        except KeyError:
            raise serializers.ValidationError('Заполните значение акции')

        return {
            'type': value['type'],
            value['type']: value[value['type']],
        }


class CategorySaleSerializer(BaseSaleSerializer):

    class Meta:
        model = CategorySale
        fields = ('category', 'details')


class CollectionSaleSerializer(BaseSaleSerializer):

    class Meta:
        model = CollectionSale
        fields = ('collection', 'details')


class ProductSaleSerializer(BaseSaleSerializer):
    class Meta:
        model = ProductSale
        fields = ('product', 'details')


class CollectionListSaleSerializer(serializers.ModelSerializer):
    pk = serializers.IntegerField(source='collection.pk')
    name = serializers.CharField(source='collection.name')

    class Meta:
        model = CollectionSale
        fields = ('pk', 'name', 'details')


class CategoryListSaleSerializer(serializers.ModelSerializer):
    pk = serializers.IntegerField(source='category.pk')
    name = serializers.CharField(source='category.name')

    class Meta:
        model = CategorySale
        fields = ('pk', 'name', 'details')


class ProductListSaleSerializer(serializers.ModelSerializer):
    pk = serializers.IntegerField(source='product.pk')
    sku = serializers.IntegerField(source='product.sku')
    measure_count = serializers.CharField(source='product.measure_count')
    measure_value = serializers.CharField(source='product.measure_value')
    product_pk = serializers.IntegerField(source='product.product_info.pk')
    name = serializers.CharField(source='product.product_info.name')

    class Meta:
        model = CategorySale
        fields = ('pk', 'product_pk', 'sku', 'measure_count', 'measure_value', 'name', 'details')


class SaleSerializer(serializers.ModelSerializer):
    image = SaleImageSerializer(read_only=True)
    categories = CategoryListSaleSerializer(source='categorysale_set', many=True, read_only=True)
    collections = CollectionListSaleSerializer(source='collectionsale_set', many=True, read_only=True)
    products = ProductListSaleSerializer(source='productsale_set', many=True, read_only=True)

    class Meta:
        model = Sale
        fields = (
            'pk',
            'name',
            'description',
            'details',
            'date_start',
            'date_end',
            'image',
            'categories',
            'collections',
            'products',
            'is_active',
        )


class SaleApiSerializer(serializers.ModelSerializer):
    image = SaleImageSerializer(read_only=True)

    class Meta:
        model = Sale
        fields = (
            'pk',
            'name',
            'description',
            'date_start',
            'date_end',
            'image',
            'is_active',
        )


class SaleAdminSerializer(BaseSaleSerializer):
    categories = CategorySaleSerializer(source='categorysale_set', many=True)
    collections = CollectionSaleSerializer(source='collectionsale_set', many=True)
    products = ProductSaleSerializer(source='productsale_set', many=True)

    class Meta:
        model = Sale
        fields = (
            'pk',
            'name',
            'description',
            'details',
            'date_start',
            'date_end',
            'image',
            'categories',
            'collections',
            'products',
            'is_active',
        )

    def validate_image(self, value):
        if not value:
            raise serializers.ValidationError('Это поле не может быть пустым.')

    def validate(self, data):
        categories = data.get('categorysale_set', None)
        collections = data.get('collectionsale_set', None)
        products = data.get('productsale_set', None)
        if categories is None and collections is None and products is None:
            raise serializers.ValidationError(
                'Акция должна содержать хотя бы одну позицию категории, коллекции или товара'
            )
        return data

    def create(self, validated_data):
        categories = validated_data.pop('categorysale_set', [])
        collections = validated_data.pop('collectionsale_set', [])
        products = validated_data.pop('productsale_set', [])

        sale = Sale.objects.create(**validated_data)

        for category in categories:
            CategorySale.objects.create(sale=sale, **category)

        for collection in collections:
            CollectionSale.objects.create(sale=sale, **collection)

        for product in products:
            ProductSale.objects.create(sale=sale, **product)

        return sale

    def update(self, instance, validated_data):
        instance.name = validated_data.pop('name')
        instance.description = validated_data.pop('description')
        instance.details = validated_data.pop('details')
        instance.date_start = validated_data.pop('date_start')
        instance.date_end = validated_data.pop('date_end')
        instance.is_active = validated_data.pop('is_active')
        instance.save()

        categories = validated_data.pop('categorysale_set', [])
        collections = validated_data.pop('collectionsale_set', [])
        products = validated_data.pop('products', [])

        instance.categories.clear()
        for category in categories:
            CategorySale.objects.create(sale=instance, **category)

        instance.collections.clear()
        for collection in collections:
            CollectionSale.objects.create(sale=instance, **collection)

        instance.products.clear()
        for product in products:
            ProductSale.objects.create(sale=instance, **product)

        return instance

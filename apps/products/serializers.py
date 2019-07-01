from rest_framework import serializers

from .models import (
    ProductInfo,
    ProductInstance,
    ProductImage,
    Category,
    Manufacturer,
    Tags,
    SFacet,
    SFacetValue,
    NFacet,
    NFacetValue,
    CollectionImage,
    Collection,
)


class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = ('pk', 'name', 'is_active', 'slug')


class NFacetSerializer(serializers.ModelSerializer):

    class Meta:
        model = NFacet
        fields = ('pk', 'name', 'slug', 'suffix', 'is_active')


class SFacetValueRelatedSerializer(serializers.ModelSerializer):

    class Meta:
        model = SFacetValue
        fields = ('pk', 'name', 'is_active')


class SFacetListSerializer(serializers.ModelSerializer):

    class Meta:
        model = SFacet
        fields = ('pk', 'name', 'slug', 'is_active')


class SFacetValueListSerializer(serializers.ModelSerializer):
    facet = SFacetListSerializer(read_only=True)

    class Meta:
        model = SFacetValue
        fields = ('pk', 'facet', 'name', 'is_active')


class SFacetSerializer(serializers.ModelSerializer):
    values = SFacetValueRelatedSerializer(many=True, read_only=True)

    class Meta:
        model = SFacet
        fields = ('pk', 'values', 'name', 'slug', 'is_active')


class SFacetValueSerializer(serializers.ModelSerializer):

    class Meta:
        model = SFacetValue
        fields = ('pk', 'facet', 'name', 'is_active')


class TagsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tags
        fields = ('pk', 'name', 'is_active')


class ManufacturerSerializer(serializers.ModelSerializer):

    class Meta:
        model = Manufacturer
        fields = ('pk', 'name', 'is_active', 'slug')


class ProductImagesSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProductImage
        fields = ('pk', 'src', 'is_active', 'is_main')


class ProductInstanceSerializer(serializers.ModelSerializer):
    images = ProductImagesSerializer(many=True)

    class Meta:
        model = ProductInstance
        fields = (
            'pk',
            'sku',
            'images',
            'measure_count',
            'measure_value',
            'price',
            'stock_balance',
            'package_amount',
            'sales',
        )


class ProductNFacetsValueSerializer(serializers.ModelSerializer):

    class Meta:
        model = NFacetValue
        fields = ('facet', 'value',)


class ProductNFacetsRetrieveSerializer(serializers.ModelSerializer):
    pk = serializers.ReadOnlyField(source='facet.pk')
    name = serializers.ReadOnlyField(source='facet.name')
    slug = serializers.ReadOnlyField(source='facet.slug')
    suffix = serializers.ReadOnlyField(source='facet.suffix')

    class Meta:
        model = NFacetValue
        fields = ('pk', 'name', 'slug', 'suffix', 'value',)


class ProductInstanceCreateSerializer(serializers.ModelSerializer):
    pk = serializers.IntegerField(read_only=False)

    class Meta:
        model = ProductInstance
        fields = (
            'pk',
            'sku',
            'images',
            'measure_count',
            'measure_value',
            'price',
            'stock_balance',
            'package_amount',
        )

    def validate_images(self, value):
        if not value:
            raise serializers.ValidationError('Это поле не может быть пустым.')

        return value


class ProductCreateSerializer(serializers.ModelSerializer):
    instances = ProductInstanceCreateSerializer(many=True)
    nfacets = ProductNFacetsValueSerializer(source='nfacetvalue_set', many=True)

    class Meta:
        model = ProductInfo
        fields = (
            'pk',
            'name',
            'manufacturer',
            'description',
            'instances',
            'category',
            'tags',
            'sfacets',
            'nfacets',
            'status',
        )

    def validate(self, data):
        if len(data['instances']) == 0:
            raise serializers.ValidationError('Требуется минимум одна позиция товара')

        for instance in data['instances']:
            if len(instance['images']) > 0:
                main_images = [image.pk for image in instance['images'] if image.is_main]
                if len(main_images) != 1:
                    raise serializers.ValidationError('Должна быть одна основная  фотография')

        return data


    def create(self, validated_data):
        instances = validated_data.pop('instances')
        nfacets = validated_data.pop('nfacetvalue_set')
        tags = validated_data.pop('tags')
        sfacets = validated_data.pop('sfacets')

        product_info = ProductInfo.objects.create(**validated_data)

        for instance in instances:
            images = instance.pop('images')
            product_instance = ProductInstance.objects.create(product_info=product_info, **instance)
            for image in images:
                image.instance = product_instance
                image.save()

        product_info.tags.add(*tags)
        product_info.sfacets.add(*sfacets)

        for nfacet in nfacets:
            NFacetValue.objects.create(product_info=product_info, **nfacet)

        return product_info

    def update(self, product, validated_data):
        product.name = validated_data.pop('name')
        product.category = validated_data.pop('category')
        product.status = validated_data.pop('status')
        product.manufacturer = validated_data.pop('manufacturer')
        product.description = validated_data.pop('description')
        product.save()

        instances = validated_data.pop('instances')
        nfacets = validated_data.pop('nfacetvalue_set', [])
        tags = validated_data.pop('tags', [])
        sfacets = validated_data.pop('sfacets', [])

        for instance in instances:
            images = instance.pop('images')
            pk = instance.pop('pk', None)
            if pk is not None:
                product_instance = ProductInstance.objects.get(pk=pk)
                product_instance.sku = instance.pop('sku')
                product_instance.measure_count = instance.pop('measure_count')
                product_instance.price = instance.pop('price')
                product_instance.package_amount = instance.pop('package_amount')
                product_instance.stock_balance = instance.pop('stock_balance')
                product_instance.measure_value = instance.pop('measure_value')
                product_instance.save()
            else:
                product_instance = ProductInstance.objects.create(product_info=product, **instance)

            for image in images:
                image.instance = product_instance
                image.save()


        product.tags.clear()
        product.tags.add(*tags)

        product.sfacets.clear()
        product.sfacets.add(*sfacets)

        product.nfacets.clear()
        for nfacet in nfacets:
            NFacetValue.objects.create(product_info=product, **nfacet)

        return product


class ProductListSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    manufacturer = ManufacturerSerializer(read_only=True)
    tags = TagsSerializer(many=True, read_only=True)
    sfacets = SFacetValueListSerializer(many=True, read_only=True)
    nfacets = ProductNFacetsValueSerializer(source='nfacetvalue_set', many=True, read_only=True)
    instances = ProductInstanceSerializer(many=True, read_only=True)

    class Meta:
        model = ProductInfo
        fields = (
            'pk',
            'name',
            'manufacturer',
            'description',
            'instances',
            'category',
            'tags',
            'sfacets',
            'nfacets',
            'status',
            'created_at',
        )


class ProductTableListSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    manufacturer = ManufacturerSerializer(read_only=True)
    instances = ProductInstanceSerializer(many=True, read_only=True)

    class Meta:
        model = ProductInfo
        fields = (
            'pk',
            'name',
            'manufacturer',
            'instances',
            'category',
            'status',
        )


class ProductRetriveSerializer(serializers.ModelSerializer):
    sfacets = SFacetValueListSerializer(many=True, read_only=True)
    nfacets = ProductNFacetsRetrieveSerializer(source='nfacetvalue_set', many=True, read_only=True)
    instances = ProductInstanceSerializer(many=True, read_only=True)

    class Meta:
        model = ProductInfo
        fields = (
            'pk',
            'name',
            'manufacturer',
            'description',
            'instances',
            'category',
            'tags',
            'sfacets',
            'nfacets',
            'status',
        )


class CollectionImageSerializer(serializers.ModelSerializer):

    class Meta:
        model = CollectionImage
        fields = ('pk', 'src')


class CollectionProductRetriveSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProductInfo
        fields = (
            'pk',
            'name',
        )


class CollectionProductInstanceSerializer(serializers.ModelSerializer):
    images = ProductImagesSerializer(many=True)
    product_info = CollectionProductRetriveSerializer()

    class Meta:
        model = ProductInstance
        fields = (
            'pk',
            'product_info',
            'sku',
            'images',
            'measure_count',
            'measure_value',
        )


class CollectionSerializer(serializers.ModelSerializer):
    image = CollectionImageSerializer(read_only=True)
    products = CollectionProductInstanceSerializer(many=True)

    class Meta:
        model = Collection
        fields = ('pk', 'name', 'slug', 'is_public', 'is_active', 'description', 'products', 'image')


class CollectionCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Collection
        fields = ('pk', 'name', 'description', 'image', 'products', 'is_public')

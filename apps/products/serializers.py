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
        fields = ("pk", "name", "is_active", "slug")


class NFacetSerializer(serializers.ModelSerializer):
    position = serializers.SerializerMethodField()

    class Meta:
        model = NFacet
        fields = ("pk", "name", "slug", "suffix", "is_active", "position")

    def get_position(self, obj):
        return obj.extra.get("order", 1)


class SFacetValueRelatedSerializer(serializers.ModelSerializer):
    class Meta:
        model = SFacetValue
        fields = ("pk", "name", "is_active")


class SFacetListSerializer(serializers.ModelSerializer):
    position = serializers.SerializerMethodField()

    class Meta:
        model = SFacet
        fields = ("pk", "name", "slug", "is_active", "position")

    def get_position(self, obj):
        return obj.extra.get("order", 1)


class SFacetValueListSerializer(serializers.ModelSerializer):
    facet = SFacetListSerializer(read_only=True)

    class Meta:
        model = SFacetValue
        fields = ("pk", "facet", "name", "is_active")


class SFacetSerializer(serializers.ModelSerializer):
    values = SFacetValueRelatedSerializer(many=True, read_only=True)

    class Meta:
        model = SFacet
        fields = ("pk", "values", "name", "slug", "is_active")


class SFacetValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = SFacetValue
        fields = ("pk", "facet", "name", "is_active")


class TagsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tags
        fields = ("pk", "name", "is_active")


class ManufacturerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Manufacturer
        fields = ("pk", "name", "is_active", "slug")


class ProductImagesSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ("pk", "src", "is_active", "is_main")


class ProductInstanceSerializer(serializers.ModelSerializer):
    images = ProductImagesSerializer(many=True)

    class Meta:
        model = ProductInstance
        fields = (
            "pk",
            "sku",
            "images",
            "status",
            "measure",
            "capacity_type",
            "price",
            "base_price",
            "stock_balance",
            "package_amount",
            "sales",
            "collections",
        )


class ProductNFacetValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = NFacetValue
        fields = "__all__"


class ProductNFacetsRetrieveSerializer(serializers.ModelSerializer):
    pk = serializers.ReadOnlyField(source="facet.pk")
    name = serializers.ReadOnlyField(source="facet.name")
    slug = serializers.ReadOnlyField(source="facet.slug")
    suffix = serializers.ReadOnlyField(source="facet.suffix")

    class Meta:
        model = NFacetValue
        fields = (
            "pk",
            "name",
            "slug",
            "suffix",
            "value",
        )


class ProductInstanceCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductInstance
        fields = (
            "pk",
            "sku",
            "images",
            "measure",
            "capacity_type",
            "base_price",
            "stock_balance",
            "package_amount",
            "status",
        )

    def validate_images(self, value):
        if not value:
            raise serializers.ValidationError("Это поле не может быть пустым.")

        main_images = [image.pk for image in value if image.is_main]
        if len(main_images) != 1:
            raise serializers.ValidationError("Должна быть одна основная  фотография")

        return value

    def update(self, instance, validated_data):
        images = validated_data.pop("images")

        # Пересечение ключей validated_data и разрешённых полей
        for attr in validated_data.keys() & set(self.Meta.fields):
            setattr(instance, attr, validated_data[attr])
        instance.save()

        for image in images:
            image.instance = instance
            image.save()

        return instance


class ProductCreateSerializer(serializers.ModelSerializer):
    instances = ProductInstanceCreateSerializer(many=True)

    class Meta:
        model = ProductInfo
        fields = (
            "pk",
            "name",
            "manufacturer",
            "description",
            "instances",
            "category",
            "tags",
            "sfacets",
            "nfacets",
            "extra",
        )

    def validate(self, data):
        if len(data["instances"]) == 0:
            raise serializers.ValidationError("Требуется минимум одна позиция товара")

        # for instance in data['instances']:
        #    if len(instance['images']) > 0:
        #        main_images = [image.pk for image in instance['images'] if image.is_main]
        #        if len(main_images) != 1:
        #            raise serializers.ValidationError('Должна быть одна основная  фотография')

        return data

    def create(self, validated_data):
        instances = validated_data.pop("instances")
        # nfacets = validated_data.pop('nfacetvalue_set')
        nfacets = validated_data.pop("nfacets")
        tags = validated_data.pop("tags")
        sfacets = validated_data.pop("sfacets")

        product_info = ProductInfo.objects.create(**validated_data)

        for instance in instances:
            images = instance.pop("images")
            instance["price"] = instance["base_price"]
            product_instance = ProductInstance.objects.create(
                product_info=product_info, **instance
            )
            for image in images:
                image.instance = product_instance
                image.save()

        product_info.tags.add(*tags)
        product_info.sfacets.add(*sfacets)

        product_info.nfacets.add(*nfacets)

        # for nfacet in nfacets:
        #    NFacetValue.objects.create(product_info=product_info, **nfacet)

        return product_info

    def update(self, product, validated_data):
        fields = {"name", "category", "status", "manufacturer", "description"}
        for attr in validated_data.keys() & fields:
            setattr(product, attr, validated_data[attr])
        product.save()

        nfacets = validated_data.pop("nfacets", [])
        tags = validated_data.pop("tags", [])
        sfacets = validated_data.pop("sfacets", [])

        product.tags.clear()
        product.tags.add(*tags)

        product.sfacets.clear()
        product.sfacets.add(*sfacets)

        product.nfacets.clear()
        for nfacet in nfacets:
            NFacetValue.objects.create(product_info=product, **nfacet)

        return product


class AdminProductInfoSerializer(serializers.ModelSerializer):
    nfacets = ProductNFacetValueSerializer(many=True)
    instances = ProductInstanceCreateSerializer(many=True)

    class Meta:
        model = ProductInfo
        fields = (
            "pk",
            "name",
            "manufacturer",
            "description",
            "category",
            "tags",
            "sfacets",
            "nfacets",
            "instances",
        )

    def update(self, product, validated_data):
        product.name = validated_data.pop("name")
        product.category = validated_data.pop("category")
        product.status = validated_data.pop("status")
        product.manufacturer = validated_data.pop("manufacturer")
        product.description = validated_data.pop("description")
        product.save()

        nfacets = validated_data.pop("nfacets", [])
        tags = validated_data.pop("tags", [])
        sfacets = validated_data.pop("sfacets", [])

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
    nfacets = ProductNFacetValueSerializer(many=True, read_only=True)
    instances = ProductInstanceSerializer(many=True, read_only=True)

    class Meta:
        model = ProductInfo
        fields = (
            "pk",
            "name",
            "name_slug",
            "manufacturer",
            "description",
            "instances",
            "category",
            "tags",
            "sfacets",
            "nfacets",
            "created_at",
            "extra",
        )


class ProductTableListSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    manufacturer = ManufacturerSerializer(read_only=True)
    instances = ProductInstanceSerializer(many=True, read_only=True)

    class Meta:
        model = ProductInfo
        fields = (
            "pk",
            "name",
            "manufacturer",
            "instances",
            "category",
            "status",
        )


class ProductInstanceTableSerializer(serializers.ModelSerializer):
    category = serializers.ReadOnlyField(source="product_info.category.name")
    name = serializers.ReadOnlyField(source="product_info.name")

    class Meta:
        model = ProductInstance
        fields = (
            "pk",
            "sku",
            "measure",
            "category",
            "name",
        )


class ProductRetriveSerializer(serializers.ModelSerializer):
    sfacets = SFacetValueListSerializer(many=True, read_only=True)
    nfacets = ProductNFacetsRetrieveSerializer(many=True, read_only=True)
    instances = ProductInstanceSerializer(many=True, read_only=True)

    class Meta:
        model = ProductInfo
        fields = (
            "pk",
            "name",
            "manufacturer",
            "description",
            "instances",
            "category",
            "tags",
            "sfacets",
            "nfacets",
        )


class CollectionImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = CollectionImage
        fields = ("pk", "src")


class CollectionProductRetriveSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductInfo
        fields = (
            "pk",
            "name",
        )


class CollectionProductInstanceSerializer(serializers.ModelSerializer):
    images = ProductImagesSerializer(many=True)
    product_info = CollectionProductRetriveSerializer()

    class Meta:
        model = ProductInstance
        fields = (
            "pk",
            "product_info",
            "sku",
            "images",
            "measure",
        )


class CollectionSerializer(serializers.ModelSerializer):
    image = CollectionImageSerializer(read_only=True)
    products = CollectionProductInstanceSerializer(many=True)

    class Meta:
        model = Collection
        fields = (
            "pk",
            "name",
            "slug",
            "is_public",
            "is_active",
            "description",
            "products",
            "image",
        )


class CollectionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Collection
        fields = ("pk", "name", "description", "image", "products", "is_public")

    def validate_image(self, value):
        if not value:
            raise serializers.ValidationError("Это поле не может быть пустым.")

        return value


class CollectionApiSerializer(serializers.ModelSerializer):
    image = CollectionImageSerializer(read_only=True)

    class Meta:
        model = Collection
        fields = (
            "pk",
            "name",
            "slug",
            "is_public",
            "is_active",
            "description",
            "image",
        )

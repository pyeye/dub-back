"""core URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.conf import settings
from rest_framework import routers

from apps.authentication.views import CreateGuestView, JWTUserView, SecretView
from apps.users.views import CustomerAPIView, PasswordAPIView, CartSessionAPIView, WatchedSessionAPIView
from apps.news.views import NewsViewSet
from apps.products.views import CategoryAPIView, TagsListAPI, FacetsListAPI, ProductListAPI, ProductDetailAPI, ProductDetailInstancesAPI, FacetAllValuesListAPI, CollectionDetailAPIView
from apps.home.views import HomeCollectionAPI, HomeSalesAPI, HomeNewsApiView, NewProductsListAPI
from apps.search.views import SearchListAPI, CompletionListAPI
from apps.sales.views import SalesViewSet

from apps.products.admin_api import (
    AdminProductViewSet,
    AdminProductInstanceViewSet,
    AdminProductCategoryViewSet,
    AdminProductTagsViewSet,
    AdminProductManufacturerViewSet,
    AdminProductNFacetViewSet,
    AdminProductSFacetViewSet,
    AdminProductSFacetValueViewSet,
    AdminProductImageViewSet,
    AdminCollectionImageViewSet,
    AdminCollectionViewSet,
)
from apps.news.admin_api import AdminNewsViewSet, AdminNewsCategoryViewSet, AdminNewsImageViewSet
from apps.sales.admin import AdminSaleViewSet, AdminSalesImageViewSet
from apps.home.admin import AdminHomeSaleViewSet, AdminHomeCollectionViewSet

router = routers.SimpleRouter()
router.register(r'news', NewsViewSet, basename='api-news')
router.register(r'sales', SalesViewSet, basename='api-sales')

admin_router = routers.SimpleRouter()
admin_router.register(r'news', AdminNewsViewSet, basename='admin-news')
admin_router.register(r'nimages', AdminNewsImageViewSet, basename='admin-news-image')
admin_router.register(r'cimages', AdminCollectionImageViewSet, basename='admin-collections-image')
admin_router.register(r'collections', AdminCollectionViewSet, basename='admin-collections')
admin_router.register(r'simages', AdminSalesImageViewSet, basename='admin-sales-image')
admin_router.register(r'sales', AdminSaleViewSet, basename='admin-sales')
admin_router.register(r'ncategories', AdminNewsCategoryViewSet, basename='admin-news-category')
admin_router.register(r'products', AdminProductViewSet, basename='admin-products')
admin_router.register(r'product-instances', AdminProductInstanceViewSet, basename='admin-product-instances')
admin_router.register(r'pimages', AdminProductImageViewSet, basename='admin-products-images')
admin_router.register(r'pcategories', AdminProductCategoryViewSet, basename='admin-products-category')
admin_router.register(r'ptags', AdminProductTagsViewSet, basename='admin-products-tags')
admin_router.register(r'pmanufacturers', AdminProductManufacturerViewSet, basename='admin-products-manufacturers')
admin_router.register(r'pnfacets', AdminProductNFacetViewSet, basename='admin-products-number-facets')
admin_router.register(r'psfacets', AdminProductSFacetViewSet, basename='admin-products-string-facets')
admin_router.register(r'psfacets-values', AdminProductSFacetValueViewSet, basename='admin-products-string-facets-values')
admin_router.register(r'home-sales', AdminHomeSaleViewSet, basename='admin-home-sales')
admin_router.register(r'home-collections', AdminHomeCollectionViewSet, basename='admin-home-sales')

urlpatterns = [
    url(r'^admin/', include(admin_router.urls)),
    url(r'^v1/', include(router.urls)),
    url(r'^v1/products/(?P<pk>\d+)/$', ProductDetailAPI.as_view(), name="products-detail"),
    url(r'^v1/products/', ProductListAPI.as_view(), name="products-list"),
    url(r'^v1/product-instances/(?P<pk>\d+)/$', ProductDetailInstancesAPI.as_view(), name="products-detail-instances"),
    url(r'^v1/collections/(?P<pk>\d+)/$', CollectionDetailAPIView.as_view(), name="collection-detail"),
    url(r'^v1/search/', SearchListAPI.as_view(), name="products-search"),
    url(r'^v1/completions/', CompletionListAPI.as_view(), name="products-complete"),
    url(r'^v1/auth/user/', JWTUserView.as_view(), name="token-user"),
    url(r'^v1/auth/guest/', CreateGuestView.as_view(), name="token-create"),
    url(r'^v1/auth/', include('oauth2_provider.urls', namespace='oauth2_provider')),
    url(r'^v1/category/', CategoryAPIView.as_view(), name="category-api"),
    url(r'^v1/customers/set_password/', PasswordAPIView.as_view(), name="password-api"),
    url(r'^v1/customers/', CustomerAPIView.as_view(), name="customers-api"),
    url(r'^v1/home/sales/', HomeSalesAPI.as_view(), name="banner-api"),
    url(r'^v1/home/collections/', HomeCollectionAPI.as_view(), name="advertisement-api"),
    url(r'^v1/home/news/', HomeNewsApiView.as_view(), name="home-news-api"),
    url(r'^v1/home/new/', NewProductsListAPI.as_view(), name="new-products-api"),
    url(r'^v1/tags/', TagsListAPI.as_view(), name="tags-list"),
    url(r'^v1/facets/', FacetsListAPI.as_view(), name="facets-list"),
    url(r'^v1/facet/full/', FacetAllValuesListAPI.as_view(), name="facets-all-list"),
    url(r'^v1/session/carts/', CartSessionAPIView.as_view(), name="session-carts-api"),
    url(r'^v1/session/watched/', WatchedSessionAPIView.as_view(), name="session-watched-api"),
    url(r'^v1/secret/', SecretView.as_view(), name="secret-list"),

]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        url(r'^v1/__debug__/', include(debug_toolbar.urls)),
    ]

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
from apps.products.views import CategoryAPIView, TagsListAPI, FacetsListAPI, ProductListAPI, ProductDetailAPI
from apps.home.views import BannerApiView, AdvertisementApiView, HomeNewsApiView, BestsellersListAPI
from apps.search.views import SearchListAPI, CompletionListAPI
from apps.sales.views import SalesViewSet

from apps.products.admin_api import (
    AdminProductViewSet,
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

router = routers.SimpleRouter()
router.register(r'news', NewsViewSet, base_name='api-news')
router.register(r'sales', SalesViewSet, base_name='api-sales')

admin_router = routers.SimpleRouter()
admin_router.register(r'news', AdminNewsViewSet, base_name='admin-news')
admin_router.register(r'nimages', AdminNewsImageViewSet, base_name='admin-news-image')
admin_router.register(r'cimages', AdminCollectionImageViewSet, base_name='admin-collections-image')
admin_router.register(r'collections', AdminCollectionViewSet, base_name='admin-collections')
admin_router.register(r'simages', AdminSalesImageViewSet, base_name='admin-sales-image')
admin_router.register(r'sales', AdminSaleViewSet, base_name='admin-sales')
admin_router.register(r'ncategories', AdminNewsCategoryViewSet, base_name='admin-news-category')
admin_router.register(r'products', AdminProductViewSet, base_name='admin-products')
admin_router.register(r'pimages', AdminProductImageViewSet, base_name='admin-products-images')
admin_router.register(r'pcategories', AdminProductCategoryViewSet, base_name='admin-products-category')
admin_router.register(r'ptags', AdminProductTagsViewSet, base_name='admin-products-tags')
admin_router.register(r'pmanufacturers', AdminProductManufacturerViewSet, base_name='admin-products-manufacturers')
admin_router.register(r'pnfacets', AdminProductNFacetViewSet, base_name='admin-products-number-facets')
admin_router.register(r'psfacets', AdminProductSFacetViewSet, base_name='admin-products-string-facets')
admin_router.register(r'psfacets-values', AdminProductSFacetValueViewSet, base_name='admin-products-string-facets-values')

urlpatterns = [
    url(r'^admin/', include(admin_router.urls)),
    url(r'^v1/', include(router.urls)),
    url(r'^v1/products/(?P<pk>\d+)/$', ProductDetailAPI.as_view(), name="products-detail"),
    url(r'^v1/products/', ProductListAPI.as_view(), name="products-list"),
    url(r'^v1/search/', SearchListAPI.as_view(), name="products-search"),
    url(r'^v1/completions/', CompletionListAPI.as_view(), name="products-complete"),
    url(r'^v1/auth/user/', JWTUserView.as_view(), name="token-user"),
    url(r'^v1/auth/guest/', CreateGuestView.as_view(), name="token-create"),
    url(r'^v1/auth/', include('oauth2_provider.urls', namespace='oauth2_provider')),
    url(r'^v1/category/', CategoryAPIView.as_view(), name="category-api"),
    url(r'^v1/customers/set_password/', PasswordAPIView.as_view(), name="password-api"),
    url(r'^v1/customers/', CustomerAPIView.as_view(), name="customers-api"),
    url(r'^v1/home/banners/', BannerApiView.as_view(), name="banner-api"),
    url(r'^v1/home/posters/', AdvertisementApiView.as_view(), name="advertisement-api"),
    url(r'^v1/home/news/', HomeNewsApiView.as_view(), name="home-news-api"),
    url(r'^v1/home/bestsellers/', BestsellersListAPI.as_view(), name="bestseller-api"),
    url(r'^v1/tags/', TagsListAPI.as_view(), name="tags-list"),
    url(r'^v1/facets/', FacetsListAPI.as_view(), name="facets-list"),
    url(r'^v1/session/carts/', CartSessionAPIView.as_view(), name="session-carts-api"),
    url(r'^v1/session/watched/', WatchedSessionAPIView.as_view(), name="session-watched-api"),
    url(r'^v1/secret/', SecretView.as_view(), name="secret-list"),

]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        url(r'^v1/__debug__/', include(debug_toolbar.urls)),
    ]

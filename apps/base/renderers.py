from itertools import groupby

from rest_framework.renderers import JSONRenderer


class ProductRenderer(JSONRenderer):
    format = 'dub_menu'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        data.sort(key=lambda elem: elem['category']['name'])

        categories = [menu['category'] for menu in data]
        render_category = [k for k, v in groupby(categories, key=lambda elem: elem)]

        groups_data = groupby(data, key=lambda elem: elem['category']['name'])
        # [x for x in v] эквивалент list(v)
        render_data = [{'category': k, 'items': [x for x in v]} for k, v in groups_data]

        final_data =  map(self.combine_menu, zip(render_category, render_data))

        return super(ProductRenderer, self).render(data={'data': final_data, 'categories': render_category},
                                                  accepted_media_type=accepted_media_type,
                                                  renderer_context=renderer_context)

    def combine_menu(self, pair):
        category, menu = pair
        menu['category'] = category
        return menu
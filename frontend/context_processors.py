from .models import Category


def category_list(request):

    categories = (
        Category.objects
        .filter(parent__isnull=True)
        .prefetch_related("children__children")
    )

    # Categories which directly contain products
    product_category_ids = set(
        Category.objects.filter(
            productss__isnull=False
        )
        .values_list("id", flat=True)
        .distinct()
    )

    visible_ids = set(product_category_ids)

    # Add parents of categories containing products
    changed = True

    while changed:

        changed = False

        parent_ids = (
            Category.objects
            .filter(children__id__in=visible_ids)
            .values_list("id", flat=True)
            .distinct()
        )

        for parent_id in parent_ids:

            if parent_id not in visible_ids:

                visible_ids.add(parent_id)

                changed = True


    # Only top-level categories which are actually visible
    categories = [
        category
        for category in categories
        if category.id in visible_ids
    ]


    # Build visible children
    for category in categories:

        visible_children = []

        for child in category.children.all():

            if child.id in visible_ids:

                visible_children.append(child)


        category.visible_children = visible_children


        # Build visible grandchildren
        for child in visible_children:

            visible_grandchildren = []

            for grandchild in child.children.all():

                if grandchild.id in visible_ids:

                    visible_grandchildren.append(
                        grandchild
                    )


            child.visible_grandchildren = (
                visible_grandchildren
            )


    return {
        "categories": categories,
    }
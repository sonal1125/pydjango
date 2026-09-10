from io import BytesIO

from PIL import Image
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from frontend.models import Category, Inquiry, Products, Seller, SellerPlan


class SignupRoleTests(TestCase):
    def _verified_signup_post(self, payload):
        initial_response = self.client.post(reverse("signup"), payload)
        self.assertEqual(initial_response.status_code, 200)
        pending = self.client.session.get("pending_email_verification", {})
        self.assertTrue(pending.get("code"))

        verified_payload = dict(payload)
        verified_payload["verification_code"] = pending["code"]
        response = self.client.post(reverse("signup"), verified_payload)
        return response

    def test_customer_signup_creates_user_only(self):
        payload = {
            "account_type": "customer",
            "username": "newcustomer",
            "email": "customer@example.com",
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
        }

        response = self._verified_signup_post(payload)

        self.assertEqual(response.status_code, 302)
        user = get_user_model().objects.get(username="newcustomer")
        self.assertFalse(hasattr(user, "seller"))

    def test_seller_signup_creates_seller_profile(self):
        payload = {
            "account_type": "seller",
            "username": "newseller",
            "email": "seller@example.com",
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
            "store_name": "Artisan Lane",
            "owner_name": "Asha Verma",
            "phone": "9876543210",
        }

        response = self._verified_signup_post(payload)

        self.assertEqual(response.status_code, 302)
        user = get_user_model().objects.get(username="newseller")
        self.assertTrue(Seller.objects.filter(user=user, store_name="Artisan Lane").exists())

    def test_duplicate_store_name_gets_unique_slug(self):
        first_user = get_user_model().objects.create_user(
            username="seller1",
            email="seller1@example.com",
            password="StrongPass123!",
        )
        second_user = get_user_model().objects.create_user(
            username="seller2",
            email="seller2@example.com",
            password="StrongPass123!",
        )

        first = Seller.objects.create(user=first_user, store_name="MacCroch", owner_name="A")
        second = Seller.objects.create(user=second_user, store_name="MacCroch", owner_name="B")

        self.assertEqual(first.slug, "maccroch")
        self.assertEqual(second.slug, "maccroch-1")

    def test_paid_seller_signup_redirects_to_plan_checkout(self):
        payload = {
            "account_type": "seller",
            "username": "premiumseller",
            "email": "premium@example.com",
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
            "store_name": "Premium Store",
            "owner_name": "Raja Sharma",
            "phone": "9876543210",
            "payment_mode": "upi",
            "selected_plan": "starter",
        }

        response = self._verified_signup_post(payload)

        self.assertEqual(response.status_code, 302)
        self.assertIn("/seller/plan/", response.url)

    def test_customer_signup_requires_email_verification_code(self):
        response = self.client.post(
            reverse("signup"),
            {
                "account_type": "customer",
                "username": "verifiedcustomer",
                "email": "verifiedcustomer@example.com",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Email verification code has been sent")
        self.assertFalse(get_user_model().objects.filter(username="verifiedcustomer").exists())

        pending_verification = self.client.session.get("pending_email_verification", {})
        code = pending_verification.get("code")
        self.assertTrue(code)

        response = self.client.post(
            reverse("signup"),
            {
                "account_type": "customer",
                "username": "verifiedcustomer",
                "email": "verifiedcustomer@example.com",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
                "verification_code": code,
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(get_user_model().objects.filter(username="verifiedcustomer").exists())

    def test_seller_signup_requires_email_verification_code(self):
        response = self.client.post(
            reverse("signup"),
            {
                "account_type": "seller",
                "username": "verifiedseller",
                "email": "verifiedseller@example.com",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
                "store_name": "Verified Store",
                "owner_name": "Sita Rao",
                "phone": "9876543211",
                "selected_plan": "free",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Email verification code has been sent")
        self.assertFalse(get_user_model().objects.filter(username="verifiedseller").exists())

        pending_verification = self.client.session.get("pending_email_verification", {})
        code = pending_verification.get("code")
        self.assertTrue(code)

        response = self.client.post(
            reverse("signup"),
            {
                "account_type": "seller",
                "username": "verifiedseller",
                "email": "verifiedseller@example.com",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
                "store_name": "Verified Store",
                "owner_name": "Sita Rao",
                "phone": "9876543211",
                "selected_plan": "free",
                "verification_code": code,
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(get_user_model().objects.filter(username="verifiedseller").exists())
        self.assertTrue(Seller.objects.filter(user__username="verifiedseller", store_name="Verified Store").exists())

    def test_plan_catalogue_comes_from_canonical_seller_plan_records(self):
        free_plan = SellerPlan.objects.create(
            name="Free",
            slug="free",
            product_limit=10,
            media_limit=1,
            price=0,
            is_default=True,
        )
        starter = SellerPlan.objects.create(
            name="Starter",
            slug="starter",
            product_limit=50,
            media_limit=5,
            price=999,
        )
        growth = SellerPlan.objects.create(
            name="Growth",
            slug="growth",
            product_limit=200,
            media_limit=12,
            price=2499,
        )

        self.assertEqual(SellerPlan.get_default_plan(), free_plan)
        self.assertEqual(
            SellerPlan.get_plan_choices(),
            [
                ("free", "Free Plan"),
                ("starter", "Starter Plan - ₹999 / month"),
                ("growth", "Growth Plan - ₹2499 / month"),
            ],
        )
        self.assertEqual(SellerPlan.resolve_plan("starter"), starter)
        self.assertEqual(SellerPlan.resolve_plan("missing"), free_plan)

    def test_seller_plan_checkout_saves_selected_plan(self):
        self.user = get_user_model().objects.create_user(
            username="plancheckoutseller",
            email="plancheckout@example.com",
            password="StrongPass123!",
        )
        self.seller = Seller.objects.create(
            user=self.user,
            store_name="Plan Checkout Store",
            slug="plan-checkout-store",
        )
        self.plan = SellerPlan.objects.create(
            name="Starter",
            slug="starter",
            product_limit=50,
            media_limit=5,
            price=999,
        )

        self.client.force_login(self.user)
        response = self.client.post(
            reverse("seller_plan_checkout", kwargs={"slug": self.seller.slug}),
            {"plan_slug": "starter"},
        )

        self.seller.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.seller.plan_id, self.plan.id)

    def test_signup_plan_choices_use_live_seller_plan_prices(self):
        SellerPlan.objects.create(
            name="Starter",
            slug="starter",
            product_limit=50,
            media_limit=5,
            description="",
            price=1499,
        )

        response = self.client.get(reverse("signup"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Starter Plan - ₹1499")

    def test_seller_can_add_product_with_image_from_dashboard(self):
        user = get_user_model().objects.create_user(
            username="sellerwithimages",
            email="sellerimages@example.com",
            password="StrongPass123!",
        )
        seller = Seller.objects.create(
            user=user,
            store_name="Image Seller",
            slug="image-seller",
            plan=SellerPlan.objects.create(
                name="Starter",
                slug="starter",
                product_limit=50,
                media_limit=5,
                price=999,
            ),
        )
        category = Category.objects.create(name="Jewelry", slug="jewelry")

        image = BytesIO()
        Image.new("RGB", (200, 200), color="blue").save(image, format="PNG")
        image.seek(0)

        self.client.force_login(user)
        response = self.client.post(
            reverse("seller_add_product"),
            {
                "name": "Gold Ring",
                "category": category.id,
                "price": 1200,
                "stock_quantity": 10,
                "description": "Handmade gold ring",
                "images": SimpleUploadedFile("ring.png", image.getvalue(), content_type="image/png"),
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Products.objects.filter(name="Gold Ring", seller=seller).exists())
        self.assertTrue(seller.products.filter(name="Gold Ring").exists())


class SellerDashboardPaginationTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="selleruser",
            email="seller@example.com",
            password="StrongPass123!",
        )
        self.category = Category.objects.create(
            name="Home Decor",
            slug="home-decor",
        )
        self.seller = Seller.objects.create(
            user=self.user,
            store_name="Craft Corner",
            slug="craft-corner",
        )

        for index in range(1, 15):
            Products.objects.create(
                name=f"Product {index}",
                price=100 + index,
                stock_quantity=index,
                category=self.category,
                seller=self.seller,
                slug=f"product-{index}",
            )

        self.customer = get_user_model().objects.create_user(
            username="customer1",
            email="customer@example.com",
            password="StrongPass123!",
        )
        self.inquiry = Inquiry.objects.create(
            customer=self.customer,
            seller=self.seller,
            status=Inquiry.STATUS_NEW,
        )

    def test_dashboard_preserves_search_filters_and_uses_pagination(self):
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("seller_dashboard"),
            {"q": "customer1", "status": "new", "product_page": 2},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["search_query"], "customer1")
        self.assertEqual(response.context["status_filter"], "new")
        self.assertEqual(response.context["products"].number, 2)
        self.assertTrue(hasattr(response.context["products"], "paginator"))
        self.assertTrue(hasattr(response.context["inquiries"], "paginator"))

    def test_dashboard_supports_product_search_and_per_page_selector(self):
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("seller_dashboard"),
            {"product_q": "Product 1", "product_per_page": "20"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["product_search_query"], "Product 1")
        self.assertEqual(response.context["product_per_page"], 20)
        self.assertEqual(response.context["products"].paginator.per_page, 20)
        self.assertContains(response, 'name="product_q"')
        self.assertContains(response, 'name="product_per_page"')

    def test_seller_can_delete_product_from_dashboard(self):
        self.client.force_login(self.user)
        product = self.seller.products.first()

        response = self.client.post(
            reverse("seller_product_delete", kwargs={"slug": product.slug})
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(Products.objects.filter(pk=product.pk).exists())

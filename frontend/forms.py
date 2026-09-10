from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import ContactMessage, Products, Seller, SellerPlan
from .models.seller import ensure_default_seller_plans
from django.contrib.auth.models import User

class SignupForm(UserCreationForm):
    account_type = forms.ChoiceField(
        choices=[
            ("customer", "Customer"),
            ("seller", "Seller"),
        ],
        initial="customer",
        widget=forms.RadioSelect,
    )
    email = forms.EmailField(required=True)
    verification_code = forms.CharField(
        required=False,
        max_length=6,
        label="Email verification code",
        help_text="Enter the 6-digit code sent to your email.",
    )
    store_name = forms.CharField(required=False, max_length=200)
    owner_name = forms.CharField(required=False, max_length=200)
    phone = forms.CharField(required=False, max_length=20)
    payment_mode = forms.ChoiceField(
        choices=[
            ("cod", "Cash on Delivery"),
            ("upi", "UPI"),
            ("card", "Card / Online Payment"),
            ("bank", "Bank Transfer"),
            ("whatsapp", "WhatsApp Order"),
        ],
        initial="cod",
        required=False,
    )
    selected_plan = forms.ChoiceField(
        choices=[],
        initial="free",
        required=False,
    )

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)
        ensure_default_seller_plans()
        choices = SellerPlan.get_plan_choices()
        self.fields["selected_plan"].choices = choices
        if "selected_plan" not in self.data:
            self.initial["selected_plan"] = choices[0][0] if choices else "free"

    def clean_selected_plan(self):
        value = self.cleaned_data.get("selected_plan")
        if not value:
            return SellerPlan.get_default_plan().slug if SellerPlan.get_default_plan() else "free"
        return value

    class Meta(UserCreationForm.Meta):
        fields = [
            "account_type",
            "username",
            "email",
            "verification_code",
            "password1",
            "password2",
            "store_name",
            "owner_name",
            "phone",
            "payment_mode",
            "selected_plan",
        ]

    def clean(self):
        cleaned_data = super().clean()

        account_type = cleaned_data.get("account_type")

        # -----------------------------------------
        # SELLER REQUIRED FIELDS
        # -----------------------------------------

        if account_type == "seller":

            if not cleaned_data.get("store_name"):
                self.add_error(
                    "store_name",
                    "Store name is required for seller accounts."
                )

            if not cleaned_data.get("owner_name"):
                self.add_error(
                    "owner_name",
                    "Owner name is required for seller accounts."
                )

            if not cleaned_data.get("phone"):
                self.add_error(
                    "phone",
                    "Phone number is required for seller accounts."
                )

        # -----------------------------------------
        # EMAIL
        # -----------------------------------------

        email = (
            cleaned_data.get("email") or ""
        ).strip().lower()

        # One email = one Django account
        if email:
            email_exists = User.objects.filter(
                email__iexact=email
            ).exists()

            if email_exists:
                self.add_error(
                    "email",
                    "This email address is already registered. "
                    "Please use another email or log in."
                )

        # -----------------------------------------
        # EMAIL VERIFICATION
        # -----------------------------------------

        entered_code = (
            cleaned_data.get("verification_code") or ""
        ).strip()

        pending_data = {}

        if self.request is not None:
            pending_data = (
                self.request.session.get(
                    "pending_email_verification",
                    {}
                ) or {}
            )

        expected_email = (
            pending_data.get("email") or ""
        ).strip().lower()

        expected_code = str(
            pending_data.get("code") or ""
        ).strip()

        verified = (
            pending_data.get("verified") is True
            and expected_email == email
        )

        if email:

            if not verified:

                if not entered_code:
                    self.add_error(
                        "verification_code",
                        "Please verify your email before creating "
                        "your account."
                    )

                elif (
                    expected_email != email
                    or entered_code != expected_code
                ):
                    self.add_error(
                        "verification_code",
                        "Verification code is incorrect."
                    )

        return cleaned_data


class ContactMessageForm(forms.ModelForm):

    class Meta:
        model = ContactMessage

        fields = [
            "name",
            "email",
            "phone",
            "subject",
            "message"
        ]


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    """
    File field that properly handles multiple uploaded files.
    The actual number allowed is controlled by the seller's plan
    in the view, not here.
    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        if not data:
            if self.required:
                raise forms.ValidationError(
                    self.error_messages["required"],
                    code="required",
                )
            return []

        if isinstance(data, (list, tuple)):
            return [
                super().clean(uploaded_file, initial)
                for uploaded_file in data
            ]

        return [super().clean(data, initial)]


class ProductForm(forms.ModelForm):

    images = MultipleFileField(
        required=False,
        widget=MultipleFileInput(
            attrs={
                "multiple": True,
                "accept": "image/*",
            }
        ),
        help_text="Upload at least one product image.",
    )

    class Meta:
        model = Products
        fields = [
            "name",
            "category",
            "price",
            "stock_quantity",
            "description",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 5}),
        }

    def clean(self):
        cleaned_data = super().clean()

        images = cleaned_data.get("images") or []

        if not self.instance.pk and not images:
            self.add_error(
                "images",
                "Please upload at least one product image."
            )

        cleaned_data["images"] = images

        return cleaned_data


class SellerProfileForm(forms.ModelForm):
    class Meta:
        model = Seller
        fields = [
            "store_name",
            "owner_name",
            "plan",
            "payment_mode",
            "logo",
            "banner",
            "email",
            "phone",
            "whatsapp_number",
            "address",
            "city",
            "state",
            "website",
            "description",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 6}),
            "address": forms.Textarea(attrs={"rows": 4}),
        }
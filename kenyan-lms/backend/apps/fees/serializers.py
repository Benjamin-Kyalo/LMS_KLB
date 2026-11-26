"""Fee serializers."""
from apps.core.serializers import InstitutionCodeMixin
from rest_framework import serializers

from apps.fees.models import FeeInvoice, FeeStructure, Payment


class FeeStructureSerializer(InstitutionCodeMixin, serializers.ModelSerializer):
    term_name = serializers.CharField(source="term.name", read_only=True)
    school_class_name = serializers.CharField(source="school_class.name", read_only=True, allow_null=True)

    class Meta:
        model = FeeStructure
        fields = "__all__"
        read_only_fields = ["reference", "institution"]


class FeeInvoiceSerializer(InstitutionCodeMixin, serializers.ModelSerializer):
    learner_name = serializers.CharField(source="learner.full_name", read_only=True)
    admission_number = serializers.CharField(source="learner.admission_number", read_only=True)
    balance = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    fee_name = serializers.CharField(source="fee_structure.name", read_only=True, allow_null=True)

    class Meta:
        model = FeeInvoice
        fields = "__all__"
        read_only_fields = ["reference", "institution", "amount_paid", "status"]


class PaymentSerializer(InstitutionCodeMixin, serializers.ModelSerializer):
    invoice_reference = serializers.CharField(source="invoice.reference", read_only=True)

    class Meta:
        model = Payment
        fields = "__all__"
        read_only_fields = ["reference", "institution", "recorded_by"]

    def validate(self, attrs):
        invoice = attrs.get("invoice") or getattr(self.instance, "invoice", None)
        amount = attrs.get("amount", getattr(self.instance, "amount", None))
        if invoice and amount is not None and amount <= 0:
            raise serializers.ValidationError({"amount": "Payment must be greater than zero."})
        if invoice and invoice.status == "CANCELLED":
            raise serializers.ValidationError({"invoice": "Cannot pay a cancelled invoice."})
        return attrs

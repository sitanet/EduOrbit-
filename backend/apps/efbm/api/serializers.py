from rest_framework import serializers
from backend.apps.efbm.models import (
    FeeStructure, Invoice, InvoiceItem, Payment, PaymentAllocation, StudentWallet, WalletTransaction, StudentLedger
)

class FeeStructureSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeeStructure
        fields = ['id', 'school', 'academic_year', 'name', 'amount', 'category']


class InvoiceItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceItem
        fields = ['id', 'fee_structure', 'amount']


class InvoiceSerializer(serializers.ModelSerializer):
    items = InvoiceItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = Invoice
        fields = ['id', 'student', 'invoice_number', 'issue_date', 'due_date', 'status', 'items']


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['id', 'invoice', 'amount', 'payment_method', 'reference', 'payment_date']


class AllocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentAllocation
        fields = ['id', 'payment', 'invoice_item', 'amount']


class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentWallet
        fields = ['id', 'parent', 'balance']


class WalletTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WalletTransaction
        fields = ['id', 'wallet', 'amount', 'transaction_type', 'created_at']


class LedgerSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentLedger
        fields = ['id', 'student', 'description', 'debit_amount', 'credit_amount', 'balance_after', 'reference_id', 'created_at']

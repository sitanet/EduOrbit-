# Generated manually for Phase 8 Payment Voucher Enhancement

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('people', '0001_initial'),
        ('efbm', '0014_alter_suppliercreditnote_options_and_more'),
    ]

    operations = [
        # Add status field to SupplierPayment (new field)
        migrations.AddField(
            model_name='supplierpayment',
            name='status',
            field=models.CharField(max_length=20, choices=[('draft', 'Draft'), ('pending', 'Pending Approval'), ('approved', 'Approved'), ('processed', 'Bank Processed'), ('cancelled', 'Cancelled')], default='draft', db_index=True),
        ),
        
        # Add payment_number field to SupplierPayment (new field)
        migrations.AddField(
            model_name='supplierpayment',
            name='payment_number',
            field=models.CharField(max_length=100, unique=True, db_index=True, default='TEMP'),
            preserve_default=False,
        ),
        
        # Add new workflow fields to SupplierPayment
        migrations.AddField(
            model_name='supplierpayment',
            name='prepared_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='prepared_payments', to='people.person'),
        ),
        migrations.AddField(
            model_name='supplierpayment',
            name='approved_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='approved_payments', to='people.person'),
        ),
        migrations.AddField(
            model_name='supplierpayment',
            name='processed_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='processed_payments', to='people.person'),
        ),
        migrations.AddField(
            model_name='supplierpayment',
            name='prepared_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='supplierpayment',
            name='approved_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='supplierpayment',
            name='processed_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='supplierpayment',
            name='bank_account',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='supplier_payments', to='efbm.bankaccount'),
        ),
        migrations.AddField(
            model_name='supplierpayment',
            name='bank_reference',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
        migrations.AddField(
            model_name='supplierpayment',
            name='description',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='supplierpayment',
            name='withholding_tax_amount',
            field=models.DecimalField(decimal_places=2, default=0.00, max_digits=12),
        ),
        migrations.AddField(
            model_name='supplierpayment',
            name='net_amount',
            field=models.DecimalField(decimal_places=2, null=True, blank=True, max_digits=12),
        ),
        
        # Add new fields to PaymentVoucher
        migrations.AddField(
            model_name='paymentvoucher',
            name='prepared_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='prepared_vouchers', to='people.person'),
        ),
        migrations.AddField(
            model_name='paymentvoucher',
            name='submitted_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='submitted_vouchers', to='people.person'),
        ),
        migrations.AddField(
            model_name='paymentvoucher',
            name='approved_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='approved_vouchers', to='people.person'),
        ),
        migrations.AddField(
            model_name='paymentvoucher',
            name='rejected_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='rejected_vouchers', to='people.person'),
        ),
        migrations.AddField(
            model_name='paymentvoucher',
            name='processed_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='processed_vouchers', to='people.person'),
        ),
        migrations.AddField(
            model_name='paymentvoucher',
            name='prepared_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='paymentvoucher',
            name='submitted_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='paymentvoucher',
            name='approved_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='paymentvoucher',
            name='rejected_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='paymentvoucher',
            name='processed_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='paymentvoucher',
            name='purpose',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='paymentvoucher',
            name='beneficiary_name',
            field=models.CharField(blank=True, default='', max_length=200),
        ),
        migrations.AddField(
            model_name='paymentvoucher',
            name='beneficiary_account',
            field=models.CharField(blank=True, default='', max_length=50),
        ),
        migrations.AddField(
            model_name='paymentvoucher',
            name='beneficiary_bank',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
        migrations.AddField(
            model_name='paymentvoucher',
            name='rejection_reason',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='paymentvoucher',
            name='supporting_documents',
            field=models.TextField(blank=True, default='', help_text='List of supporting documents (invoices, receipts, etc.)'),
        ),
    ]

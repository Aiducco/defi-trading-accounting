from django.db import models as django_db_models


class AccountingWallet(django_db_models.Model):
    address = django_db_models.CharField(max_length=255, null=False)
    provider = django_db_models.PositiveSmallIntegerField(null=False)
    provider_name = django_db_models.CharField(max_length=255, null=False)

    created_at = django_db_models.DateTimeField(auto_now_add=True)
    updated_at = django_db_models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "src"
        db_table = "accounting_wallet"
        unique_together = ["address", "provider"]


class WalletPortfolio(django_db_models.Model):
    portfolio_value = django_db_models.FloatField(null=False)
    equity_value = django_db_models.FloatField(null=False)

    wallet = django_db_models.ForeignKey(
        AccountingWallet, on_delete=django_db_models.PROTECT
    )

    portfolio_date = django_db_models.DateField(auto_now=True)

    created_at = django_db_models.DateTimeField(auto_now_add=True)
    updated_at = django_db_models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "src"
        db_table = "accounting_wallet_portfolio"


class Order(django_db_models.Model):
    order_id = django_db_models.CharField(max_length=255)
    market = django_db_models.CharField(max_length=255, null=False)
    type = django_db_models.PositiveSmallIntegerField(null=False)
    type_name = django_db_models.CharField(max_length=255, null=False)
    side = django_db_models.PositiveSmallIntegerField(null=False)
    side_name = django_db_models.CharField(max_length=255, null=False)
    status = django_db_models.PositiveSmallIntegerField(null=False)
    status_name = django_db_models.CharField(max_length=255, null=False)
    original_size = django_db_models.FloatField(null=False)
    remaining_size = django_db_models.FloatField(null=False)
    order_timestamp = django_db_models.BigIntegerField(null=False)
    order_created_at = django_db_models.DateTimeField(null=False)

    wallet = django_db_models.ForeignKey(
        AccountingWallet, on_delete=django_db_models.PROTECT
    )

    created_at = django_db_models.DateTimeField(auto_now_add=True)
    updated_at = django_db_models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "src"
        db_table = "accounting_order"


class OrderFill(django_db_models.Model):
    price = django_db_models.FloatField(null=False)
    size = django_db_models.FloatField(null=False)
    fee = django_db_models.FloatField(null=False)
    closed_pnl = django_db_models.FloatField(null=False)
    side = django_db_models.PositiveSmallIntegerField(null=False)
    side_name = django_db_models.CharField(max_length=255, null=False)
    direction = django_db_models.PositiveSmallIntegerField(null=True)
    direction_name = django_db_models.CharField(max_length=255, null=True)
    position_side = django_db_models.PositiveSmallIntegerField(null=False)
    position_side_name = django_db_models.CharField(max_length=255, null=False)
    hash = django_db_models.CharField(max_length=255, null=True)
    order_fill_timestamp = django_db_models.BigIntegerField(null=False)
    order_fill_created_at = django_db_models.DateTimeField(null=False)

    order = django_db_models.ForeignKey(
        Order, on_delete=django_db_models.PROTECT, null=True, related_name="orderfills"
    )

    created_at = django_db_models.DateTimeField(auto_now_add=True)
    updated_at = django_db_models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "src"
        db_table = "accounting_order_fill"


class FundingPayment(django_db_models.Model):
    market = django_db_models.CharField(max_length=255, null=False)
    payment = django_db_models.FloatField(null=False)
    funding_rate = django_db_models.FloatField(null=False)
    position_size = django_db_models.FloatField(null=False)
    hash = django_db_models.CharField(max_length=255, null=True)
    funding_timestamp = django_db_models.BigIntegerField(null=False)
    funding_created_at = django_db_models.DateTimeField(null=False)

    wallet = django_db_models.ForeignKey(
        AccountingWallet, on_delete=django_db_models.PROTECT
    )

    created_at = django_db_models.DateTimeField(auto_now_add=True)
    updated_at = django_db_models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "src"
        db_table = "accounting_funding_payment"


class Position(django_db_models.Model):
    market = django_db_models.CharField(max_length=255, null=False)
    status = django_db_models.PositiveSmallIntegerField(null=False)
    status_name = django_db_models.CharField(max_length=255, null=False)
    side = django_db_models.PositiveSmallIntegerField(null=False)
    side_name = django_db_models.CharField(max_length=255, null=False)
    size = django_db_models.FloatField(null=False)
    remaining_size = django_db_models.FloatField(null=False)
    unrealized_pnl = django_db_models.FloatField(null=False)
    realized_pnl = django_db_models.FloatField(null=False)
    value = django_db_models.FloatField(null=False)

    wallet = django_db_models.ForeignKey(
        AccountingWallet, on_delete=django_db_models.PROTECT
    )

    position_created_at = django_db_models.DateTimeField(null=False)
    position_closed_at = django_db_models.DateTimeField(null=True)
    created_at = django_db_models.DateTimeField(auto_now_add=True)
    updated_at = django_db_models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "src"
        db_table = "accounting_trade_position"

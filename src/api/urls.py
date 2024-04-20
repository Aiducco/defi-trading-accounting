from django.urls import path

from src.api.views import accounting_management as accounting_management_views
from src.api.views import position_funding_report as position_funding_api_views
from src.api.views import trade_report as report_api_views

urlpatterns = [
    path(
        "accountant/trades/export",
        report_api_views.TradeReport.as_view(),
        name="defi-trading.trade_report",
    ),
    path(
        "accountant/fundings/export",
        position_funding_api_views.PositionFundingsReport.as_view(),
        name="defi-trading.position_fundings_report",
    ),
    path(
        "management/wallet-address",
        accounting_management_views.AccountingWallet.as_view(),
        name="defi-trading.wallet_address",
    ),
]

from __future__ import unicode_literals
import hashlib
from unittest import TestCase

from django.http import HttpResponse, HttpResponseForbidden
from mock import MagicMock, Mock

from payments.core import BasicProvider
from payments import PaymentError, PaymentStatus, RedirectNeeded

from . import ECPayProvider

VARIANT = 'ecpay'
MERCHAND_ID = '2000132'
MERCHAND_NAME = 'Shop Name'
HASH_KEY = '5294y06JbISpM5x9'
HASH_IV = 'v77hoKGq4kWxNNIS'

INPUT_POST = {
    'BankCode': '005',
    'ExpireDate': '2018/02/04',
    'MerchantID': '2000132',
    'MerchantTradeNo': '398126F08AC383BC524F',
    'PaymentType': 'ATM_LAND',
    'RtnCode': '2',
    'RtnMsg': 'Get VirtualAccount Succeeded',
    'TradeAmt': '1000',
    'TradeDate': '2018/02/01 22:53:26',
    'TradeNo': '1802012253184197',
    'vAccount': '5219803543954460',
    'StoreID': '',
    'CustomField1': '',
    'CustomField2': '',
    'CustomField3': '',
    'CustomField4': '',
    'CheckMacValue': '80A9971638C8CEBA4CFE7A21673E508B0882239CBAE1A11EBC646DBCFB24E4A6'
}


class Payment(Mock):
    id = 1
    variant = VARIANT
    currency = 'NTD'
    total = 1000
    status = PaymentStatus.WAITING

    def get_process_url(self):
        return 'http://example.com'

    def get_failure_url(self):
        return 'http://cancel.com'

    def get_success_url(self):
        return 'http://success.com'

    def change_status(self, status):
        self.status = status


class TestECPayProvider(TestCase):

    def setUp(self):
        self.payment = Payment()

    def test_get_hidden_fields(self):
        """ECPayProvider.get_hidden_fields() returns a dictionary"""
        provider = ECPayProvider(
            merchand_id=MERCHAND_ID,
            merchand_name=MERCHAND_NAME,
            hash_key=HASH_KEY,
            hash_iv=HASH_IV)
        self.assertEqual(type(provider.get_hidden_fields(self.payment)), dict)

    def test_process_data_payment_input(self):
        """ECPayProvider.process_data() returns a correct HTTP response"""
        request = MagicMock()
        request.POST = INPUT_POST
        provider = ECPayProvider(
            merchand_id=MERCHAND_ID,
            merchand_name=MERCHAND_NAME,
            hash_key=HASH_KEY,
            hash_iv=HASH_IV)
        response = provider.process_data(self.payment, request)
        self.assertEqual(type(response), HttpResponse)
        self.assertEqual(self.payment.status, PaymentStatus.INPUT)
        self.assertEqual(self.payment.message, INPUT_POST['RtnMsg'])
        self.assertEqual(self.payment.transaction_id, INPUT_POST['TradeNo'])

    def test_incorrect_process_data(self):
        """ECPayProvider.process_data() checks signature (CheckMacValue)"""
        data = dict(INPUT_POST)
        data.update({'TradeAmt': 10000})
        request = MagicMock()
        request.POST = data
        provider = ECPayProvider(
            merchand_id=MERCHAND_ID,
            merchand_name=MERCHAND_NAME,
            hash_key=HASH_KEY,
            hash_iv=HASH_IV)
        response = provider.process_data(self.payment, request)
        self.assertEqual(type(response), HttpResponseForbidden)

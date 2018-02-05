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
    'Barcode1': '0702126EA',
    'Barcode2': '3453011203193999',
    'Barcode3': '020589000001000',
    'ExpireDate': '2018/02/12 16:55:38',
    'MerchantID': '2000132',
    'MerchantTradeNo': '944692A47464BFE91931',
    'PaymentNo': '',
    'PaymentType': 'BARCODE_BARCODE',
    'RtnCode': '10100073',
    'RtnMsg': 'Get CVS Code Succeeded.',
    'TradeAmt': '1000',
    'TradeDate': '2018/02/05 16:55:38',
    'TradeNo': '1802051655256142',
    'StoreID': '',
    'CustomField1': '',
    'CustomField2': '',
    'CustomField3': '',
    'CustomField4': '',
    'CheckMacValue': '847264D1CF961B2022549427CF72A900DD384A7061F24B59A9E5144CE6AA2FE3'
}

BARCODE_POST = {
    'Barcode1': '0702126EA',
    'Barcode2': '3453011790037935',
    'Barcode3': '020531000001000',
    'ExpireDate': '2018/02/12 17:06:50',
    'MerchantID': '2000132',
    'MerchantTradeNo': 'CC2CCDB330C48A68888A',
    'PaymentNo': '',
    'PaymentType': 'BARCODE_BARCODE',
    'RtnCode': '10100073',
    'RtnMsg': 'Get CVS Code Succeeded.',
    'TradeAmt': '1000',
    'TradeDate': '2018/02/05 17:06:50',
    'TradeNo': '1802051706426163',
    'StoreID': '',
    'CustomField1': '',
    'CustomField2': '',
    'CustomField3': '',
    'CustomField4': '',
    'CheckMacValue': '543A0641562D81EABE301C70D59B9613E0F2758D545F526C0877840FF4C3F9E4'
}

SUCCESS_POST = {
    'CustomField1': '',
    'CustomField2': '',
    'CustomField3': '',
    'CustomField4': '',
    'MerchantID': '2000132',
    'MerchantTradeNo': '81E48579D5B631BA4DF0',
    'PaymentDate': '2018/02/05 16:52:01',
    'PaymentType': 'WebATM_LAND',
    'PaymentTypeChargeFee': '1',
    'RtnCode': '1',
    'RtnMsg': '交易成功',
    'SimulatePaid': '0',
    'StoreID': '',
    'TradeAmt': '1000',
    'TradeDate': '2018/02/05 16:51:46',
    'TradeNo': '1802051651466135',
    'CheckMacValue': 'F1896F208081BC236C53DC0CC246C1B2EF712C33A618F96F47006A3B2B6780C0'
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
        """ ECPayProvider.process_data() returns
            a correct HTTP response when payment initiated """
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
        # self.assertEqual(self.payment.message, INPUT_POST['RtnMsg'])
        # self.assertEqual(self.payment.transaction_id, INPUT_POST['TradeNo'])

    def test_process_data_payment_input_barcode(self):
        """ ECPayProvider.process_data() returns
            a correct HTTP response when payment initiated """
        request = MagicMock()
        request.POST = BARCODE_POST
        provider = ECPayProvider(
            merchand_id=MERCHAND_ID,
            merchand_name=MERCHAND_NAME,
            hash_key=HASH_KEY,
            hash_iv=HASH_IV)
        response = provider.process_data(self.payment, request)
        self.assertEqual(type(response), HttpResponse)
        self.assertEqual(self.payment.status, PaymentStatus.INPUT)

    def test_process_data_payment_success(self):
        """ ECPayProvider.process_data() returns
            a correct HTTP response when payment succeful """
        request = MagicMock()
        request.POST = SUCCESS_POST
        provider = ECPayProvider(
            merchand_id=MERCHAND_ID,
            merchand_name=MERCHAND_NAME,
            hash_key=HASH_KEY,
            hash_iv=HASH_IV)
        response = provider.process_data(self.payment, request)
        self.assertEqual(type(response), HttpResponse)
        self.assertEqual(self.payment.status, PaymentStatus.CONFIRMED)
        # self.assertEqual(self.payment.message, INPUT_POST['RtnMsg'])
        # self.assertEqual(self.payment.transaction_id, INPUT_POST['TradeNo'])

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

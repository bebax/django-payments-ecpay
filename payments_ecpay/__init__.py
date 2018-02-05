from __future__ import unicode_literals
import hashlib
import datetime
import time
import json

try:
    # For Python 3.0 and later
    from urllib.parse import urlencode, quote, quote_plus
except ImportError:
    # Fall back to Python 2's urllib2
    from urllib import urlencode
    from urllib import quote, quote_plus

from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import ugettext_lazy as _
from django.http import HttpResponse, HttpResponseForbidden

from payments.core import BasicProvider
from payments import PaymentError, PaymentStatus, RedirectNeeded

REPLACEMENTS = {
    '-': '%2d',
    '_': '%5f',
    '.': '%2e',
    '!': '%21',
    '*': '%2a',
    '(': '%28',
    ')': '%29',
}


def urlencodeReplacement(string, check_out):
    ### UrlEncode function from ECPay's documentation ###
    replacement_dict = REPLACEMENTS
    if check_out:
        # double encode url symbols '/' and ':'
        replacement_dict.update({'%2f': '%252f', '%3a': '%253a'})

    for value, replacement in replacement_dict.items():
        string = string.replace(replacement, value)

    return string


class ECPayProvider(BasicProvider):
    ALL = 'ALL'
    ATM = 'ATM'
    WEB_ATM = 'WebATM'
    CVS = 'CVS'
    BARCODE = 'BARCODE'
    CREDIT = 'Credit'
    ANROID_PAY = 'AndroidPay'

    def __init__(self, *args, **kwargs):
        self.merchand_id = kwargs.pop('merchand_id')
        self.merchand_name = kwargs.pop('merchand_name', 'Description')
        self.hash_key = kwargs.pop('hash_key')
        self.hash_iv = kwargs.pop('hash_iv')
        self.expiration_days = kwargs.pop('expiration_days', 3)
        self.choose_payments = kwargs.pop('payment_types', self.ALL)
        self.excluded_payments = kwargs.pop('excluded_payments', '')
        self.client_back_url = kwargs.pop('client_back_url', '')
        self.endpoint = kwargs.pop(
            'endpoint',
            'https://payment-stage.ecpay.com.tw/Cashier/AioCheckOut/V5')
        super(ECPayProvider, self).__init__(*args, **kwargs)

        if not self._capture:
            raise ImproperlyConfigured(
                _('ECPay does not support pre-authorization.'))

    def _getSignature(self, data, check_out=False):
        # ECPay's payment expects a check mac value of the sorted
        # transaction data sandwiched between the HashKey and HashIV
        sorted_data = sorted(data.items())
        sorted_data.insert(0, ('HashKey', self.hash_key))
        sorted_data.append(('HashIV', self.hash_iv))

        request = urlencodeReplacement(
            quote(urlencode(sorted_data), '+%').lower(),
            check_out)

        result = hashlib.sha256(
            request.encode('utf-8')).hexdigest().upper()

        return result

    def get_hidden_fields(self, payment):
        return_url = self.get_return_url(payment)

        # merchand_trade_no is allowed to be max 20 characters
        merchand_trade_no = hashlib.sha256((str(
            datetime.datetime.now())).encode('utf-8')).hexdigest().upper()[:20]
        # date format is defined in ECPay's documentation
        date = time.strftime('%Y/%m/%d %H:%M:%S', time.localtime(time.time()))

        data = {
            'MerchantTradeNo': merchand_trade_no,
            'MerchantTradeDate': date,
            'TotalAmount':  "%.0f" % (payment.total,),
            'TradeDesc': self.merchand_name,
            'ItemName': payment.description or 'Default Item Name',
            'ReturnURL': return_url,
            'PaymentInfoURL': return_url,
            'ChoosePayment': self.choose_payments,
            'IgnorePayment': '#'.join(self.excluded_payments),
            'ClientBackURL': self.client_back_url,
            'ExpireDate': self.expiration_days,
            'MerchantID': self.merchand_id,
            'InvoiceMark': 'N',
            'EncryptType': '1',
            'PaymentType': 'aio'
        }

        data['CheckMacValue'] = self._getSignature(data, True)

        return data

    def get_action(self, payment):
        return self.endpoint

    def process_data(self, payment, request):
        data = request.POST

        if type(data) != dict:
            data = data.dict()

        check_mac_value = data.pop('CheckMacValue', None)

        mac_value = self._getSignature(data)

        if mac_value == check_mac_value:
            return_code = data.get('RtnCode', -1)

            payment.extra_data = data
            payment.message = data.get('RtnMsg', '')
            payment.transaction_id = data.get('TradeNo', '')

            # Return code 2 or 10100073 is returned when the user
            # completed the first step of a payment procedure, e.g.
            # generating the barcodes for payment at convenince stores
            if return_code in ['2', '10100073']:
                payment.change_status(PaymentStatus.INPUT)
            # Code 1 is returned when the payment is completed
            elif return_code in ['1']:
                payment.captured_amount = data.get('TradeAmt', 0)
                payment.change_status(PaymentStatus.CONFIRMED)
            # Error when unknown code is return but with a valid signature
            elif return_code:
                payment.change_status(PaymentStatus.ERROR)

            payment.save()
            return HttpResponse('OK')
        else:
            return HttpResponseForbidden('FAILED')

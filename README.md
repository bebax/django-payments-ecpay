django-payments-ecpay
=======================

A `django-payments <https://github.com/mirumee/django-payments>` backend for the ECPay (Taiwan) payment gateway.

Reference documentation can be found at the following address:
https://www.ecpay.com.tw/Content/files/ecpay_011.pdf

Parameters
----------

* **merchand_id** : Merchant Identification number assigned by ECPay (required).
* **hash_key** : Hash Key assigned by ECPay (required).
* **hash_iv** : Hash IV assigned by ECPay (required).
* **endpoint** (default='https://payment-stage.ecpay.com.tw/Cashier/AioCheckOut/V5') : The ECPay payment gateway endpoint. Use 'https://payment.ecpay.com.tw/Cashier/AioCheckOut/V5' for the production environment (required).

* **merchand_name** : Merchant Identification number assigned by ECPay (optional).
* **expiration_days** : Validity of payment process. Between 1 to 60 days, defaults to 3 days. (optional).
* **client_back_url** : URL to which the customer is redirect to after payment (optional).
* **choose_payments** : Default payment type. Can be one of 'ALL', 'ATM', 'WebATM', 'CVS', 'BARCODE', 'Credit', 'AndroidPay' and defaults to 'ALL' (optional).
* **excluded_payments** : Array of excluded payments options. Options are 'ATM', 'WebATM', 'CVS', 'BARCODE', 'Credit', 'AndroidPay' (optional).


Usage example
----------

Add the following lines to your configuration in `settings.py`:

```python
  PAYMENT_VARIANTS = {
      'default': ('payments_ecpay.ECPayProvider', {
        'merchand_id': '2000132',
        'merchand_name': 'Shop Name',
        'hash_key': '5294y06JbISpM5x9',
        'hash_iv': 'v77hoKGq4kWxNNIS',
        'expiration_days': 3,
        'excluded_payments': ['Credit', 'AndroidPay'],
        'endpoint': 'https://payment.ecpay.com.tw/Cashier/AioCheckOut/V5'}),
  }
```
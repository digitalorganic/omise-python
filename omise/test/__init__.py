import sys
import unittest
import mock


try:
    import json
except ImportError:
    import simplejson as json


try:
    basestring
except NameError:
    basestring = str


if sys.version_info[0] == 2:
    def next(o, **kw):
        return o.next(**kw)


class _MockResponse(object):

    def __init__(self, content):
        self._content = content

    def json(self):
        return json.loads(self._content)


class _RequestAssertable(object):

    def mockResponse(self, api_call, response):
        api_call.return_value = response = _MockResponse(response)
        return response

    def assertRequest(self, api_call, url, data=None):
        if data is None:
            data = {}
        api_call.assert_called_with(
            url,
            data=data,
            headers=mock.ANY,
            auth=mock.ANY,
            verify=mock.ANY)


class RequestTest(_RequestAssertable, unittest.TestCase):

    def _getTargetClass(self):
        from .. import Request
        return Request

    def test_init(self):
        class_ = self._getTargetClass()
        request = class_('skey_test', 'https://api.omise.co')
        self.assertEqual(request.api_key, 'skey_test')
        self.assertEqual(request.api_base, 'https://api.omise.co')

    def test_init_no_api_key(self):
        class_ = self._getTargetClass()
        def _func():
            class_(None, 'https://api.omise.co')
        self.assertRaises(AttributeError, _func)

    @mock.patch('requests.get')
    def test_send(self, api_call):
        class_ = self._getTargetClass()
        request = class_('skey_test', 'https://api.omise.co')
        self.mockResponse(api_call, '{"ping":"pong"}')
        self.assertEqual(request.send('get', 'ping'), {'ping': 'pong'})
        self.assertRequest(api_call, 'https://api.omise.co/ping')

    @mock.patch('requests.get')
    def test_send_tuple_url(self, api_call):
        class_ = self._getTargetClass()
        request = class_('skey_test', 'https://api.omise.co')
        self.mockResponse(api_call, '{"ping":"pong"}')
        self.assertEqual(request.send('get', ('ping', 1)), {'ping': 'pong'})
        self.assertRequest(api_call, 'https://api.omise.co/ping/1')

    @mock.patch('requests.post')
    def test_send_post(self, api_call):
        class_ = self._getTargetClass()
        request = class_('skey_test', 'https://api.omise.co')
        params = {'test': 'request'}
        self.mockResponse(api_call, '{"ping":"pong"}')
        self.assertEqual(request.send('post', 'ping', params), {'ping': 'pong'})
        self.assertRequest(api_call, 'https://api.omise.co/ping', params)


class _ResourceMixin(_RequestAssertable, unittest.TestCase):

    def setUp(self):
        self._secret_mocker = mock.patch('omise.api_secret', 'skey_test')
        self._public_mocker = mock.patch('omise.api_public', 'pkey_test')
        self._secret_mocker.start()
        self._public_mocker.start()

    def tearDown(self):
        self._secret_mocker.stop()
        self._public_mocker.stop()

    def _getTargetClass(self):
        from .. import Base
        return Base

    def test_from_data(self):
        class_ = self._getTargetClass()
        instance = class_.from_data({'id': 'tst_data', 'description': 'foo'})
        self.assertEqual(instance.id, 'tst_data')
        self.assertEqual(instance.description, 'foo')
        self.assertEqual(instance.changes, {})

    def test_repr(self):
        class_ = self._getTargetClass()
        instance = class_.from_data({'id': 'tst_data'})
        self.assertEqual(
            repr(instance),
            "<%s id='%s' at %s>" % (
                class_.__name__,
                'tst_data',
                hex(id(instance)),
            )
        )

    def test_repr_without_id(self):
        class_ = self._getTargetClass()
        instance = class_.from_data({})
        self.assertEqual(
            repr(instance),
            "<%s at %s>" % (
                class_.__name__,
                hex(id(instance)),
            )
        )

    def test_changes(self):
        class_ = self._getTargetClass()
        instance = class_.from_data({'id': 'tst_data', 'description': 'foo'})
        instance.description = 'foobar'
        instance.email = 'foo@example.com'
        self.assertEqual(instance.changes, {
            'description': 'foobar',
            'email': 'foo@example.com',
        })


class AccountTest(_ResourceMixin):

    def _getTargetClass(self):
        from .. import Account
        return Account

    @mock.patch('requests.get')
    def test_retrieve(self, api_call):
        class_ = self._getTargetClass()
        self.mockResponse(api_call, """{
            "object": "account",
            "id": "acct_test",
            "email": null,
            "created": "2014-10-20T08:21:42Z"
        }""")

        account = class_.retrieve()
        self.assertTrue(isinstance(account, class_))
        self.assertEqual(account.id, 'acct_test')
        self.assertEqual(account.created, '2014-10-20T08:21:42Z')
        self.assertRequest(api_call, 'https://api.omise.co/account')

        self.mockResponse(api_call, """{
            "object": "account",
            "id": "acct_foo",
            "email": null,
            "created": "2014-10-20T08:21:42Z"
        }""")

        account.reload()
        self.assertEqual(account.id, 'acct_foo')
        self.assertRequest(api_call, 'https://api.omise.co/account')


class BalanceTest(_ResourceMixin):

    def _getTargetClass(self):
        from .. import Balance
        return Balance

    @mock.patch('requests.get')
    def test_retrieve(self, api_call):
        class_ = self._getTargetClass()
        self.mockResponse(api_call, """{
            "object": "balance",
            "livemode": false,
            "available": 0,
            "total": 0,
            "currency": "thb"
        }""")

        balance = class_.retrieve()
        self.assertTrue(isinstance(balance, class_))
        self.assertEqual(balance.available, 0)
        self.assertEqual(balance.currency, 'thb')
        self.assertEqual(balance.total, 0)
        self.assertRequest(api_call, 'https://api.omise.co/balance')

        self.mockResponse(api_call, """{
            "object": "balance",
            "livemode": false,
            "available": 4294967295,
            "total": 0,
            "currency": "thb"
        }""")

        balance.reload()
        self.assertEqual(balance.available, 4294967295)
        self.assertRequest(api_call, 'https://api.omise.co/balance')


class TokenTest(_ResourceMixin):

    def _getTargetClass(self):
        from .. import Token
        return Token

    def _getCardClass(self):
        from .. import Card
        return Card

    @mock.patch('requests.post')
    def test_create(self, api_call):
        class_ = self._getTargetClass()
        card_class_ = self._getCardClass()
        self.mockResponse(api_call, """{
            "object": "token",
            "id": "tokn_test",
            "livemode": false,
            "location": "/tokens/tokn_test",
            "used": false,
            "card": {
                "object": "card",
                "id": "card_test",
                "livemode": false,
                "country": "th",
                "city": "Bangkok",
                "postal_code": "10320",
                "financing": "credit",
                "last_digits": "4242",
                "brand": "Visa",
                "expiration_month": 10,
                "expiration_year": 2018,
                "fingerprint": "098f6bcd4621d373cade4e832627b4f6",
                "name": "Somchai Prasert",
                "created": "2014-10-20T09:41:56Z"
            },
            "created": "2014-10-20T09:41:56Z"
        }""")

        token = class_.create(
            name='Somchai Prasert',
            number='4242424242424242',
            expiration_month=10,
            expiration_year=2018,
            city='Bangkok',
            postal_code='10320',
            security_code=123
        )

        self.assertTrue(isinstance(token, class_))
        self.assertTrue(isinstance(token.card, card_class_))
        self.assertEqual(token.id, 'tokn_test')
        self.assertEqual(token.card.id, 'card_test')
        self.assertEqual(token.card.last_digits, '4242')
        self.assertRequest(api_call, 'https://vault.omise.co/tokens', {
            'card[name]': 'Somchai Prasert',
            'card[number]': '4242424242424242',
            'card[expiration_month]': 10,
            'card[expiration_year]': 2018,
            'card[city]': 'Bangkok',
            'card[postal_code]': '10320',
            'card[security_code]': 123
        })

    @mock.patch('requests.get')
    def test_retrieve(self, api_call):
        class_ = self._getTargetClass()
        card_class_ = self._getCardClass()
        self.mockResponse(api_call, """{
            "object": "token",
            "id": "tokn_test",
            "livemode": false,
            "location": "/tokens/tokn_test",
            "used": false,
            "card": {
                "object": "card",
                "id": "card_test",
                "livemode": false,
                "country": "th",
                "city": "Bangkok",
                "postal_code": "10320",
                "financing": "credit",
                "last_digits": "4242",
                "brand": "Visa",
                "expiration_month": 10,
                "expiration_year": 2018,
                "fingerprint": "098f6bcd4621d373cade4e832627b4f6",
                "name": "Somchai Prasert",
                "created": "2014-10-20T09:41:56Z"
            },
            "created": "2014-10-20T09:41:56Z"
        }""")

        token = class_.retrieve('tokn_test')
        self.assertTrue(isinstance(token, class_))
        self.assertTrue(isinstance(token.card, card_class_))
        self.assertFalse(token.used)
        self.assertEqual(token.id, 'tokn_test')
        self.assertEqual(token.card.id, 'card_test')
        self.assertEqual(token.card.last_digits, '4242')
        self.assertRequest(api_call, 'https://vault.omise.co/tokens/tokn_test')

        self.mockResponse(api_call, """{
            "object": "token",
            "id": "tokn_test",
            "livemode": false,
            "location": "/tokens/tokn_test",
            "used": true,
            "card": {
                "object": "card",
                "id": "card_test",
                "livemode": false,
                "country": "th",
                "city": "Bangkok",
                "postal_code": "10320",
                "financing": "credit",
                "last_digits": "4242",
                "brand": "Visa",
                "expiration_month": 10,
                "expiration_year": 2018,
                "fingerprint": "098f6bcd4621d373cade4e832627b4f6",
                "name": "Somchai Prasert",
                "created": "2014-10-20T09:41:56Z"
            },
            "created": "2014-10-20T09:41:56Z"
        }""")

        token.reload()
        self.assertEqual(token.id, 'tokn_test')
        self.assertTrue(token.used)
        self.assertRequest(api_call, 'https://api.omise.co/tokens/tokn_test')

class CardTest(_ResourceMixin):

    def _getTargetClass(self):
        from .. import Card
        return Card

    def _makeOne(self):
        return self._getTargetClass().from_data({
            'city': 'Bangkok',
            'financing': '',
            'object': 'card',
            'expiration_year': 2016,
            'last_digits': '4242',
            'created': '2014-10-21T04:04:12Z',
            'country': '',
            'brand': 'Visa',
            'livemode': False,
            'expiration_month': 10,
            'postal_code': '10320',
            'location': '/customers/cust_test/cards/card_test',
            'fingerprint': '098f6bcd4621d373cade4e832627b4f6',
            'id': 'card_test',
            'name': 'Somchai Prasert'
        })

    @mock.patch('requests.get')
    def test_reload(self, api_call):
        card = self._makeOne()
        class_ = self._getTargetClass()

        self.assertTrue(isinstance(card, class_))
        self.assertEqual(card.id, 'card_test')
        self.assertEqual(card.name, 'Somchai Prasert')

        self.mockResponse(api_call, """{
            "object": "card",
            "id": "card_test",
            "livemode": false,
            "location": "/customers/cust_test/cards/card_test",
            "country": "",
            "city": "Bangkok",
            "postal_code": "10310",
            "financing": "",
            "last_digits": "4242",
            "brand": "Visa",
            "expiration_month": 12,
            "expiration_year": 2018,
            "fingerprint": "098f6bcd4621d373cade4e832627b4f6",
            "name": "S. Prasert",
            "created": "2014-10-21T04:04:12Z"
        }""")

        card.reload()
        self.assertEqual(card.id, 'card_test')
        self.assertEqual(card.name, 'S. Prasert')
        self.assertRequest(
            api_call,
            'https://api.omise.co/customers/cust_test/cards/card_test'
        )

    @mock.patch('requests.patch')
    def test_update(self, api_call):
        card = self._makeOne()
        class_ = self._getTargetClass()
        self.mockResponse(api_call, """{
            "object": "card",
            "id": "card_test",
            "livemode": false,
            "location": "/customers/cust_test/cards/card_test",
            "country": "",
            "city": "Bangkok",
            "postal_code": "10310",
            "financing": "",
            "last_digits": "4242",
            "brand": "Visa",
            "expiration_month": 12,
            "expiration_year": 2018,
            "fingerprint": "098f6bcd4621d373cade4e832627b4f6",
            "name": "Example User",
            "created": "2014-10-21T04:04:12Z"
        }""")

        self.assertTrue(isinstance(card, class_))
        self.assertEqual(card.name, 'Somchai Prasert')
        self.assertEqual(card.expiration_month, 10)
        self.assertEqual(card.expiration_year, 2016)
        card.name = 'Example User'
        card.expiration_month = 12
        card.expiration_year = 2018
        card.update()

        self.assertEqual(card.name, 'Example User')
        self.assertEqual(card.expiration_month, 12)
        self.assertEqual(card.expiration_year, 2018)
        self.assertRequest(
            api_call,
            'https://api.omise.co/customers/cust_test/cards/card_test',
            {
                'name': 'Example User',
                'expiration_month': 12,
                'expiration_year': 2018,
            }
        )

    @mock.patch('requests.delete')
    def test_destroy(self, api_call):
        card = self._makeOne()
        class_ = self._getTargetClass()
        self.mockResponse(api_call, """{
            "object": "card",
            "id": "card_test",
            "livemode": false,
            "deleted": true
        }""")

        self.assertTrue(isinstance(card, class_))
        self.assertEqual(card.name, 'Somchai Prasert')

        card.destroy()
        self.assertTrue(card.destroyed)
        self.assertRequest(
            api_call,
            'https://api.omise.co/customers/cust_test/cards/card_test'
        )


class ChargeTest(_ResourceMixin):

    def _getTargetClass(self):
        from .. import Charge
        return Charge

    def _getCardClass(self):
        from .. import Card
        return Card

    def _makeOne(self):
        return self._getTargetClass().from_data({
            'card': {
                'city': 'Bangkok',
                'financing': 'credit',
                'object': 'card',
                'expiration_year': 2018,
                'last_digits': '4242',
                'created': '2014-10-20T09:41:56Z',
                'country': 'th',
                'brand': 'Visa',
                'livemode': False,
                'expiration_month': 10,
                'postal_code': '10320',
                'fingerprint': '098f6bcd4621d373cade4e832627b4f6',
                'id': 'card_test',
                'name': 'Somchai Prasert'
            },
            'capture': False,
            'object': 'charge',
            'description': 'Order-384',
            'reference': '9qt1b3n635uv6plypp2spzkpe',
            'created': '2014-10-21T11:12:28Z',
            'ip': '127.0.0.1',
            'livemode': False,
            'authorize_uri': 'https://www.example.com/payments/test/authorize',
            'currency': 'thb',
            'amount': 100000,
            'transaction': None,
            'location': '/charges/chrg_test',
            'return_uri': 'https://www.example.com/',
            'customer': None,
            'id': 'chrg_test',
            'captured': False,
            'authorized': True
        })

    @mock.patch('requests.post')
    def test_create(self, api_call):
        class_ = self._getTargetClass()
        card_class_ = self._getCardClass()
        self.mockResponse(api_call, """{
            "object": "charge",
            "id": "chrg_test",
            "livemode": false,
            "location": "/charges/chrg_test",
            "amount": 100000,
            "currency": "thb",
            "description": "Order-384",
            "capture": false,
            "authorized": false,
            "captured": false,
            "transaction": null,
            "return_uri": "https://www.example.com/",
            "reference": "9qt1b3n635uv6plypp2spzkpe",
            "authorize_uri": "https://www.example.com/payments/test/authorize",
            "card": {
                "object": "card",
                "id": "card_test",
                "livemode": false,
                "country": "th",
                "city": "Bangkok",
                "postal_code": "10320",
                "financing": "credit",
                "last_digits": "4242",
                "brand": "Visa",
                "expiration_month": 10,
                "expiration_year": 2018,
                "fingerprint": "098f6bcd4621d373cade4e832627b4f6",
                "name": "Somchai Prasert",
                "created": "2014-10-20T09:41:56Z"
            },
            "customer": null,
            "ip": "127.0.0.1",
            "created": "2014-10-21T11:12:28Z"
        }""")

        charge = class_.create(
            return_uri='https://www.example.com/',
            amount=100000,
            currency='thb',
            description='Order-384',
            ip='127.0.0.1',
            card='tokn_test',
        )

        self.assertTrue(isinstance(charge, class_))
        self.assertTrue(isinstance(charge.card, card_class_))
        self.assertEqual(charge.id, 'chrg_test')
        self.assertEqual(charge.return_uri, 'https://www.example.com/')
        self.assertEqual(charge.amount, 100000)
        self.assertEqual(charge.currency, 'thb')
        self.assertEqual(charge.description, 'Order-384')
        self.assertEqual(charge.ip, '127.0.0.1')
        self.assertEqual(charge.card.id, 'card_test')
        self.assertEqual(charge.card.last_digits, '4242')
        self.assertRequest(
            api_call,
            'https://api.omise.co/charges',
            {
                'return_uri': 'https://www.example.com/',
                'amount': 100000,
                'currency': 'thb',
                'description': 'Order-384',
                'ip': '127.0.0.1',
                'card': 'tokn_test',
            }
        )

    @mock.patch('requests.get')
    def test_retrieve(self, api_call):
        class_ = self._getTargetClass()
        card_class_ = self._getCardClass()
        self.mockResponse(api_call, """{
            "object": "charge",
            "id": "chrg_test",
            "livemode": false,
            "location": "/charges/chrg_test",
            "amount": 100000,
            "currency": "thb",
            "description": "Order-384",
            "capture": false,
            "authorized": true,
            "captured": false,
            "transaction": null,
            "return_uri": "https://www.example.com/",
            "reference": "9qt1b3n635uv6plypp2spzkpe",
            "authorize_uri": "https://www.example.com/payments/test/authorize",
            "card": {
                "object": "card",
                "id": "card_test",
                "livemode": false,
                "country": "th",
                "city": "Bangkok",
                "postal_code": "10320",
                "financing": "credit",
                "last_digits": "4242",
                "brand": "Visa",
                "expiration_month": 10,
                "expiration_year": 2018,
                "fingerprint": "098f6bcd4621d373cade4e832627b4f6",
                "name": "Somchai Prasert",
                "created": "2014-10-20T09:41:56Z"
            },
            "customer": null,
            "ip": "127.0.0.1",
            "created": "2014-10-21T11:12:28Z"
        }""")

        charge = class_.retrieve('chrg_test')
        self.assertTrue(isinstance(charge, class_))
        self.assertTrue(isinstance(charge.card, card_class_))
        self.assertEqual(charge.id, 'chrg_test')
        self.assertEqual(charge.return_uri, 'https://www.example.com/')
        self.assertEqual(charge.amount, 100000)
        self.assertEqual(charge.currency, 'thb')
        self.assertEqual(charge.description, 'Order-384')
        self.assertEqual(charge.ip, '127.0.0.1')
        self.assertEqual(charge.card.id, 'card_test')
        self.assertEqual(charge.card.last_digits, '4242')
        self.assertRequest(api_call, 'https://api.omise.co/charges/chrg_test')

        self.mockResponse(api_call, """{
            "object": "charge",
            "id": "chrg_test",
            "livemode": false,
            "location": "/charges/chrg_test",
            "amount": 120000,
            "currency": "thb",
            "description": "Order-384",
            "capture": false,
            "authorized": true,
            "captured": false,
            "transaction": null,
            "return_uri": "https://www.example.com/",
            "reference": "9qt1b3n635uv6plypp2spzkpe",
            "authorize_uri": "https://www.example.com/payments/test/authorize",
            "card": {
                "object": "card",
                "id": "card_test",
                "livemode": false,
                "country": "th",
                "city": "Bangkok",
                "postal_code": "10320",
                "financing": "credit",
                "last_digits": "4242",
                "brand": "Visa",
                "expiration_month": 10,
                "expiration_year": 2018,
                "fingerprint": "098f6bcd4621d373cade4e832627b4f6",
                "name": "Somchai Prasert",
                "created": "2014-10-20T09:41:56Z"
            },
            "customer": null,
            "ip": "127.0.0.1",
            "created": "2014-10-21T11:12:28Z"
        }""")

        charge.reload()
        self.assertEqual(charge.amount, 120000)
        self.assertEqual(charge.currency, 'thb')
        self.assertRequest(api_call, 'https://api.omise.co/charges/chrg_test')

    @mock.patch('requests.patch')
    def test_update(self, api_call):
        charge = self._makeOne()
        class_ = self._getTargetClass()
        self.mockResponse(api_call, """{
            "object": "charge",
            "id": "chrg_test",
            "livemode": false,
            "location": "/charges/chrg_test",
            "amount": 100000,
            "currency": "thb",
            "description": "New description",
            "capture": false,
            "authorized": true,
            "captured": false,
            "transaction": null,
            "return_uri": "https://www.example.com/",
            "reference": "9qt1b3n635uv6plypp2spzkpe",
            "authorize_uri": "https://www.example.com/payments/test/authorize",
            "card": {
                "object": "card",
                "id": "card_test",
                "livemode": false,
                "country": "th",
                "city": "Bangkok",
                "postal_code": "10320",
                "financing": "credit",
                "last_digits": "4242",
                "brand": "Visa",
                "expiration_month": 10,
                "expiration_year": 2018,
                "fingerprint": "098f6bcd4621d373cade4e832627b4f6",
                "name": "Somchai Prasert",
                "created": "2014-10-20T09:41:56Z"
            },
            "customer": null,
            "ip": "127.0.0.1",
            "created": "2014-10-21T11:12:28Z"
        }""")

        self.assertTrue(isinstance(charge, class_))
        self.assertEqual(charge.description, 'Order-384')
        charge.description = 'New description'
        charge.update()

        self.assertEqual(charge.description, 'New description')
        self.assertRequest(
            api_call,
            'https://api.omise.co/charges/chrg_test',
            {'description': 'New description'}
        )

    @mock.patch('requests.post')
    def test_capture(self, api_call):
        charge = self._makeOne()
        class_ = self._getTargetClass()
        self.mockResponse(api_call, """{
            "object": "charge",
            "id": "chrg_test",
            "livemode": false,
            "location": "/charges/chrg_test",
            "amount": 100000,
            "currency": "thb",
            "description": "New description",
            "capture": false,
            "authorized": true,
            "captured": true,
            "transaction": null,
            "return_uri": "https://www.example.com/",
            "reference": "9qt1b3n635uv6plypp2spzkpe",
            "authorize_uri": "https://www.example.com/payments/test/authorize",
            "card": {
                "object": "card",
                "id": "card_test",
                "livemode": false,
                "country": "th",
                "city": "Bangkok",
                "postal_code": "10320",
                "financing": "credit",
                "last_digits": "4242",
                "brand": "Visa",
                "expiration_month": 10,
                "expiration_year": 2018,
                "fingerprint": "098f6bcd4621d373cade4e832627b4f6",
                "name": "Somchai Prasert",
                "created": "2014-10-20T09:41:56Z"
            },
            "customer": null,
            "ip": "127.0.0.1",
            "created": "2014-10-21T11:12:28Z"
        }""")

        self.assertTrue(isinstance(charge, class_))
        self.assertFalse(charge.captured)
        charge.capture()

        self.assertTrue(charge.captured)
        self.assertRequest(
            api_call,
            'https://api.omise.co/charges/chrg_test/capture',
        )


class CollectionTest(_ResourceMixin):

    def _getTargetClass(self):
        from .. import Collection
        return Collection

    def _getAccountClass(self):
        from .. import Account
        return Account

    def _makeOne(self):
        return self._getTargetClass().from_data({
            'object': 'list',
            'data': [
                {'object': 'account', 'id': 'acct_test_1'},
                {'object': 'account', 'id': 'acct_test_2'},
                {'object': 'account', 'id': 'acct_test_3'},
                {'object': 'account', 'id': 'acct_test_4'},
            ]
        })

    def test_len(self):
        collection = self._makeOne()
        self.assertEqual(len(collection), 4)

    def test_iter(self):
        collection = self._makeOne()
        iterable = iter(collection)
        firstItem = next(iterable)
        self.assertTrue(isinstance(firstItem, self._getAccountClass()))
        self.assertEqual(firstItem.id, 'acct_test_1')
        self.assertEqual(next(iterable).id, 'acct_test_2')
        self.assertEqual(next(iterable).id, 'acct_test_3')
        self.assertEqual(next(iterable).id, 'acct_test_4')
        def _func():
            next(iterable)
        self.assertRaises(StopIteration, _func)

    def test_getitem(self):
        collection = self._makeOne()
        self.assertTrue(isinstance(collection[0], self._getAccountClass()))
        self.assertEqual(collection[0].id, 'acct_test_1')
        self.assertEqual(collection[3].id, 'acct_test_4')
        self.assertEqual(collection[-1].id, 'acct_test_4')

    def test_retrieve(self):
        collection = self._makeOne()
        firstItem = collection.retrieve('acct_test_1')
        self.assertTrue(isinstance(firstItem, self._getAccountClass()))
        self.assertEqual(firstItem.id, 'acct_test_1')
        self.assertEqual(collection.retrieve('acct_test_2').id, 'acct_test_2')
        self.assertEqual(collection.retrieve('acct_test_3').id, 'acct_test_3')
        self.assertEqual(collection.retrieve('acct_test_4').id, 'acct_test_4')
        self.assertEqual(collection.retrieve('acct_test_5'), None)

    def test_retrieve_no_args(self):
        collection = self._makeOne()
        def _extract_id(item):
            return item.id
        firstItem = collection.retrieve()[0]
        self.assertTrue(isinstance(firstItem, self._getAccountClass()))
        self.assertEqual(
            list(map(_extract_id, collection.retrieve())),
            list(map(_extract_id, list(collection)))
        )


class CustomerTest(_ResourceMixin):

    def _getTargetClass(self):
        from .. import Customer
        return Customer

    def _getCardClass(self):
        from .. import Card
        return Card

    def _getCollectionClass(self):
        from .. import Collection
        return Collection

    def _makeOne(self):
        return self._getTargetClass().from_data({
            'object': 'customer',
            'description': 'John Doe (id: 30)',
            'created': '2014-10-24T08:26:46Z',
            'livemode': False,
            'email': 'john.doe@example.com',
            'default_card': 'card_test',
            'location': '/customers/cust_test',
            'cards': {
                'from': '1970-01-01T07:00:00+07:00',
                'object': 'list',
                'to': '2014-10-24T15:32:31+07:00',
                'limit': 20,
                'location': '/customers/cust_test/cards',
                'offset': 0,
                'total': 1,
                'data': [
                    {
                        'city': None,
                        'financing': '',
                        'object': 'card',
                        'expiration_year': 2017,
                        'last_digits': '4242',
                        'created': '2014-10-24T08:26:07Z',
                        'country': '',
                        'brand': 'Visa',
                        'livemode': False,
                        'expiration_month': 9,
                        'postal_code': None,
                        'location': '/customers/cust_test/cards/card_test',
                        'fingerprint': '098f6bcd4621d373cade4e832627b4f6',
                        'id': 'card_test',
                        'name': 'Test card'
                    }
                ]
            },
            'id': 'cust_test'
        })

    @mock.patch('requests.post')
    def test_create(self, api_call):
        class_ = self._getTargetClass()
        card_class_ = self._getCardClass()
        collection_class_ = self._getCollectionClass()
        self.mockResponse(api_call, """{
            "object": "customer",
            "id": "cust_test",
            "livemode": false,
            "location": "/customers/cust_test",
            "default_card": null,
            "email": "john.doe@example.com",
            "description": "John Doe (id: 30)",
            "created": "2014-10-24T06:04:48Z",
            "cards": {
                "object": "list",
                "from": "1970-01-01T07:00:00+07:00",
                "to": "2014-10-24T13:04:48+07:00",
                "offset": 0,
                "limit": 20,
                "total": 1,
                "data": [
                    {
                        "object": "card",
                        "id": "card_test",
                        "livemode": false,
                        "location": "/customers/cust_test/cards/card_test",
                        "country": "",
                        "city": null,
                        "postal_code": null,
                        "financing": "",
                        "last_digits": "4242",
                        "brand": "Visa",
                        "expiration_month": 9,
                        "expiration_year": 2017,
                        "fingerprint": "098f6bcd4621d373cade4e832627b4f6",
                        "name": "Test card",
                        "created": "2014-10-24T08:26:07Z"
                    }
                ],
                "location": "/customers/cust_test/cards"
            }
         }""")

        customer = class_.create(
            description='John Doe (id: 30)',
            email='john.doe@example.com',
            card='tokn_test',
        )

        self.assertTrue(isinstance(customer, class_))
        self.assertTrue(isinstance(customer.cards, collection_class_))
        self.assertTrue(isinstance(customer.cards[0], card_class_))
        self.assertEqual(customer.id, 'cust_test')
        self.assertEqual(customer.description, 'John Doe (id: 30)')
        self.assertEqual(customer.email, 'john.doe@example.com')
        self.assertEqual(customer.cards[0].id, 'card_test')
        self.assertEqual(customer.cards[0].last_digits, '4242')
        self.assertRequest(
            api_call,
            'https://api.omise.co/customers',
            {
                'description': 'John Doe (id: 30)',
                'email': 'john.doe@example.com',
                'card': 'tokn_test',
            }
        )

    @mock.patch('requests.get')
    def test_retrieve(self, api_call):
        class_ = self._getTargetClass()
        card_class_ = self._getCardClass()
        collection_class_ = self._getCollectionClass()
        self.mockResponse(api_call, """{
            "object": "customer",
            "id": "cust_test",
            "livemode": false,
            "location": "/customers/cust_test",
            "default_card": "card_test",
            "email": "john.doe@example.com",
            "description": "John Doe (id: 30)",
            "created": "2014-10-24T08:26:46Z",
            "cards": {
                "object": "list",
                "from": "1970-01-01T07:00:00+07:00",
                "to": "2014-10-24T15:32:31+07:00",
                "offset": 0,
                "limit": 20,
                "total": 1,
                "data": [
                    {
                        "object": "card",
                        "id": "card_test",
                        "livemode": false,
                        "location": "/customers/cust_test/cards/card_test",
                        "country": "",
                        "city": null,
                        "postal_code": null,
                        "financing": "",
                        "last_digits": "4242",
                        "brand": "Visa",
                        "expiration_month": 9,
                        "expiration_year": 2017,
                        "fingerprint": "098f6bcd4621d373cade4e832627b4f6",
                        "name": "Test card",
                        "created": "2014-10-24T08:26:07Z"
                    }
                ],
                "location": "/customers/cust_test/cards"
            }
        }""")

        customer = class_.retrieve('cust_test')
        self.assertTrue(isinstance(customer, class_))
        self.assertTrue(isinstance(customer.cards, collection_class_))
        self.assertTrue(isinstance(customer.cards[0], card_class_))
        self.assertEqual(customer.id, 'cust_test')
        self.assertEqual(customer.description, 'John Doe (id: 30)')
        self.assertEqual(customer.email, 'john.doe@example.com')
        self.assertEqual(customer.cards[0].id, 'card_test')
        self.assertEqual(customer.cards[0].last_digits, '4242')
        self.assertRequest(api_call, 'https://api.omise.co/customers/cust_test')

        self.mockResponse(api_call, """{
            "object": "customer",
            "id": "cust_test",
            "livemode": false,
            "location": "/customers/cust_test",
            "default_card": "card_test",
            "email": "john.smith@example.com",
            "description": "John Doe (id: 30)",
            "created": "2014-10-24T08:26:46Z",
            "cards": {
                "object": "list",
                "from": "1970-01-01T07:00:00+07:00",
                "to": "2014-10-24T15:32:31+07:00",
                "offset": 0,
                "limit": 20,
                "total": 1,
                "data": [
                    {
                        "object": "card",
                        "id": "card_test",
                        "livemode": false,
                        "location": "/customers/cust_test/cards/card_test",
                        "country": "",
                        "city": null,
                        "postal_code": null,
                        "financing": "",
                        "last_digits": "4242",
                        "brand": "Visa",
                        "expiration_month": 9,
                        "expiration_year": 2017,
                        "fingerprint": "098f6bcd4621d373cade4e832627b4f6",
                        "name": "Test card",
                        "created": "2014-10-24T08:26:07Z"
                    }
                ],
                "location": "/customers/cust_test/cards"
            }
        }""")

        customer.reload()
        self.assertEqual(customer.email, 'john.smith@example.com')
        self.assertRequest(api_call, 'https://api.omise.co/customers/cust_test')

    @mock.patch('requests.patch')
    def test_update(self, api_call):
        customer = self._makeOne()
        class_ = self._getTargetClass()
        self.mockResponse(api_call, """{
            "object": "customer",
            "id": "cust_test",
            "livemode": false,
            "location": "/customers/cust_test",
            "default_card": "card_test",
            "email": "john.smith@example.com",
            "description": "Another description",
            "created": "2014-10-24T08:26:46Z",
            "cards": {
                "object": "list",
                "from": "1970-01-01T07:00:00+07:00",
                "to": "2014-10-24T15:32:31+07:00",
                "offset": 0,
                "limit": 20,
                "total": 1,
                "data": [
                    {
                        "object": "card",
                        "id": "card_test",
                        "livemode": false,
                        "location": "/customers/cust_test/cards/card_test",
                        "country": "",
                        "city": null,
                        "postal_code": null,
                        "financing": "",
                        "last_digits": "4242",
                        "brand": "Visa",
                        "expiration_month": 9,
                        "expiration_year": 2017,
                        "fingerprint": "098f6bcd4621d373cade4e832627b4f6",
                        "name": "Test card",
                        "created": "2014-10-24T08:26:07Z"
                    }
                ],
                "location": "/customers/cust_test/cards"
            }
        }""")

        self.assertTrue(isinstance(customer, class_))
        self.assertEqual(customer.description, 'John Doe (id: 30)')
        self.assertEqual(customer.email, 'john.doe@example.com')

        customer.description = 'Another description'
        customer.email = 'john.smith@example.com'
        customer.update()

        self.assertEqual(customer.description, 'Another description')
        self.assertEqual(customer.email, 'john.smith@example.com')
        self.assertRequest(
            api_call,
            'https://api.omise.co/customers/cust_test',
            {
                'description': 'Another description',
                'email': 'john.smith@example.com',
            }
        )

    @mock.patch('requests.delete')
    def test_destroy(self, api_call):
        customer = self._makeOne()
        class_ = self._getTargetClass()
        self.mockResponse(api_call, """{
            "object": "customer",
            "id": "cust_test",
            "livemode": false,
            "deleted": true
        }""")

        self.assertTrue(isinstance(customer, class_))
        self.assertEqual(customer.email, 'john.doe@example.com')

        customer.destroy()
        self.assertTrue(customer.destroyed)
        self.assertRequest(api_call, 'https://api.omise.co/customers/cust_test')


class TransferTest(_ResourceMixin):

    def _getTargetClass(self):
        from .. import Transfer
        return Transfer

    def _getCollectionClass(self):
        from .. import Collection
        return Collection

    def _makeOne(self):
        return self._getTargetClass().from_data({
            'object': 'transfer',
            'created': '2014-11-18T11:31:26Z',
            'livemode': False,
            'failure_message': None,
            'paid': False,
            'currency': 'thb',
            'amount': 100000,
            'transaction': None,
            'location': '/transfers/trsf_test',
            'failure_code': None,
            'id': 'trsf_test',
            'sent': False
        })

    @mock.patch('requests.post')
    def test_create(self, api_call):
        class_ = self._getTargetClass()
        self.mockResponse(api_call, """{
            "object": "transfer",
            "id": "trsf_test",
            "livemode": false,
            "location": "/transfers/trsf_test",
            "sent": false,
            "paid": false,
            "amount": 100000,
            "currency": "thb",
            "failure_code": null,
            "failure_message": null,
            "transaction": null,
            "created": "2014-11-18T11:31:26Z"
        }""")

        transfer = class_.create(amount=100000)
        self.assertTrue(isinstance(transfer, class_))
        self.assertEqual(transfer.id, 'trsf_test')
        self.assertEqual(transfer.amount, 100000)
        self.assertRequest(
            api_call,
            'https://api.omise.co/transfers',
            {'amount': 100000}
        )

    @mock.patch('requests.get')
    def test_retrieve(self, api_call):
        class_ = self._getTargetClass()
        self.mockResponse(api_call, """{
            "object": "transfer",
            "id": "trsf_test",
            "livemode": false,
            "location": "/transfers/trsf_test",
            "sent": false,
            "paid": false,
            "amount": 100000,
            "currency": "thb",
            "failure_code": null,
            "failure_message": null,
            "transaction": null,
            "created": "2014-11-18T11:31:26Z"
        }
        """)

        transfer = class_.retrieve('trsf_test')
        self.assertTrue(isinstance(transfer, class_))
        self.assertFalse(transfer.sent)
        self.assertFalse(transfer.paid)
        self.assertEqual(transfer.id, 'trsf_test')
        self.assertEqual(transfer.amount, 100000)
        self.assertEqual(transfer.transaction, None)
        self.assertRequest(api_call, 'https://api.omise.co/transfers/trsf_test')

        self.mockResponse(api_call, """{
            "object": "transfer",
            "id": "trsf_test",
            "livemode": false,
            "location": "/transfers/trsf_test",
            "sent": true,
            "paid": true,
            "amount": 100000,
            "currency": "thb",
            "failure_code": null,
            "failure_message": null,
            "transaction": null,
            "created": "2014-11-18T11:31:26Z"
        }
        """)

        transfer.reload()
        self.assertTrue(transfer.sent)
        self.assertTrue(transfer.paid)

    @mock.patch('requests.get')
    def test_retrieve_no_args(self, api_call):
        class_ = self._getTargetClass()
        collection_class_ = self._getCollectionClass()
        self.mockResponse(api_call, """{
            "object": "list",
            "from": "1970-01-01T07:00:00+07:00",
            "to": "2014-10-27T11:36:24+07:00",
            "offset": 0,
            "limit": 20,
            "total": 1,
            "data": [
                {
                    "object": "transfer",
                    "id": "trsf_test",
                    "livemode": false,
                    "location": "/transfers/trsf_test",
                    "sent": false,
                    "paid": false,
                    "amount": 96350,
                    "currency": "thb",
                    "failure_code": null,
                    "failure_message": null,
                    "transaction": null,
                    "created": "2014-11-18T11:31:26Z"
                }
            ]
        }""")

        transfers = class_.retrieve()
        self.assertTrue(isinstance(transfers, collection_class_))
        self.assertTrue(isinstance(transfers[0], class_))
        self.assertTrue(transfers[0].id, 'trsf_test')
        self.assertTrue(transfers[0].amount, 96350)
        self.assertRequest(api_call, 'https://api.omise.co/transfers')

    @mock.patch('requests.patch')
    def test_update(self, api_call):
        transfer = self._makeOne()
        class_ = self._getTargetClass()
        self.mockResponse(api_call, """{
            "object": "transfer",
            "id": "trsf_test",
            "livemode": false,
            "location": "/transfers/trsf_test",
            "sent": false,
            "paid": false,
            "amount": 80000,
            "currency": "thb",
            "failure_code": null,
            "failure_message": null,
            "transaction": null,
            "created": "2014-11-18T11:31:26Z"
        }""")

        self.assertTrue(isinstance(transfer, class_))
        self.assertEqual(transfer.amount, 100000)
        transfer.amount = 80000
        transfer.update()

        self.assertEqual(transfer.amount, 80000)
        self.assertRequest(
            api_call,
            'https://api.omise.co/transfers/trsf_test',
            {'amount': 80000}
        )

    @mock.patch('requests.delete')
    def test_destroy(self, api_call):
        transfer = self._makeOne()
        class_ = self._getTargetClass()
        self.mockResponse(api_call, """{
            "object": "transfer",
            "id": "trsf_test",
            "livemode": false,
            "deleted": true
        }""")

        self.assertTrue(isinstance(transfer, class_))
        self.assertEqual(transfer.id, 'trsf_test')

        transfer.destroy()
        self.assertTrue(transfer.destroyed)
        self.assertRequest(
            api_call,
            'https://api.omise.co/transfers/trsf_test'
        )


class TransactionTest(_ResourceMixin):

    def _getTargetClass(self):
        from .. import Transaction
        return Transaction

    def _getCollectionClass(self):
        from .. import Collection
        return Collection

    @mock.patch('requests.get')
    def test_retrieve(self, api_call):
        class_ = self._getTargetClass()
        self.mockResponse(api_call, """{
            "object": "transaction",
            "id": "trxn_test",
            "type": "credit",
            "amount": 9635024,
            "currency": "thb",
            "created": "2014-10-27T06:58:56Z"
        }
        """)

        transaction = class_.retrieve('trxn_test')
        self.assertTrue(isinstance(transaction, class_))
        self.assertEqual(transaction.id, 'trxn_test')
        self.assertEqual(transaction.type, 'credit')
        self.assertEqual(transaction.amount, 9635024)
        self.assertEqual(transaction.currency, 'thb')
        self.assertRequest(
            api_call,
            'https://api.omise.co/transactions/trxn_test'
        )

        transaction.amount = 9635023
        self.assertEqual(transaction.amount, 9635023)
        self.mockResponse(api_call, """{
            "object": "transaction",
            "id": "trxn_test",
            "type": "credit",
            "amount": 9635024,
            "currency": "thb",
            "created": "2014-10-27T06:58:56Z"
        }
        """)

        transaction.reload()
        self.assertEqual(transaction.amount, 9635024)
        self.assertEqual(transaction.currency, 'thb')
        self.assertRequest(
            api_call,
            'https://api.omise.co/transactions/trxn_test'
        )

    @mock.patch('requests.get')
    def test_retrieve_no_args(self, api_call):
        class_ = self._getTargetClass()
        collection_class_ = self._getCollectionClass()
        self.mockResponse(api_call, """{
            "object": "list",
            "from": "1970-01-01T07:00:00+07:00",
            "to": "2014-10-27T14:55:29+07:00",
            "offset": 0,
            "limit": 20,
            "total": 2,
            "data": [
                {
                    "object": "transaction",
                    "id": "trxn_test_1",
                    "type": "credit",
                    "amount": 9635024,
                    "currency": "thb",
                    "created": "2014-10-27T06:58:56Z"
                },
                {
                    "object": "transaction",
                    "id": "trxn_test_2",
                    "type": "debit",
                    "amount": 100025,
                    "currency": "thb",
                    "created": "2014-10-27T07:02:54Z"
                }
            ]
        }""")

        transactions = class_.retrieve()
        self.assertTrue(isinstance(transactions, collection_class_))
        self.assertTrue(isinstance(transactions[0], class_))
        self.assertTrue(transactions[0].id, 'trxn_test_1')
        self.assertTrue(transactions[0].type, 'credit')
        self.assertTrue(transactions[0].amount, 9635024)
        self.assertTrue(isinstance(transactions[1], class_))
        self.assertTrue(transactions[1].id, 'trxn_test_2')
        self.assertTrue(transactions[1].type, 'debit')
        self.assertTrue(transactions[1].amount, 100025)
        self.assertRequest(api_call, 'https://api.omise.co/transactions')

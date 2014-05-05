# Copyright 2014 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS-IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


"""Tests for crypto and hashing."""

__author__ = 'Mike Gainer (mgainer@google.com)'

import re

import actions

from common import crypto

URLSAFE_B64_ALPHABET = re.compile('^[a-zA-Z0-9-_=]+$')


class EncryptionManagerTests(actions.TestBase):

    def test_hmac_is_consistent(self):
        message = 'Mary had a little lamb.  Her doctors were astounded'
        h1 = crypto.EncryptionManager.hmac(message)
        h2 = crypto.EncryptionManager.hmac(message)
        self.assertEquals(h1, h2)
        self.assertNotEquals(h1, message)

    def test_encrypt_is_consistent(self):
        message = 'Mary had a little lamb.  Her doctors were astounded'
        e1 = crypto.EncryptionManager.encrypt(message)
        e2 = crypto.EncryptionManager.encrypt(message)
        self.assertEquals(e1, e2)
        self.assertNotEquals(e1, message)

    def test_encrypt_urlsafe_is_urlsafe(self):
        message = 'Mary had a little lamb.  Her doctors were astounded'
        e1 = crypto.EncryptionManager.encrypt(message)
        self.assertIsNone(URLSAFE_B64_ALPHABET.match(e1))  # some illegal chars
        e2 = crypto.EncryptionManager.encrypt_to_base64(message)
        self.assertIsNotNone(URLSAFE_B64_ALPHABET.match(e2))
        self.assertNotEquals(message, e2)

    def test_encrypt_decrypt(self):
        message = 'Mary had a little lamb.  Her doctors were astounded'
        e = crypto.EncryptionManager.encrypt(message)
        d = crypto.EncryptionManager.decrypt(e)
        self.assertEquals(d, message)
        self.assertNotEquals(e, d)

    def test_encrypt_decrypt_urlsafe(self):
        message = 'Mary had a little lamb.  Her doctors were astounded'
        e = crypto.EncryptionManager.encrypt_to_base64(message)
        d = crypto.EncryptionManager.decrypt_from_base64(e)
        self.assertEquals(d, message)
        self.assertNotEquals(e, d)


class XsrfTokenManagerTests(actions.TestBase):

    def test_valid_token(self):
        action = 'lob_cheese'
        t = crypto.XsrfTokenManager.create_xsrf_token(action)
        self.assertTrue(crypto.XsrfTokenManager.is_xsrf_token_valid(
            t, action))

    def test_token_for_different_action(self):
        action1 = 'lob_cheese'
        action2 = 'eat_cheese'
        t1 = crypto.XsrfTokenManager.create_xsrf_token(action1)
        self.assertFalse(crypto.XsrfTokenManager.is_xsrf_token_valid(
            t1, action2))

    def test_token_for_mangled_string(self):
        action = 'lob_cheese'
        t = crypto.XsrfTokenManager.create_xsrf_token(action)
        self.assertFalse(crypto.XsrfTokenManager.is_xsrf_token_valid(
            t, action + '.'))


class PiiObfuscationHmac(actions.TestBase):

    def test_consistent(self):
        message = 'Mary had a little lamb.  Her doctors were astounded'
        secret = 'skoodlydoodah'
        h1 = crypto.hmac_sha_2_256_transform(secret, message)
        h2 = crypto.hmac_sha_2_256_transform(secret, message)
        self.assertEquals(h1, h2)
        self.assertNotEquals(h1, message)

    def test_change_secret_changes_hmac(self):
        message = 'Mary had a little lamb.  Her doctors were astounded'
        secret = 'skoodlydoodah'
        h1 = crypto.hmac_sha_2_256_transform(secret, message)
        h2 = crypto.hmac_sha_2_256_transform(secret + '.', message)
        self.assertNotEquals(h1, h2)
        self.assertNotEquals(h1, message)


class GenCryptoKeyFromHmac(actions.TestBase):

    def test_gen_crypto_key(self):
        message = 'Mary had a little lamb.  Her doctors were astounded'
        action = 'lob_cheese'
        t = crypto.XsrfTokenManager.create_xsrf_token(message)

        secret = crypto.generate_transform_secret_from_xsrf_token(t, action)
        self.assertNotEqual(secret, message)
        self.assertNotEqual(secret, action)
        self.assertNotEqual(secret, t)

    def test_use_crypto_key(self):
        action = 'lob_cheese'
        t = crypto.XsrfTokenManager.create_xsrf_token(action)
        secret = crypto.generate_transform_secret_from_xsrf_token(t, action)

        message = 'Mary had a little lamb.  Her doctors were astounded'
        e = crypto.EncryptionManager.encrypt(message, secret)
        d = crypto.EncryptionManager.decrypt(e, secret)

        self.assertEquals(d, message)
        self.assertNotEquals(e, d)
        self.assertNotEquals(e, secret)
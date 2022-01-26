# Copyright 2022 The Matrix.org Foundation C.I.C.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from typing import Optional

import aiounittest

from tests import create_module
from username_from_threepid import LoginType, UsernameFromThreepid


class UsernameFromThreepidTestCase(aiounittest.AsyncTestCase):
    async def test_no_3pid(self) -> None:
        """Tests that the module returns None if no 3pid matching the configuration could
        be found.
        """
        module = create_module({"threepid_to_use": "email"})
        res = await module.set_username_from_threepid({}, {})
        self.assertIsNone(res)

    async def test_no_3pid_exception(self) -> None:
        """Tests that the module raises a RuntimeError if no 3pid matching the
        configuration could be found and the configuration requires it.
        """
        module = create_module({"threepid_to_use": "email", "fail_if_not_found": True})
        with self.assertRaises(RuntimeError):
            await module.set_username_from_threepid({}, {})

    async def test_email(self) -> None:
        """Tests that email addresses are correctly translated into usernames."""
        input = "foo@bar.baz"
        expected_output = "foo-bar.baz"
        module = create_module({"threepid_to_use": "email"})
        await self._test_email(module, input, expected_output)

    async def test_email_invalid_char(self) -> None:
        """Tests that characters that would be illegal in an MXID are correctly filtered
        out of the resulting username.
        """
        input = "fooé@bar.baz"
        expected_output = "foo-bar.baz"
        module = create_module({"threepid_to_use": "email"})
        await self._test_email(module, input, expected_output)

    async def test_email_conflict(self) -> None:
        """Tests that, when registering with an email address, a digit is appended if the
        resulting username clashes with an existing user.
        """
        input = "foo@bar.baz"
        expected_output = "foo-bar.baz1"
        module = create_module({"threepid_to_use": "email"}, succeed_attempt=2)
        await self._test_email(module, input, expected_output)

    async def _test_email(
        self,
        module: UsernameFromThreepid,
        input: str,
        expected_output: Optional[str],
    ) -> None:
        """Calls the given module's "set_username_from_threepid" method and checks that
        the resulting value matches what's expected.

        Args:
            module: The module to test.
            input: The email address to test with.
            expected_output: The expected return value from the module

        Raises:
            AssertionError if the return value from the module doesn't match the expected
                value.
        """
        uia_results = {
            LoginType.EMAIL_IDENTITY: {
                "address": input,
                "medium": "email",
                "verified_at": 0,
            }
        }
        res = await module.set_username_from_threepid(uia_results, {})
        self.assertEqual(res, expected_output)

    async def test_msisdn(self) -> None:
        """Tests that registering with a phone number correctly translates into a
        username.
        """
        msisdn_number = "440000000000"
        module = create_module({"threepid_to_use": "msisdn"})
        uia_results = {
            LoginType.MSISDN: {
                "address": msisdn_number,
                "medium": "msisdn",
                "verified_at": 0,
            }
        }
        res = await module.set_username_from_threepid(uia_results, {})
        self.assertEqual(res, msisdn_number)

    async def test_msisdn_conflict(self) -> None:
        """Tests that, when registering with an email address, a digit is appended if the
        resulting username clashes with an existing user.
        """
        msisdn_number = "440000000000"
        module = create_module({"threepid_to_use": "msisdn"}, succeed_attempt=2)
        uia_results = {
            LoginType.MSISDN: {
                "address": msisdn_number,
                "medium": "msisdn",
                "verified_at": 0,
            }
        }
        res = await module.set_username_from_threepid(uia_results, {})
        self.assertEqual(res, msisdn_number + "-1")

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
import re
import string
from typing import Any, Dict, Optional

import attr
from synapse.module_api import ModuleApi
from synapse.module_api.errors import ConfigError, SynapseError
from typing_extensions import Final

mxid_localpart_allowed_characters = frozenset(
    "_-./=" + string.ascii_lowercase + string.digits
)


class LoginType:
    EMAIL_IDENTITY: Final = "m.login.email.identity"
    MSISDN: Final = "m.login.msisdn"


@attr.s(auto_attribs=True, frozen=True)
class UsernameFromThreepidConfig:
    threepid_to_use: str
    fail_if_not_found: bool = False


class UsernameFromThreepid:
    def __init__(self, config: UsernameFromThreepidConfig, api: ModuleApi):
        # Keep a reference to the config and Module API
        self._api = api
        self._config = config

        self._api.register_password_auth_provider_callbacks(
            get_username_for_registration=self.set_username_from_threepid,
        )

    @staticmethod
    def parse_config(config: Dict[str, Any]) -> UsernameFromThreepidConfig:
        """Checks that the required fields are present and at a correct value, and
        instantiates a UsernameEmailConfig.

        Args:
            config: The raw configuration dict.

        Returns:
            A UsernameEmailConfig generated from this configuration

        Raises:
            ConfigError if a required field is missing or at an illegal value.
        """
        if "threepid_to_use" not in config:
            raise ConfigError('missing required configuration key: "threepid_to_use"')

        if config["threepid_to_use"] not in ["email", "msisdn"]:
            raise ConfigError(
                '"threepid_to_use" can only be either "email" or "msisdn"'
            )

        return UsernameFromThreepidConfig(**config)

    async def set_username_from_threepid(
        self,
        auth_result: Dict[str, Any],
        params: Dict[str, Any],
    ) -> Optional[str]:
        """Look at the provided UIA result and figure out a username from the 3PIDs
        provided during registration.

        Args:
            auth_result: The UIA results.
            params: The body of the /register request. Not used by this module.

        Returns:
            A username, or None if no 3PID was provided and "fail_if_not_found" is set to
            False.

        Raises:
            RuntimeError if no 3PID was provided and "fail_if_not_found" is set to True.
        """
        final_username: Optional[str] = None

        if (
            self._config.threepid_to_use == "email"
            and LoginType.EMAIL_IDENTITY in auth_result
        ):
            address = auth_result[LoginType.EMAIL_IDENTITY]["address"]

            # filter out invalid characters
            filtered = filter(
                lambda c: c in mxid_localpart_allowed_characters,
                address.replace("@", "-").lower(),
            )
            desired_username = "".join(filtered)

            # Generate a unique username by appending "xx" to the desired value if it
            # clashes with an existing username, where "xx" is the first integer that
            # doesn't create a clash.
            final_username = await self._generate_unique_username(
                r"^(.*?)(\d+)$",
                desired_username,
            )
        elif (
            self._config.threepid_to_use == "msisdn" and LoginType.MSISDN in auth_result
        ):
            desired_username = auth_result[LoginType.MSISDN]["address"]
            # Generate a unique username by appending "-xx" to the desired value if it
            # clashes with an existing username, where "xx" is the first integer that
            # doesn't create a clash. We can't just add "xx" because otherwise we wouldn't
            # be able to distinguish digits we've added from digits that are included in
            # the phone number.
            final_username = await self._generate_unique_username(
                r"^(.*?-)(\d+)$",
                desired_username,
                separator="-",
            )
        else:
            if self._config.fail_if_not_found:
                raise RuntimeError("Cannot derive mxid from 3pid; no recognised 3pid")

        return final_username

    async def _generate_unique_username(
        self,
        r: str,
        desired_username: str,
        separator: str = "",
    ) -> str:
        """Generates a unique username based on the given value extracted by the module,
        appending an integer to it if it clashes with an existing username.

        Args:
            r: The pattern to use to identify whether we've already started appending
                integers to the desired value.
            desired_username: The initial value to check for existence and derive if
                needed.
            separator: The separator between the desired username and the integer.

        Returns:
            A unique username based on the initial value.
        """
        while True:
            try:
                await self._api.check_username(desired_username)
                # if we got this far we passed the check.
                break
            except SynapseError as e:
                if e.errcode == "M_USER_IN_USE":
                    m = re.match(r, desired_username)
                    if m:
                        desired_username = m.group(1) + str(int(m.group(2)) + 1)
                    else:
                        desired_username += separator + "1"
                else:
                    # something else went wrong.
                    raise

        return desired_username

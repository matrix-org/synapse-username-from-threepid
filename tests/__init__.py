from typing import Any, Dict

from mock import Mock
from synapse.api.errors import SynapseError
from synapse.module_api import ModuleApi

from username_from_threepid import UsernameFromThreepid


def create_module(
    config: Dict[str, Any],
    fail_first_attempt: bool = False,
) -> UsernameFromThreepid:
    # Create a mock based on the ModuleApi spec, but override some mocked functions
    # because some capabilities are needed for running the tests.
    async def check_username(username: str) -> None:
        if fail_first_attempt and not username.endswith("1"):
            raise SynapseError(code=400, msg="Username in use", errcode="M_USER_IN_USE")

    module_api = Mock(spec=ModuleApi)
    module_api.check_username = Mock(side_effect=check_username)

    parsed_config = UsernameFromThreepid.parse_config(config)

    return UsernameFromThreepid(parsed_config, module_api)

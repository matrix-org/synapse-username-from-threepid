# Synapse module to set usernames from third-party identifiers

This Synapse module derives usernames from third party identifiers (i.e. email addresses
and phone numbers) when registering users.


## Installation

From the virtual environment that you use for Synapse, install this module with:
```shell
pip install synapse-username-from-threepid
```
(If you run into issues, you may need to upgrade `pip` first, e.g. by running
`pip install --upgrade pip`)

Then alter your homeserver configuration, adding to your `modules` configuration:
```yaml
modules:
  - module: username_from_threepid.UsernameFromThreepid
    config:
      # Which third-party identifier to look for. Can either be "email" (for email
      # addresses), or "msisdn" (for phone numbers).
      # Required.
      threepid_to_use: "email"

      # Whether to fail the registration if no third-party identifier was provided during
      # the registration process.
      # Optional, defaults to false.
      fail_if_not_found: true
```


## Development

In a virtual environment with pip ≥ 21.1, run
```shell
pip install -e .[dev]
```

To run the unit tests, you can either use:
```shell
tox -e py
```
or
```shell
trial tests
```

To run the linters and `mypy` type checker, use `./scripts-dev/lint.sh`.


## Releasing

The exact steps for releasing will vary; but this is an approach taken by the
Synapse developers (assuming a Unix-like shell):

 1. Set a shell variable to the version you are releasing (this just makes
    subsequent steps easier):
    ```shell
    version=X.Y.Z
    ```

 2. Update `setup.cfg` so that the `version` is correct.

 3. Stage the changed files and commit.
    ```shell
    git add -u
    git commit -m v$version -n
    ```

 4. Push your changes.
    ```shell
    git push
    ```

 5. When ready, create a signed tag for the release:
    ```shell
    git tag -s v$version
    ```
    Base the tag message on the changelog.

 6. Push the tag.
    ```shell
    git push origin tag v$version
    ```

 7. If applicable:
    Create a source distribution and upload it to PyPI:
    ```shell
    python -m build
    twine upload dist/username_from_threepid-$version*
    ```

import os
import sys
import types

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT_DIR)


# Tests should not depend on external bobber package installation.
if "bobber" not in sys.modules:
    bobber_module = types.ModuleType("bobber")

    class _BobberClientStub:
        def __init__(self, *_args, **_kwargs):
            pass

        def healthcheck(self) -> bool:
            return True

        def produce(self, *_args, **_kwargs) -> bool:
            return True

        def close(self) -> None:
            return None

    bobber_module.BobberClient = _BobberClientStub
    sys.modules["bobber"] = bobber_module


# python-magic may be installed without native libmagic on local dev machines.
if "magic" not in sys.modules:
    magic_module = types.ModuleType("magic")

    def _from_buffer(*_args, **_kwargs):
        return "application/octet-stream"

    magic_module.from_buffer = _from_buffer
    sys.modules["magic"] = magic_module

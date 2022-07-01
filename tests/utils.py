import contextlib
import os
import shutil
import tempfile
from typing import Iterator, Optional, cast, Union


@contextlib.contextmanager
def isolated_filesystem(
    temp_dir: Optional[Union[str, os.PathLike]] = None
) -> Iterator[str]:
    """A context manager that creates a temporary directory and
    changes the current working directory to it. This isolates tests
    that affect the contents of the CWD to prevent them from
    interfering with each other.

    :param temp_dir: Create the temporary directory under this
        directory. If given, the created directory is not removed
        when exiting.

    .. versionchanged:: 8.0
        Added the ``temp_dir`` parameter.
    """
    cwd = os.getcwd()
    dt = tempfile.mkdtemp(dir=temp_dir)  # type: ignore[type-var]
    os.chdir(dt)

    try:
        yield cast(str, dt)
    finally:
        os.chdir(cwd)

        if temp_dir is None:
            try:
                shutil.rmtree(dt)
            except OSError:  # noqa: B014
                pass

# Logging

Flows has a centralized logging system, so that you can setup the verbosity of the library easily.

Currently the default verbosity of the library is `WARNING`.

To change the level of verbosity, just use one of the direct setters. For instance, here is how to change the verbosity
to the INFO level.

```python
import flows

flows.logging.set_verbosity_info()
```

You can also use the environment variable `FLOWS_VERBOSITY` to override the default verbosity. You can set it
to one of the following: `debug`, `info`, `warning`, `error`, `critical`. For example:

```bash
FLOWS_VERBOSITY=error ./myprogram.py
```

Additionally, some `warnings` can be disabled by setting the environment variable
`FLOWS_NO_ADVISORY_WARNINGS` to a true value, like *1*. This will disable any warning that is logged using
[`logger.warning_advice`]. For example:

```bash
FLOWS_NO_ADVISORY_WARNINGS=1 ./myprogram.py
```

Here is an example of how to use the same logger as the library in your own module or script:

```python
from flows import logging

logging.set_verbosity_info()
logger = logging.get_logger("flows")
logger.info("INFO")
logger.warning("WARN")
```


All the methods of this logging module are documented below, the main ones are
[`logging.get_verbosity`] to get the current level of verbosity in the logger and
[`logging.set_verbosity`] to set the verbosity to the level of your choice. In order (from the least
verbose to the most verbose), those levels (with their corresponding int values in parenthesis) are:

- `flows.logging.CRITICAL` or `flows.logging.FATAL` (int value, 50): only report the most
  critical errors.
- `flows.logging.ERROR` (int value, 40): only report errors.
- `flows.logging.WARNING` or `flows.logging.WARN` (int value, 30): only reports error and
  warnings. This the default level used by the library.
- `flows.logging.INFO` (int value, 20): reports error, warnings and basic information.
- `flows.logging.DEBUG` (int value, 10): report all information.

## Add file handler

You can add a file handler to the logger, so that all the logs are also written to a file. For instance:

```python
from flows import logging

logging.auto_set_dir() # by default, the logs are written to the library's root directory (flows/logs/{timestamp}/log.log)
logger = logging.get_logger()
logger.info("INFO")
logger.warning("WARN")
```

If you want to change the directory where the logs are written, you can use the `set_dir` method:

```python
from flows import logging

logging.set_dir("/tmp/logs")
logger = logging.get_logger()
logger.info("INFO")
logger.warning("WARN")
```

## Logging inside Flow library

When you are developing the flows library, you should use the module-level logger, like this:

```python
# flows/base_flows/custom_flows.py
from ...utils import logging

logger = logging.get_logger(__name__)

def flow():
    logger.info("INFO")
    logger.warning("WARN")
```


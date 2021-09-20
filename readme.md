# GVFB Booking

An oddly specific automated shift booking script for the Greater Vancouver Food Bank,
which allows people (mainly me) to register for shifts before they become full.

This can also probably be tweaked to work with other organizations on the Better Impact volunteer platform.

There are a few options to specify to configure:

```yaml
---
# Example config.yaml entry
username: qiz-li
password: mysupersafepassword

time:
  tuesday: 912
  wednesday:
    - 912
    - 14
  friday:
    - 14
    - 58
```

## Configuration variables

**`username`** _string_

Your username used to log into Better Impact.

**`password`** _string_

Your password used to log into Better Impact (keep this a secret).

**`time`** _dictionary_

Entries of human readable weekday names that you want to book shifts on (e.g. `tuesday`, `friday`).

Under each entry, you can specify a list of shift times to book. Possible options are:

- **`912`** _(9 AM - 12 PM)_

- **`14`** _(1 PM - 4 PM)_

- **`58`** _(5 PM - 8 PM)_

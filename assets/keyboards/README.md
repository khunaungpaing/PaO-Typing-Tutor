# Custom keyboard layouts

Add a `.json` file here and restart the application. Bindings use physical
QWERTY key labels and may emit one or more Unicode code points.

The virtual keyboard displays only the active output layer: `normal` by
default and `shift` while Shift is held. Physical English QWERTY labels are not
shown, but they are still used as the JSON binding identifiers below.

```json
{
  "name": "Myanmar",
  "bindings": {
    "Q": {"normal": "ဆ", "shift": "ဈ"},
    "S": {"normal": "ျ", "shift": "ှ"},
    "SPACE": {"normal": " ", "shift": " "}
  }
}
```

Unlisted keys inherit the built-in **Pa-O Kham Dom Experimental** mapping,
allowing layouts to be built incrementally. Supported labels are those printed
on the virtual keyboard.

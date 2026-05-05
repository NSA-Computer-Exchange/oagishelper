# oagishelper

A Python `xml.etree.ElementTree` wrapper for working with OAGIS BOD XML documents. Provides namespace-transparent XPath queries, convenience value accessors, and helpers for building and modifying BOD structures.

---

## Installation

```bash
pip install oagishelper
```

---

## Quick Start

```python
from oagishelper import OagisHelper

# Parse from string
h = OagisHelper(xml_string)

# Or use the classmethod
h = OagisHelper.fromstring(xml_string)

# Strip the default Infor namespace before parsing
h = OagisHelper(xml_string, strip_ns=True)

# Build a blank BOD from scratch
h = OagisHelper.frombod("Sync", "SalesOrder", fields={"LogicalID": "lid://infor.com/M3"})
```

---

## Namespace Handling

When an OAGIS document carries the default Infor namespace (`xmlns="http://schema.infor.com/InforOAGIS/2"`), ElementTree prefixes every tag internally with the namespace URI in Clark notation — which silently breaks plain XPath queries.

`oagishelper` detects this namespace automatically at parse time and rewrites XPath expressions transparently. You always write plain paths:

```python
h.find("ApplicationArea/Sender/LogicalID")        # works with or without namespace
h.find_value("DataArea/Sync/TenantID")             # same
```

Alternatively, strip the namespace before parsing:

```python
h = OagisHelper(xml_string, strip_ns=True)
```

---

## API Reference

### Instantiation

#### `OagisHelper(xml=None, strip_ns=False)`
Create an instance, optionally parsing an XML string immediately.

| Parameter | Type | Description |
|---|---|---|
| `xml` | `str` | XML string to parse. If omitted, creates an empty instance. |
| `strip_ns` | `bool` | Remove the default Infor namespace before parsing. Default `False`. |

```python
h = OagisHelper()                          # empty instance
h = OagisHelper(xml_string)               # parse immediately
h = OagisHelper(xml_string, strip_ns=True)
```

---

#### `OagisHelper.fromstring(xml, strip_ns=False)` — classmethod
Equivalent to `OagisHelper(xml, strip_ns)`. Returns an `OagisHelper` instance.

```python
h = OagisHelper.fromstring(xml_string)
h = OagisHelper.fromstring(xml_string, strip_ns=True)
```

---

#### `OagisHelper.frombod(verb, noun, fields=None, namespaces=None)` — classmethod
Build a blank OAGIS BOD and return an `OagisHelper` instance. Returns `None` if `verb` or `noun` are not valid XML names.

| Parameter | Type | Description |
|---|---|---|
| `verb` | `str` | BOD verb (e.g. `"Sync"`, `"Process"`). Must be a valid XML element name. |
| `noun` | `str` | BOD noun (e.g. `"SalesOrder"`). Must be a valid XML element name. |
| `fields` | `dict` | Optional values for standard BOD fields (see below). |
| `namespaces` | `dict` | Optional namespace attributes to set on the root element. |

**`fields` keys:**

| Key | Default | Description |
|---|---|---|
| `LogicalID` | `""` | Placed in `ApplicationArea/Sender/LogicalID` |
| `CreationDateTime` | Current UTC time | Format: `2026-04-30T09:11:00.000` |
| `BODID` | `""` | Placed in `ApplicationArea/BODID` |
| `TenantID` | `""` | Placed in `DataArea/<Verb>/TenantID` |
| `AccountingEntity` | `""` | Placed in `DataArea/<Verb>/AccountingEntityID` |
| `actionCode` | `"Add"` | Attribute on `DataArea/<Verb>/ActionCriteria/ActionExpression` |

All fields are always present in the output XML even if not supplied.

```python
h = OagisHelper.frombod(
    "Sync", "SalesOrder",
    fields={
        "LogicalID": "lid://infor.com/M3",
        "BODID": "abc-123",
        "TenantID": "ACME",
        "AccountingEntity": "100",
        "actionCode": "Add",
    },
    namespaces={"xmlns": "http://schema.infor.com/InforOAGIS/2"}
)
```

**Generated structure:**

```xml
<SyncSalesOrder xmlns="http://schema.infor.com/InforOAGIS/2">
    <ApplicationArea>
        <Sender>
            <LogicalID>lid://infor.com/M3</LogicalID>
        </Sender>
        <CreationDateTime>2026-04-30T09:11:00.000</CreationDateTime>
        <BODID>abc-123</BODID>
    </ApplicationArea>
    <DataArea>
        <Sync>
            <TenantID>ACME</TenantID>
            <AccountingEntityID>100</AccountingEntityID>
            <ActionCriteria>
                <ActionExpression actionCode="Add" />
            </ActionCriteria>
        </Sync>
        <SalesOrder />
    </DataArea>
</SyncSalesOrder>
```

---

### Serialization

#### `tostring(encoding="unicode", xml_declaration=False)`
Serialize the stored XML to a string. Returns `""` if no XML is loaded.

| Parameter | Type | Description |
|---|---|---|
| `encoding` | `str` | `"unicode"` returns `str`; `"utf-8"` returns bytes. Default `"unicode"`. |
| `xml_declaration` | `bool` | Prepend `<?xml version="1.0" encoding="utf-8"?>`. Default `False`. |

```python
xml_str = h.tostring()
xml_str = h.tostring(xml_declaration=True)
```

---

### Reading Elements

#### `find(xpath)`
Return the first `Element` matching the XPath, or `None`. Namespace-transparent.

```python
elem = h.find("ApplicationArea/Sender/LogicalID")
```

---

#### `find_value(xpath, default="")`
Return the text content of the first matching element. Returns `default` if the element is missing or has no text.

```python
logical_id = h.find_value("ApplicationArea/Sender/LogicalID")
tenant     = h.find_value("DataArea/Sync/TenantID", default="UNKNOWN")
```

---

#### `findall(xpath)`
Return a list of all `Element` objects matching the XPath. Returns `[]` if none found. Namespace-transparent.

```python
lines = h.findall("DataArea/SalesOrder/SalesOrderLine")
```

---

#### `findall_values(xpath, default="")`
Return a list of text values for all matching elements. Elements with no text yield `default`.

```python
ids = h.findall_values("DataArea/SalesOrder/SalesOrderLine/LineNumber")
```

---

### Reading Attributes

#### `attribute_get(xpath)`
Return an attribute value. The XPath must end with `/@attributeName`. Returns `None` if the element or attribute is missing.

```python
release_id = h.attribute_get("DataArea/SalesOrder/@releaseID")
```

---

### Modifying Elements

#### `element_set(xpath, value)`
Set the text content of an existing element. Returns `True` on success, `False` if the element is not found.

```python
h.element_set("ApplicationArea/BODID", "new-bod-id")
```

---

#### `element_tag(xpath, tag)`
Rename an element's tag. `tag` must be a valid XML element name. Returns `True` on success, `False` if the element is not found or the tag is invalid.

```python
h.element_tag("DataArea/OldName", "NewName")
```

---

#### `element_create(xpath, value=None, attrs=None)`
Create a new element at the given path. Any missing parent elements are created automatically. The final element is always created (even if a sibling with the same tag exists). All path segments must be valid XML element names. Returns `True` on success, `False` on invalid path or if no XML is loaded.

| Parameter | Type | Description |
|---|---|---|
| `xpath` | `str` | Full path to the new element. |
| `value` | `str` | Optional text content. |
| `attrs` | `dict` | Optional attributes to set. |

```python
h.element_create("DataArea/SalesOrder/OrderHeader", value="HDR-001")
h.element_create("DataArea/SalesOrder/OrderHeader", attrs={"type": "standard"})
```

---

#### `element_delete(xpath)`
Delete all elements matching the XPath. Also removes all child elements underneath. Cannot delete the root element. Returns `True` if at least one element was deleted, `False` otherwise.

```python
h.element_delete("DataArea/SalesOrder/SalesOrderLine")
```

---

### Modifying Attributes

#### `attribute_set(xpath, attrs)`
Set one or more attributes on an element. Returns `True` on success, `False` if the element is not found.

```python
h.attribute_set("DataArea/SalesOrder", {"releaseID": "9.2", "languageCode": "en-US"})
```

---

#### `attribute_delete(xpath, attrs)`
Delete a list of attributes from an element. Missing attributes are silently skipped. Returns `True` if the element is found, `False` otherwise.

```python
h.attribute_delete("DataArea/SalesOrder", ["releaseID", "languageCode"])
```

---

## Return Values

| Type | Meaning |
|---|---|
| `OagisHelper` | Returned by `fromstring` and `frombod` on success |
| `None` | Returned by `frombod` if `verb` or `noun` are invalid XML names |
| `str` | Returned by `find_value`, `tostring` |
| `list` | Returned by `findall`, `findall_values` |
| `Element` | Returned by `find` |
| `True` | Operation succeeded |
| `False` | Operation failed (element not found, invalid name, etc.) |

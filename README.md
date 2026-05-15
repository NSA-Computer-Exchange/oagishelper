# Quick Start (TUG Attendees)

1. Click "Code"
2. Download ZIP (no Git required)

OR

git clone https://github.com/NSA-Computer-Exchange/oagishelper  

---

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

#### `fromstring(xml, strip_ns=False)`
Load XML into an existing instance, or chain on a new one. Returns `self`.

```python
h = OagisHelper()
h.fromstring(xml_string)               # load into existing instance

h = OagisHelper().fromstring(xml_string)  # create and load in one step
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
    namespaces={"": "http://schema.infor.com/InforOAGIS/2", "xsi": "http://www.w3.org/2001/XMLSchema-instance"}
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
Return a list of `OagisHelper` objects wrapping each matching element. Returns `[]` if none found. Namespace-transparent. Each result supports all `OagisHelper` methods (`find_value`, `element_set`, etc.) relative to the matched element.

```python
lines = h.findall("DataArea/SalesOrder/SalesOrderLine")
for line in lines:
    print(line.find_value("LineNumber"), line.find_value("Quantity"))
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

#### `element_set(xpath, value, create=False, create_parents=True)`
Set the text content of an element. Returns `True` on success, `False` if the element is not found (or a parent is missing when `create_parents=False`).

| Parameter | Type | Description |
|---|---|---|
| `xpath` | `str` | Full path to the element. |
| `value` | `str` | Text content to set. |
| `create` | `bool` | If `True`, create the element when it does not exist. Default `False`. |
| `create_parents` | `bool` | If `True` (default), create any missing parent elements when `create=True`. If `False`, returns `False` when a parent is missing. Ignored when `create=False`. |

```python
h.element_set("ApplicationArea/BODID", "new-bod-id")
h.element_set("DataArea/SalesOrder/OrderHeader", "HDR-001", create=True)
h.element_set("DataArea/SalesOrder/OrderHeader", "HDR-001", create=True, create_parents=False)
```

---

#### `element_tag(xpath, tag)`
Rename an element's tag. `tag` must be a valid XML element name. Returns `True` on success, `False` if the element is not found or the tag is invalid.

```python
h.element_tag("DataArea/OldName", "NewName")
```

---

#### `element_create(xpath, value=None, attrs=None, create_parents=True)`
Create a new element at the given path. The final element is always created (even if a sibling with the same tag exists). All path segments must be valid XML element names. Returns an `OagisHelper` wrapping the new element on success, or `None` on failure (invalid path, missing parent when `create_parents=False`, or no XML loaded). The returned instance is falsy on failure and truthy on success.

Supports `.//anchor/child` search-style paths: the anchor element is located anywhere in the tree and the remaining path is created beneath it.

| Parameter | Type | Description |
|---|---|---|
| `xpath` | `str` | Full path to the new element. Supports `.//anchor/remaining` search paths. |
| `value` | `str` | Optional text content. |
| `attrs` | `dict` | Optional attributes to set. |
| `create_parents` | `bool` | If `True` (default), any missing parent elements are created automatically. If `False`, returns `None` when a parent is missing. |

```python
# Simple path
h.element_create("DataArea/SalesOrder/OrderHeader", value="HDR-001")

# Search-style path — creates line under the existing SupplierInvoice element
line = h.element_create(".//SupplierInvoice/SupplierInvoiceLine")
if line:
    line.element_set("LineNumber", "1", create=True)
    line.element_set("Quantity", "125", create=True)
    line.element_set("Description", "FLEX-OIL DELIVERY", create=True)
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
| `OagisHelper` (truthy) | Returned by `fromstring`, `frombod`, and `element_create` on success |
| `None` / falsy | Returned by `frombod` and `element_create` on failure |
| `str` | Returned by `find_value`, `tostring` |
| `list[OagisHelper]` | Returned by `findall` |
| `list[str]` | Returned by `findall_values` |
| `Element` | Returned by `find` |
| `True` | Operation succeeded (`element_set`, `attribute_set`, etc.) |
| `False` | Operation failed (element not found, invalid name, etc.) |

import re
from datetime import datetime
from xml.etree import ElementTree as ET
from typing import Optional

_XML_NAME_RE = re.compile(r'^[a-zA-Z_:][a-zA-Z0-9_:.\-]*$')


def _valid_xml_name(name: str) -> bool:
    return bool(name and _XML_NAME_RE.match(name) and not name.lower().startswith("xml"))


def _ns_xpath(xpath: str, ns: str) -> str:
    prefix = f"{{{ns}}}"
    parts = xpath.split("/")
    out = []
    for part in parts:
        if not part or part in (".", "..") or part == "*" or part.startswith("{") or part.startswith("@"):
            out.append(part)
        elif "[" in part:
            tag, rest = part.split("[", 1)
            if tag and tag not in (".", "..", "*") and not tag.startswith("{"):
                out.append(f"{prefix}{tag}[{rest}")
            else:
                out.append(part)
        else:
            out.append(f"{prefix}{part}")
    return "/".join(out)


class OagisHelper:

    _INFOR_NS = "http://schema.infor.com/InforOAGIS/2"
    _INFOR_NS_ATTR = f'xmlns="{_INFOR_NS}"'

    def __init__(self, xml: Optional[str] = None, strip_ns: bool = False) -> None:
        self._root: Optional[ET.Element] = None
        self._ns: Optional[str] = None
        if xml is not None:
            if strip_ns:
                xml = xml.replace(self._INFOR_NS_ATTR, "")
            self._root = ET.fromstring(xml)
            if self._root.tag.startswith(f"{{{self._INFOR_NS}}}"):
                self._ns = self._INFOR_NS

    def __bool__(self) -> bool:
        return self._root is not None

    def fromstring(self, xml: str, strip_ns: bool = False) -> "OagisHelper":
        if strip_ns:
            xml = xml.replace(self._INFOR_NS_ATTR, "")
        self._root = ET.fromstring(xml)
        self._ns = self._INFOR_NS if self._root.tag.startswith(f"{{{self._INFOR_NS}}}") else None
        return self

    def tostring(self, encoding: str = "unicode", xml_declaration: bool = False) -> str:
        if self._root is None:
            return ""
        if self._ns:
            ET.register_namespace("", self._ns)
        result = ET.tostring(self._root, encoding=encoding, method="xml")
        if xml_declaration:
            result = '<?xml version="1.0" encoding="utf-8"?>\n' + result
        return result

    def find(self, xpath: str) -> Optional[ET.Element]:
        if self._root is None:
            return None
        if self._ns:
            xpath = _ns_xpath(xpath, self._ns)
        return self._root.find(xpath)

    def find_value(self, xpath: str, default: str = "") -> str:
        element = self.find(xpath)
        if element is None or element.text is None:
            return default
        return element.text

    def findall(self, xpath: str) -> list:
        if self._root is None:
            return []
        if self._ns:
            xpath = _ns_xpath(xpath, self._ns)
        results = []
        for elem in self._root.findall(xpath):
            instance = OagisHelper()
            instance._root = elem
            instance._ns = self._ns
            results.append(instance)
        return results

    def findall_values(self, xpath: str, default: str = "") -> list:
        return [e._root.text if e._root.text is not None else default for e in self.findall(xpath)]

    def attribute_get(self, xpath: str) -> Optional[str]:
        if "/@" not in xpath:
            return None
        element_path, attr = xpath.rsplit("/@", 1)
        element = self.find(element_path)
        if element is None:
            return None
        return element.get(attr)

    def attribute_set(self, xpath: str, attrs: dict) -> bool:
        element = self.find(xpath)
        if element is None:
            return False
        for k, v in attrs.items():
            element.set(k, str(v))
        return True

    def attribute_delete(self, xpath: str, attrs: list) -> bool:
        element = self.find(xpath)
        if element is None:
            return False
        for attr in attrs:
            if attr in element.attrib:
                del element.attrib[attr]
        return True

    def element_tag(self, xpath: str, tag: str) -> bool:
        if not _valid_xml_name(tag):
            return False
        element = self.find(xpath)
        if element is None:
            return False
        element.tag = f"{{{self._ns}}}{tag}" if self._ns else tag
        return True

    def element_set(self, xpath: str, value: str, create: bool = False, create_parents: bool = True) -> bool:
        element = self.find(xpath)
        if element is None:
            if not create:
                return False
            if '//' in xpath:
                if '/' not in xpath:
                    return False
                parent_xpath, leaf_tag = xpath.rsplit('/', 1)
                if not _valid_xml_name(leaf_tag):
                    return False
                parent = self.find(parent_xpath)
                if parent is None:
                    return False
                ns_tag = f"{{{self._ns}}}{leaf_tag}" if self._ns else leaf_tag
                element = ET.SubElement(parent, ns_tag)
            else:
                segments = xpath.split("/")
                if not all(_valid_xml_name(seg) for seg in segments):
                    return False
                ns_segments = [f"{{{self._ns}}}{seg}" for seg in segments] if self._ns else segments
                current = self._root
                for tag in ns_segments[:-1]:
                    child = current.find(tag)
                    if child is None:
                        if not create_parents:
                            return False
                        child = ET.SubElement(current, tag)
                    current = child
                element = ET.SubElement(current, ns_segments[-1])
        element.text = str(value)
        return True

    def element_create(self, xpath: str, value: Optional[str] = None, attrs: Optional[dict] = None, create_parents: bool = True) -> Optional["OagisHelper"]:
        if not xpath or self._root is None:
            return None

        if '//' in xpath:
            search_part, _, create_part = xpath.partition('//')
            anchor_tag, _, remaining = create_part.partition('/')
            if not _valid_xml_name(anchor_tag) or not remaining:
                return None
            anchor = self.find(f"{search_part}//{anchor_tag}")
            if anchor is None:
                return None
            segments = remaining.split("/")
            if not all(_valid_xml_name(seg) for seg in segments):
                return None
            ns_segments = [f"{{{self._ns}}}{seg}" for seg in segments] if self._ns else segments
            current = anchor
        else:
            segments = xpath.split("/")
            if not all(_valid_xml_name(seg) for seg in segments):
                return None
            ns_segments = [f"{{{self._ns}}}{seg}" for seg in segments] if self._ns else segments
            current = self._root

        for tag in ns_segments[:-1]:
            child = current.find(tag)
            if child is None:
                if not create_parents:
                    return None
                child = ET.SubElement(current, tag)
            current = child

        new_elem = ET.SubElement(current, ns_segments[-1])
        if value is not None:
            new_elem.text = str(value)
        if attrs:
            for k, v in attrs.items():
                new_elem.set(k, str(v))

        instance = OagisHelper()
        instance._root = new_elem
        instance._ns = self._ns
        return instance

    def element_delete(self, xpath: str) -> bool:
        if not xpath or self._root is None or "/" not in xpath:
            return False

        parent_path, child_tag = xpath.rsplit("/", 1)
        parent = self.find(parent_path)
        if parent is None:
            return False

        child_tag = _ns_xpath(child_tag, self._ns) if self._ns else child_tag
        children = parent.findall(child_tag)
        if not children:
            return False

        for child in children:
            parent.remove(child)
        return True

    @classmethod
    def frombod(cls, verb: str, noun: str, fields: Optional[dict] = None, namespaces: Optional[dict] = None) -> Optional["OagisHelper"]:
        if not _valid_xml_name(verb) or not _valid_xml_name(noun):
            return None

        fields = fields or {}
        namespaces = namespaces or {}

        default_ns = namespaces.get("", "")
        for prefix, uri in namespaces.items():
            ET.register_namespace(prefix, uri)

        def _tag(name):
            return f"{{{default_ns}}}{name}" if default_ns else name

        root = ET.Element(_tag(f"{verb}{noun}"))

        app_area = ET.SubElement(root, _tag("ApplicationArea"))

        sender = ET.SubElement(app_area, _tag("Sender"))
        ET.SubElement(sender, _tag("LogicalID")).text = str(fields.get("LogicalID") or "")

        creation_dt = fields.get("CreationDateTime")
        if creation_dt is None:
            now = datetime.utcnow()
            creation_dt = now.strftime("%Y-%m-%dT%H:%M:%S.") + f"{now.microsecond // 1000:03d}"
        ET.SubElement(app_area, _tag("CreationDateTime")).text = str(creation_dt)

        ET.SubElement(app_area, _tag("BODID")).text = str(fields.get("BODID") or "")

        data_area = ET.SubElement(root, _tag("DataArea"))
        verb_elem = ET.SubElement(data_area, _tag(verb))

        ET.SubElement(verb_elem, _tag("TenantID")).text = str(fields.get("TenantID") or "")
        ET.SubElement(verb_elem, _tag("AccountingEntityID")).text = str(fields.get("AccountingEntity") or "")

        action_code = fields.get("actionCode", "Add")
        action_criteria = ET.SubElement(verb_elem, _tag("ActionCriteria"))
        ET.SubElement(action_criteria, _tag("ActionExpression")).set("actionCode", str(action_code))

        ET.SubElement(data_area, _tag(noun))

        instance = cls()
        instance._root = root
        instance._ns = default_ns or None
        return instance

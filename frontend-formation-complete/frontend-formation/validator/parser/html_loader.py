"""Parse contract-relevant HTML into a normalized document model."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from bs4 import BeautifulSoup, Tag

NATIVE_INTERACTIVE_TAGS = {"button", "input", "select", "textarea"}
INLINE_EVENT_ATTRS = {
    "onclick",
    "onchange",
    "onsubmit",
    "onkeydown",
    "onkeyup",
    "onkeypress",
    "onmouseover",
    "onmouseout",
    "onmousedown",
    "onmouseup",
    "onfocus",
    "onblur",
    "oninput",
    "ondblclick",
    "onpointerdown",
    "onpointerup",
}
NATIVE_ROLES = {
    "button": "button",
    "select": "combobox",
    "textarea": "textbox",
}
INTERACTIVE_ROLES = {
    "button",
    "checkbox",
    "combobox",
    "link",
    "listbox",
    "menuitem",
    "option",
    "radio",
    "slider",
    "spinbutton",
    "switch",
    "tab",
    "textbox",
}


@dataclass(frozen=True)
class DomElement:
    tag: str
    dom_id: str | None
    classification: str | None
    action: str | None
    contract_path: str | None
    feedback_target: str | None
    role: str | None
    href: str | None
    tabindex_value: str | None
    aria_label: str | None
    aria_labelledby: str | None
    aria_live: str | None
    text: str
    value: str | None
    associated_label_text: str
    labelledby_text: str
    inline_handlers: tuple[str, ...] = field(default_factory=tuple)

    @property
    def ref(self) -> str:
        return f"#{self.dom_id}" if self.dom_id else f"<{self.tag}> (no id)"

    @property
    def is_native_interactive(self) -> bool:
        return self.tag in NATIVE_INTERACTIVE_TAGS or (self.tag == "a" and bool(self.href))

    @property
    def is_semantic_interactive(self) -> bool:
        return self.is_native_interactive or bool(self.role) or self.tabindex_value is not None

    @property
    def accessible_name_present(self) -> bool:
        if self.aria_label and self.aria_label.strip():
            return True
        if self.labelledby_text.strip():
            return True
        if self.associated_label_text.strip():
            return True
        if self.text.strip():
            return True
        return bool(self.value and self.value.strip())


@dataclass(frozen=True)
class ScreenRoot:
    screen: str | None
    mission: str | None
    ref: str


@dataclass
class HtmlDocument:
    path: str
    elements: list[DomElement]
    screen_roots: list[ScreenRoot]
    id_counts: Counter[str]

    @property
    def elements_by_id(self) -> dict[str, DomElement]:
        result: dict[str, DomElement] = {}
        for element in self.elements:
            if element.dom_id and element.dom_id not in result:
                result[element.dom_id] = element
        return result

    @property
    def duplicate_ids(self) -> set[str]:
        return {dom_id for dom_id, count in self.id_counts.items() if count > 1}


def _text_for(tag: Tag) -> str:
    return " ".join(tag.stripped_strings)


def _associated_label_text(tag: Tag, soup: BeautifulSoup) -> str:
    texts = []
    dom_id = tag.attrs.get("id")
    if dom_id:
        for label in soup.find_all("label", attrs={"for": dom_id}):
            texts.append(_text_for(label))
    parent = tag.find_parent("label")
    if parent is not None:
        texts.append(_text_for(parent))
    return " ".join(text for text in texts if text)


def _labelledby_text(tag: Tag, soup: BeautifulSoup) -> str:
    refs = str(tag.attrs.get("aria-labelledby", "")).split()
    texts = []
    for ref in refs:
        target = soup.find(id=ref)
        if target is not None:
            texts.append(_text_for(target))
    return " ".join(text for text in texts if text)


def load_html(path: str | Path) -> HtmlDocument:
    path = str(path)
    with open(path, encoding="utf-8") as handle:
        soup = BeautifulSoup(handle.read(), "html.parser")

    elements: list[DomElement] = []
    ids: list[str] = []
    for tag in soup.find_all(True):
        attrs = tag.attrs
        dom_id = attrs.get("id")
        if dom_id:
            ids.append(str(dom_id))
        inline_handlers = tuple(sorted(a for a in INLINE_EVENT_ATTRS if a in attrs))
        elements.append(
            DomElement(
                tag=tag.name,
                dom_id=str(dom_id) if dom_id else None,
                classification=attrs.get("data-classification"),
                action=attrs.get("data-action"),
                contract_path=attrs.get("data-contract-path"),
                feedback_target=attrs.get("data-feedback-target"),
                role=attrs.get("role"),
                href=attrs.get("href"),
                tabindex_value=attrs.get("tabindex"),
                aria_label=attrs.get("aria-label"),
                aria_labelledby=attrs.get("aria-labelledby"),
                aria_live=attrs.get("aria-live"),
                text=_text_for(tag),
                value=attrs.get("value"),
                associated_label_text=_associated_label_text(tag, soup),
                labelledby_text=_labelledby_text(tag, soup),
                inline_handlers=inline_handlers,
            )
        )

    roots = []
    for root in soup.find_all(attrs={"data-screen": True}):
        roots.append(
            ScreenRoot(
                screen=root.get("data-screen"),
                mission=root.get("data-mission"),
                ref=f"#{root.get('id')}" if root.get("id") else f"<{root.name}> screen root",
            )
        )

    return HtmlDocument(path=path, elements=elements, screen_roots=roots, id_counts=Counter(ids))

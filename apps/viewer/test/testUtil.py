from typing import Any, Optional, TypeVar


def checkKeysExist(items, expectedKeys: list[str]) -> None:
    for item in items:
        assert item.key in expectedKeys
        expectedKeys.remove(item.key)
    assert len(expectedKeys) == 0, f"Some buttons were not found: {expectedKeys}"


T = TypeVar("T")


def getComponentByKey(components: Any, key: str, level: int = 0) -> Optional[T]:
    for comp in components:
        print(f'Checking component: {comp}', flush=True)
        if getattr(comp, "key", None) == key:
            print(f'Found component with key={key}: {comp}', flush=True)
            return comp
        elif child := getComponentByKeyChildren(comp, key, level + 1):
            return child
    return None


def getComponentByKeyChildren(comp: Any, key: str, level: int = 0) -> Optional[Any]:
    print(f'{"  " * level}Checking children of component: {comp}', flush=True)
    if hasattr(comp, 'children'):
        print(f'{"  " * level}Component has children: {comp.children}', flush=True)
        found = getComponentByKey(comp.children, key, level + 1)
        if found is not None:
            print(f'{"  " * level}Found component in children: {found}', flush=True)
            return found


def stPrintStructure(componentList) -> None:
    print(f'componentList={componentList}', flush=True)
    for item in componentList.items:
        print(f'componentList={componentList} item={item}', flush=True)

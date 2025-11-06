from typing import Any, Optional, TypeVar


T = TypeVar("T")


def getComponentByKey(app: Any, componentType: str, key: str) -> Optional[T]:
    components = getattr(app, componentType, [])
    for comp in components:
        print(f'Checking component: {comp}', flush=True)
        if getattr(comp, "key", None) == key:
            return comp
    return None


def stPrintStructure(componentList) -> None:
    print(f'componentList={componentList}', flush=True)
    for item in componentList.items:
        print(f'componentList={componentList} item={item}', flush=True)

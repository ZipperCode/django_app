from typing import Optional

from web_app.model.const import UsedStatus


def get_export_type(export_type) -> Optional[UsedStatus]:
    if not export_type:
        return None
    t = str(export_type)
    if t == "1":
        return UsedStatus.Used
    elif t == "2":
        return UsedStatus.Default
    elif t == "3":
        return UsedStatus.Unable
    return None

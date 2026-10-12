from __future__ import annotations

import json
import uuid
from pathlib import Path

from app.models import Profile, ProfileCreate, ProfileUpdate

DATA_DIR = Path.home() / ".local" / "share" / "fingerprint-browser"
PROFILES_FILE = DATA_DIR / "profiles.json"
USER_DATA_ROOT = DATA_DIR / "user_data"


def _ensure() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    USER_DATA_ROOT.mkdir(parents=True, exist_ok=True)
    if not PROFILES_FILE.exists():
        PROFILES_FILE.write_text("[]", encoding="utf-8")


def _load() -> list[Profile]:
    _ensure()
    raw = json.loads(PROFILES_FILE.read_text(encoding="utf-8"))
    return [Profile.model_validate(x) for x in raw]


def _save(profiles: list[Profile]) -> None:
    _ensure()
    PROFILES_FILE.write_text(
        json.dumps([p.model_dump() for p in profiles], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def list_profiles() -> list[Profile]:
    return _load()


def get_profile(profile_id: str) -> Profile | None:
    for p in _load():
        if p.id == profile_id:
            return p
    return None


def create_profile(body: ProfileCreate) -> Profile:
    profiles = _load()
    profile = Profile(id=uuid.uuid4().hex[:12], **body.model_dump())
    profiles.append(profile)
    _save(profiles)
    profile_data_dir(profile.id).mkdir(parents=True, exist_ok=True)
    return profile


def update_profile(profile_id: str, body: ProfileUpdate) -> Profile | None:
    profiles = _load()
    for i, p in enumerate(profiles):
        if p.id != profile_id:
            continue
        data = p.model_dump()
        for k, v in body.model_dump(exclude_unset=True).items():
            data[k] = v
        profiles[i] = Profile.model_validate(data)
        _save(profiles)
        return profiles[i]
    return None


def delete_profile(profile_id: str) -> bool:
    profiles = _load()
    new_list = [p for p in profiles if p.id != profile_id]
    if len(new_list) == len(profiles):
        return False
    _save(new_list)
    return True


def profile_data_dir(profile_id: str) -> Path:
    return USER_DATA_ROOT / profile_id

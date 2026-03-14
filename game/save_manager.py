"""세이브 매니저 — JSON 기반 진행/랭킹/설정 저장"""
import json
import os
from typing import Dict, Any
from datetime import datetime
from game.constants import SAVE_FILE, CUSTOM_LEVELS_DIR


DEFAULT_SAVE = {
    "unlocked": 1,
    "records": {},
    "settings": {
        "sfx_volume": 0.7,
    },
}


class SaveManager:
    """게임 세이브 데이터 관리"""

    def __init__(self) -> None:
        self._ensure_dirs()
        self.data = self.load()

    def _ensure_dirs(self) -> None:
        """필요한 디렉토리 생성"""
        save_dir = os.path.dirname(SAVE_FILE)
        if save_dir:
            os.makedirs(save_dir, exist_ok=True)
        os.makedirs(CUSTOM_LEVELS_DIR, exist_ok=True)
        os.makedirs("data/screenshots", exist_ok=True)

    def load(self) -> Dict[str, Any]:
        """save.json 읽기 (없으면 기본값)"""
        if os.path.exists(SAVE_FILE):
            try:
                with open(SAVE_FILE, 'r') as f:
                    data = json.load(f)
                # 기본값 보장
                for key, val in DEFAULT_SAVE.items():
                    if key not in data:
                        data[key] = val
                return data
            except (json.JSONDecodeError, IOError):
                return dict(DEFAULT_SAVE)
        return dict(DEFAULT_SAVE)

    def save(self, data: Dict[str, Any] = None) -> None:
        """save.json에 저장"""
        if data:
            self.data = data
        try:
            with open(SAVE_FILE, 'w') as f:
                json.dump(self.data, f, indent=2)
        except IOError:
            pass

    def get_unlocked(self) -> int:
        """잠금 해제된 최고 레벨 인덱스 (1-based)"""
        return self.data.get("unlocked", 1)

    def unlock_next(self, current_level: int) -> None:
        """다음 레벨 잠금 해제"""
        current_unlocked = self.data.get("unlocked", 1)
        if current_level + 1 > current_unlocked:
            self.data["unlocked"] = current_level + 1
            self.save()

    def save_record(self, level_idx: int, moves: int, time: float, stars: int) -> bool:
        """레벨 기록 저장. 신기록이면 True 반환"""
        records = self.data.get("records", {})
        key = str(level_idx)
        is_new_record = False

        if key not in records or moves < records[key].get("moves", float('inf')):
            records[key] = {
                "moves": moves,
                "time": round(time, 1),
                "stars": stars,
                "date": datetime.now().strftime("%Y-%m-%d"),
            }
            is_new_record = True
        elif stars > records[key].get("stars", 0):
            records[key]["stars"] = stars
            is_new_record = True

        self.data["records"] = records
        self.save()
        return is_new_record

    def get_record(self, level_idx: int) -> Dict[str, Any]:
        """레벨 기록 조회"""
        records = self.data.get("records", {})
        return records.get(str(level_idx), {})

    def get_settings(self) -> Dict[str, Any]:
        """설정 조회"""
        return self.data.get("settings", DEFAULT_SAVE["settings"])

    def save_settings(self, settings: Dict[str, Any]) -> None:
        """설정 저장"""
        self.data["settings"] = settings
        self.save()

    def save_custom_level(self, name: str, level_string: str) -> str:
        """커스텀 레벨 저장. 파일 경로 반환"""
        safe_name = "".join(c if c.isalnum() or c in "-_ " else "_" for c in name)
        filename = f"{safe_name}.json"
        filepath = os.path.join(CUSTOM_LEVELS_DIR, filename)
        data = {
            "name": name,
            "data": level_string,
        }
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        return filepath

    def load_custom_levels(self) -> list:
        """커스텀 레벨 목록 로드"""
        levels = []
        if os.path.isdir(CUSTOM_LEVELS_DIR):
            for fname in sorted(os.listdir(CUSTOM_LEVELS_DIR)):
                if fname.endswith('.json'):
                    fpath = os.path.join(CUSTOM_LEVELS_DIR, fname)
                    try:
                        with open(fpath, 'r') as f:
                            data = json.load(f)
                        data["filepath"] = fpath
                        levels.append(data)
                    except (json.JSONDecodeError, IOError):
                        pass
        return levels

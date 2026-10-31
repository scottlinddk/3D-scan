from dataclasses import dataclass


@dataclass(frozen=True)
class Limits:
    # ponytail: planning values. #21 replaces them with measured ARM64 VPS limits.
    max_file_bytes: int = 512 * 1024 * 1024
    user_quota_bytes: int = 5 * 1024 * 1024 * 1024
    max_chunk_bytes: int = 8 * 1024 * 1024

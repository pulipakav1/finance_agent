from src.fin_platform.memory import SessionMemoryManager


def test_memory_trim_and_metadata() -> None:
    manager = SessionMemoryManager()
    history = [{"role": "user", "content": str(i)} for i in range(20)]
    trimmed = manager.trim_history(history)
    assert len(trimmed) <= 12
    meta = manager.enrich_metadata("thread-1", {"x": 1})
    assert meta["thread_id"] == "thread-1"

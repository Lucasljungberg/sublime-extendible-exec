import asyncio
from pathlib import Path
from typing import (
    List,
    Optional,
)

import pytest

from lib import process


class FakeListener(process.ProcessListener):
    def __init__(self) -> None:
        self.lines: List[str] = []
        self.process_info: Optional[process.CompletedProcessInfo] = None

    def text(self) -> str:
        return "\n".join(self.lines).strip()

    def on_data(self, text: str) -> None:
        self.lines.append(text)

    def on_finished(self, completed_process: process.CompletedProcessInfo) -> None:
        self.process_info = completed_process


async def wait_for(p: process.AsyncProcess) -> None:
    await asyncio.to_thread(p.start)


@pytest.mark.asyncio
async def test_basic_async_process() -> None:
    listener = FakeListener()
    p = process.AsyncProcess(["echo", "hi"], {}, Path.cwd(), listener)
    await wait_for(p)

    assert "hi" == listener.text()

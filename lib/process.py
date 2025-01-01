import codecs
import dataclasses
import os
import signal
import subprocess
import threading
import time
from pathlib import Path
from typing import (
    Dict,
    List,
    Optional,
)


class Timestamp:
    def __init__(self, seconds_from_epoch: int):
        self.time = seconds_from_epoch

    def __sub__(self, other: object) -> "Timestamp":
        if not isinstance(other, Timestamp):
            raise NotImplementedError()

        return self.__class__(self.time - other.time)

    def __format__(self, spec: str) -> str:
        return format(self.time, spec)

    @classmethod
    def now(cls) -> "Timestamp":
        return cls(int(time.time()))


@dataclasses.dataclass
class Timespan:
    start: Timestamp
    end: Timestamp

    def difference(self) -> Timestamp:
        return self.end - self.start


@dataclasses.dataclass
class CompletedProcessInfo:
    elapsed_time: Timespan
    exit_code: int


class OutputView:
    def append(self, text: str) -> None:
        pass

    def show(self) -> None:
        pass


class ProcessListener:
    def on_data(self, text: str) -> None:
        pass

    def on_finished(self, completed_process: CompletedProcessInfo) -> None:
        pass



class AsyncProcess:
    def __init__(
        self,
        cmd: List[str],
        process_environment: Dict[str, str],
        cwd: Path,
        listener: ProcessListener,
    ) -> None:
        self.listener = listener
        self.start_time = Timestamp.now()
        self.killed = False

        self.process = subprocess.Popen(
            cmd,
            bufsize=0,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.PIPE,
            env=process_environment,
            cwd=cwd,
            shell=False,
            preexec_fn=os.setsid,  # Assigns a process group? Either way, it's required for os.killpg.
        )

        self.stdout_thread = threading.Thread(target=self.read_output)

    def start(self) -> None:
        self.stdout_thread.start()

    def kill(self) -> None:
        if self.killed:
            return

        self.killed = True
        os.killpg(self.process.pid, signal.SIGTERM)
        self.process.terminate()

    def is_active(self) -> bool:
        return self.exit_code() is None

    def exit_code(self) -> Optional[int]:
        return self.process.poll()

    def _clean_process(self) -> CompletedProcessInfo:
        self.process.wait()
        exit_code = self.exit_code()
        if exit_code is None:
            print(
                "The process should be done, but the exit code is undefined. Guess I'll scream."
            )
            raise ValueError("aaaa")
        return CompletedProcessInfo(
            Timespan(self.start_time, Timestamp.now()), exit_code
        )

    def read_output(self) -> None:
        decoder = codecs.getincrementaldecoder("utf-8")("replace")
        while self.process.stdout:
            data = decoder.decode(self.process.stdout.read(2**16))
            if data and not self.killed:
                self.listener.on_data(data)
            else:
                self.listener.on_finished(self._clean_process())
                break

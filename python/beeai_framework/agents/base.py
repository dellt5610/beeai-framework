# Copyright 2025 IBM Corp.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from pydantic import BaseModel

from beeai_framework.agents.types import AgentMeta, BeeAgentExecutionConfig, BeeRunInput, BeeRunOptions
from beeai_framework.cancellation import AbortSignal
from beeai_framework.context import Run, RunContext, RunContextInput, RunInstance
from beeai_framework.emitter import Emitter
from beeai_framework.memory import BaseMemory

T = TypeVar("T", bound=BaseModel)


class BaseAgent(ABC, Generic[T]):
    is_running: bool = False
    emitter: Emitter

    def run(
        self,
        prompt: str | None = None,
        execution: BeeAgentExecutionConfig | None = None,
        signal: AbortSignal | None = None,
    ) -> Run[T]:
        run_input = BeeRunInput(prompt=prompt)
        options = BeeRunOptions(execution=execution, signal=signal)

        if self.is_running:
            raise RuntimeError("Agent is already running!")

        self.is_running = True

        async def handler(context: RunContext) -> T:
            try:
                return await self._run(run_input, options, context)
            finally:
                self.is_running = False

        return RunContext.enter(
            RunInstance(emitter=self.emitter),
            RunContextInput(signal=options.signal if options else None, params=(run_input, options)),
            handler,
        )

    @abstractmethod
    async def _run(self, run_input: BeeRunInput, options: BeeRunOptions | None, context: RunContext) -> T:
        pass

    def destroy(self) -> None:
        self.emitter.destroy()

    @property
    @abstractmethod
    def memory(self) -> BaseMemory:
        pass

    @memory.setter
    @abstractmethod
    def memory(self, memory: BaseMemory) -> None:
        pass

    @property
    def meta(self) -> AgentMeta:
        return AgentMeta(
            name=self.__class__.__name__,
            description="",
            tools=[],
        )

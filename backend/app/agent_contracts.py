"""Validated maintained content and model output contracts."""
import json
import re
from typing import Any, Self

from pydantic import BaseModel, ConfigDict, Field, StrictBool, TypeAdapter, model_validator

from runner.harness import project_roots

from .schemas import ARTIFACT_MAX, TEXT_MAX
from .settings import Settings


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Prompts(StrictModel):
    builder: str = Field(min_length=1)
    coder: str = Field(min_length=1)
    repository_coder: str = Field(min_length=1)
    reviewer: str = Field(min_length=1)


class TestCase(StrictModel):
    input: Any
    expected: Any


class Fixture(StrictModel):
    name: str
    specification: str
    source: str
    output_path: str
    cases: list[TestCase] = Field(min_length=1, max_length=20)


class Draft(StrictModel):
    content: str = Field(min_length=1, max_length=ARTIFACT_MAX)
    summary: str = Field(min_length=1, max_length=TEXT_MAX)
    citations: list[str] = Field(default_factory=list, max_length=20)


class Patch(StrictModel):
    files: dict[str, str] = Field(min_length=1)
    summary: str = Field(min_length=1, max_length=TEXT_MAX)


class RepositoryProfile(StrictModel):
    name: str = Field(min_length=1, max_length=80)
    specification: str = Field(min_length=1, max_length=TEXT_MAX)
    files: list[str] = Field(min_length=1, max_length=20)
    entrypoint: str
    cases: list[TestCase] = Field(min_length=1, max_length=20)

    @model_validator(mode="after")
    def safe_scope(self) -> Self:
        if len(set(self.files)) != len(self.files):
            raise ValueError("Repository paths must be unique")
        for path in self.files:
            if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*(?:/[A-Za-z_][A-Za-z0-9_]*)*\.py", path):
                raise ValueError("Only explicit relative Python source paths are supported")
        project_roots(self.files)
        if not re.fullmatch(r"[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*:[A-Za-z]\w*", self.entrypoint):
            raise ValueError("Entrypoint must be a module and public callable")
        module, _ = self.entrypoint.split(":")
        if module.replace(".", "/") + ".py" not in self.files:
            raise ValueError("Entrypoint must be in the approved source set")
        return self

    def public_specification(self) -> dict[str, Any]:
        return self.model_dump(exclude={"cases"})


class Review(StrictModel):
    accepted: bool = Field(strict=True)
    findings: list[str] = Field(max_length=20)
    criterion_results: list[StrictBool] = Field(min_length=1, max_length=20)


def load_content(settings: Settings) -> tuple[Prompts, dict[str, Fixture]]:
    prompts = Prompts.model_validate_json((settings.data_directory / "prompts.json").read_text())
    fixtures = TypeAdapter(dict[str, Fixture]).validate_python(
        json.loads((settings.data_directory / "fixtures.json").read_text()))
    return prompts, fixtures


def load_profiles(settings: Settings) -> dict[str, RepositoryProfile]:
    return TypeAdapter(dict[str, RepositoryProfile]).validate_json(
        (settings.data_directory / "repositories.json").read_text())

import json
import logging
from typing import Generator, Tuple, Type, TypeVar

from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)
logger = logging.getLogger(__name__)


def stream_ndjson(file_path: str, model_cls: Type[T]) -> Generator[Tuple[str, T], None, None]:
    """Yield (raw_json_string, parsed_model) for each valid line in an NDJSON file."""
    with open(file_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                raw_dict = json.loads(line)
                parsed = model_cls.model_validate(raw_dict)
                yield (line, parsed)
            except (json.JSONDecodeError, ValidationError) as e:
                logger.warning(f"Skipping line {line_num} in {file_path}: {e}")
                continue

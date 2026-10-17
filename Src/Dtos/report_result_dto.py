from dataclasses import dataclass

from Src.Core.validator import validator


@dataclass(frozen=True)
class report_result_dto:
    """Хранит содержимое отчёта и независимый способ его выдачи."""

    content: str | bytes
    media_type: str
    file_extension: str
    download: bool = False

    def __post_init__(self) -> None:
        """Проверяет тип содержимого и метаданные результата."""
        if not isinstance(self.content, (str, bytes)):
            validator.validate(self.content, (str, bytes), field="content")
        validator.validate(self.media_type, str, field="media_type")
        validator.validate(self.file_extension, str, field="file_extension")
        validator.validate(self.download, bool, field="download")

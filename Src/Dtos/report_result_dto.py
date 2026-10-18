from Src.Core.validator import validator


class report_result_dto:
    """Результат форматирования: содержимое, MIME-тип, расширение и способ выдачи."""

    def __init__(self, content: str | bytes, media_type: str, file_extension: str, download: bool = False) -> None:
        """Проверяет и сохраняет содержимое и метаданные отчёта."""
        self.__set_content(content)
        self.__set_media_type(media_type)
        self.__set_file_extension(file_extension)
        self.__set_download(download)

    def __set_content(self, value: str | bytes) -> None:
        """Проверяет и сохраняет текст или байты, включая пустое содержимое."""
        if not isinstance(value, (str, bytes)):
            validator.validate(value, (str, bytes), field="content")
        self.__content = value

    def __set_media_type(self, value: str) -> None:
        """Проверяет и сохраняет MIME-тип."""
        validator.validate(value, str, field="media_type")
        self.__media_type = value

    def __set_file_extension(self, value: str) -> None:
        """Проверяет и сохраняет расширение файла."""
        validator.validate(value, str, field="file_extension")
        self.__file_extension = value

    def __set_download(self, value: bool) -> None:
        """Проверяет и сохраняет признак скачивания."""
        validator.validate(value, bool, field="download")
        self.__download = value

    @property
    def content(self) -> str | bytes:
        """Возвращает текст или байты отчёта."""
        return self.__content

    @property
    def media_type(self) -> str:
        """Возвращает MIME-тип содержимого."""
        return self.__media_type

    @property
    def file_extension(self) -> str:
        """Возвращает расширение файла без точки."""
        return self.__file_extension

    @property
    def download(self) -> bool:
        """Возвращает признак скачивания вложения."""
        return self.__download

    def __eq__(self, other):
        """Сравнивает результаты по содержимому и метаданным."""
        if not isinstance(other, report_result_dto):
            return NotImplemented
        return (self.content, self.media_type, self.file_extension, self.download) == (other.content, other.media_type, other.file_extension, other.download)

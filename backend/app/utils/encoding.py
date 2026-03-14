from codecs import BOM_UTF16_BE, BOM_UTF16_LE, BOM_UTF8


class EncodingDetectionError(ValueError):
    pass


def detect_text_encoding(raw_bytes: bytes) -> tuple[str, str]:
    if not raw_bytes:
        return "utf-8", ""

    if raw_bytes.startswith(BOM_UTF8):
        return "utf-8", raw_bytes.decode("utf-8-sig")

    if raw_bytes.startswith(BOM_UTF16_LE) or raw_bytes.startswith(BOM_UTF16_BE):
        return "utf-16", _decode_utf16(raw_bytes)

    try:
        return "utf-8", raw_bytes.decode("utf-8")
    except UnicodeDecodeError:
        pass

    if b"\x00" in raw_bytes:
        try:
            return "utf-16", _decode_utf16(raw_bytes)
        except UnicodeDecodeError:
            pass

    try:
        return "gbk", raw_bytes.decode("gbk")
    except UnicodeDecodeError as exc:
        raise EncodingDetectionError("Unable to detect text encoding. Supported encodings: UTF-8, GBK, UTF-16") from exc


def _decode_utf16(raw_bytes: bytes) -> str:
    try:
        decoded = raw_bytes.decode("utf-16")
    except UnicodeDecodeError as exc:
        raise EncodingDetectionError("Unable to detect text encoding. Supported encodings: UTF-8, GBK, UTF-16") from exc

    if decoded.startswith(("\ufeff", "\ufffe")):
        raise EncodingDetectionError("Unable to detect text encoding. Supported encodings: UTF-8, GBK, UTF-16")

    return decoded

from fastapi import HTTPException, UploadFile

from app.file_storage import save_upload


def upload(name: str, content_type: str, payload: bytes = b"media") -> UploadFile:
    return UploadFile(filename=name, file=None, headers={"content-type": content_type})


def test_save_upload_uses_safe_name_and_returns_public_url(tmp_path, monkeypatch):
    monkeypatch.setenv("CITYECHO_MEDIA_DIR", str(tmp_path))

    url, size = save_upload(upload("../../Ảnh POI.png", "image/png"), "images", "poi-1", b"png-data")

    assert url.startswith("/media/uploads/poi-1/images-")
    assert url.endswith(".png")
    assert size == 8
    assert len(list((tmp_path / "uploads" / "poi-1").glob("*.png"))) == 1


def test_save_upload_rejects_invalid_kind_and_poi_id():
    file = upload("audio.mp3", "audio/mpeg")

    try:
        save_upload(file, "other", "poi-1", b"data")
    except HTTPException as error:
        assert error.status_code == 422
    else:
        raise AssertionError("invalid media kind should be rejected")

    try:
        save_upload(file, "audios", "../outside", b"data")
    except HTTPException as error:
        assert error.status_code == 422
    else:
        raise AssertionError("invalid POI id should be rejected")


def test_save_upload_rejects_unsupported_or_oversized_file(tmp_path, monkeypatch):
    monkeypatch.setenv("CITYECHO_MEDIA_DIR", str(tmp_path))

    try:
        save_upload(upload("note.txt", "text/plain"), "images", "poi-1", b"data")
    except HTTPException as error:
        assert error.status_code == 422
    else:
        raise AssertionError("unsupported content type should be rejected")

    try:
        save_upload(upload("large.png", "image/png"), "images", "poi-1", b"x" * (5 * 1024 * 1024 + 1))
    except HTTPException as error:
        assert error.status_code == 422
    else:
        raise AssertionError("oversized image should be rejected")

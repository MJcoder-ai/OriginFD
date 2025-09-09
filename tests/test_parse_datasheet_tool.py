import base64
import pathlib
import sys
import pytest

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from services.orchestrator.tools.component_tools import ParseDatasheetTool

SAMPLE_PDF_B64 = (
    "JVBERi0xLjEKMSAwIG9iago8PCAvVHlwZSAvQ2F0YWxvZyAvUGFnZXMgMiAwIFIgPj4KZW5k"
    "b2JqCjIgMCBvYmoKPDwgL1R5cGUgL1BhZ2VzIC9LaWRzIFszIDAgUl0gL0NvdW50IDEgPj4K"
    "ZW5kb2JqCjMgMCBvYmoKPDwgL1R5cGUgL1BhZ2UgL1BhcmVudCAyIDAgUiAvTWVkaWFCb3gg"
    "WzAgMCA2MTIgNzkyXSAvQ29udGVudHMgNCAwIFIgL1Jlc291cmNlcyA8PCAvRm9udCA8PCAv"
    "RjEgNSAwIFIgPj4gPj4gPj4KZW5kb2JqCjQgMCBvYmoKPDwgL0xlbmd0aCAxMTIgPj4Kc3Ry"
    "ZWFtCkJUIC9GMSAyNCBUZiA1MCA3MDAgVGQgKFBvd2VyIFNUQzogNDAwIFcpIFRqIFQqIChW"
    "b2x0YWdlIE1QUDogNDAuNSBWKSBUaiBUKiAoQ3VycmVudCBNUFA6IDkuODggQSkgVGogVCog"
    "KEVmZmljaWVuY3k6IDIwLjMgJSkgVGogRVQKZW5kc3RyZWFtCmVuZG9iago1IDAgb2JqCjw8"
    "IC9UeXBlIC9Gb250IC9TdWJ0eXBlIC9UeXBlMSAvQmFzZUZvbnQgL0hlbHZldGljYSA+Pgpl"
    "bmRvYmoKeHJlZgowIDYKMDAwMDAwMDAwMCA2NTUzNSBmIAowMDAwMDAwMDEwIDAwMDAwIG4g"
    "CjAwMDAwMDAwNTYgMDAwMDAgbiAKMDAwMDAwMDEwNSAwMDAwMCBuIAowMDAwMDAwMjYzIDAw"
    "MDAwIG4gCjAwMDAwMDA0MDcgMDAwMDAgbiAKdHJhaWxlcgo8PCAvUm9vdCAxIDAgUiAvU2l6"
    "ZSA2ID4+CnN0YXJ0eHJlZgo0NjkKJSVFT0YK"
)


@pytest.mark.asyncio
async def test_parse_datasheet_success(tmp_path):
    pdf_path = tmp_path / "sample.pdf"
    pdf_path.write_bytes(base64.b64decode(SAMPLE_PDF_B64))
    tool = ParseDatasheetTool()
    result = await tool.execute(
        {"datasheet_url": f"file://{pdf_path}", "component_type": "pv_module"}
    )
    assert result.success is True
    assert result.outputs["specifications"]["electrical"]["power_stc_w"] == 400
    assert result.outputs["pages_processed"] == 1


@pytest.mark.asyncio
async def test_parse_datasheet_invalid_url():
    tool = ParseDatasheetTool()
    result = await tool.execute(
        {"datasheet_url": "file:///nonexistent/path.pdf", "component_type": "pv_module"}
    )
    assert result.success is False
    assert result.errors

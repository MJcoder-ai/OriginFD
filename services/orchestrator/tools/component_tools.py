"""
AI tools for component management following ODL-SD v4.1 CMS.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List

from .registry import BaseTool, ToolMetadata, ToolResult

logger = logging.getLogger(__name__)


class ParseDatasheetTool(BaseTool):
    """AI tool for parsing component datasheets and extracting specifications."""

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="parse_component_datasheet",
            version="1.0.0",
            description="Extract technical specifications from component datasheets using AI",
            category="component_management",
            inputs_schema={
                "type": "object",
                "properties": {
                    "datasheet_url": {
                        "type": "string",
                        "format": "uri",
                        "description": "URL to the component datasheet PDF",
                    },
                    "component_type": {
                        "type": "string",
                        "enum": [
                            "pv_module",
                            "inverter",
                            "battery",
                            "combiner",
                            "meter",
                            "other",
                        ],
                        "description": "Type of component for context-aware parsing",
                    },
                    "extract_images": {
                        "type": "boolean",
                        "default": True,
                        "description": "Extract images and diagrams from datasheet",
                    },
                    "extract_symbols": {
                        "type": "boolean",
                        "default": True,
                        "description": "Extract electrical symbols and schematics",
                    },
                    "target_language": {
                        "type": "string",
                        "default": "en",
                        "description": "Target language for extracted text",
                    },
                },
                "required": ["datasheet_url", "component_type"],
                "additionalProperties": False,
            },
            outputs_schema={
                "type": "object",
                "properties": {
                    "specifications": {
                        "type": "object",
                        "description": "Extracted technical specifications",
                        "properties": {
                            "electrical": {"type": "object"},
                            "mechanical": {"type": "object"},
                            "thermal": {"type": "object"},
                            "environmental": {"type": "object"},
                            "certifications": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                        },
                    },
                    "extracted_images": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "url": {"type": "string"},
                                "type": {"type": "string"},
                                "description": {"type": "string"},
                                "page": {"type": "integer"},
                            },
                        },
                    },
                    "confidence_score": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 1,
                        "description": "Confidence in extraction accuracy",
                    },
                    "processing_time_ms": {"type": "integer"},
                    "pages_processed": {"type": "integer"},
                    "warnings": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["specifications", "confidence_score"],
                "additionalProperties": False,
            },
            side_effects="write",
            rbac_scope=["component_write", "ai_parse"],
            execution_time_estimate_ms=5000,
            psu_cost_estimate=10,
            tags=["ai", "parsing", "datasheet", "ocr"],
        )

    async def execute(self, inputs: Dict[str, Any]) -> ToolResult:
        """Execute datasheet parsing."""
        start_time = datetime.utcnow()

        try:
            # Validate inputs
            validated_inputs = self.validate_inputs(inputs)

            datasheet_url = validated_inputs["datasheet_url"]
            component_type = validated_inputs["component_type"]
            extract_images = validated_inputs.get("extract_images", True)
            extract_symbols = validated_inputs.get("extract_symbols", True)

            logger.info(f"Parsing datasheet: {datasheet_url} (type: {component_type})")

            # TODO: Implement actual AI parsing logic
            # This would integrate with:
            # - PDF processing library (PyPDF2, pdfplumber)
            # - OCR service (Tesseract, Google Vision API)
            # - AI/ML model for specification extraction
            # - Image extraction and classification

            warnings: List[str] = []

            # 1. Download the datasheet PDF
            pdf_bytes = await self._download_pdf(datasheet_url)

            # 2. Parse PDF and optionally extract images
            text, images, pages_processed, parse_warnings = self._extract_pdf_content(
                pdf_bytes, extract_images
            )
            warnings.extend(parse_warnings)

            # 3. Use AI model to extract structured specifications
            specifications, confidence = await self._extract_specifications_ai(
                text, component_type, validated_inputs.get("target_language", "en")
            )

            processing_time = int(
                (datetime.utcnow() - start_time).total_seconds() * 1000
            )

            outputs = {
                "specifications": specifications,
                "extracted_images": images if extract_images else [],
                "confidence_score": confidence,
                "processing_time_ms": processing_time,
                "pages_processed": pages_processed,
                "warnings": warnings,
            }

            return ToolResult(
                success=True,
                outputs=outputs,
                execution_time_ms=processing_time,
                intent=f"Parsed {component_type} datasheet with {outputs['confidence_score']:.0%} confidence",
            )

        except Exception as e:
            logger.error(f"Datasheet parsing failed: {str(e)}")
            return ToolResult(
                success=False,
                errors=[str(e)],
                execution_time_ms=int(
                    (datetime.utcnow() - start_time).total_seconds() * 1000
                ),
                intent="Failed to parse component datasheet",
            )

    # --- Parsing helpers -------------------------------------------------

    async def _download_pdf(self, url: str) -> bytes:
        """Download PDF from HTTP(S) or file URI asynchronously."""
        try:
            if url.startswith("file://"):
                path = url.replace("file://", "")
                import asyncio
                from pathlib import Path

                data = await asyncio.to_thread(Path(path).read_bytes)
                if not data.startswith(b"%PDF"):
                    raise ValueError("Provided file is not a valid PDF")
                return data

            import httpx

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                content = response.content
            if not content.startswith(b"%PDF"):
                raise ValueError("URL did not return a valid PDF")
            return content
        except Exception as e:
            raise RuntimeError(f"Failed to download datasheet: {e}") from e

    def _extract_pdf_content(
        self, pdf_bytes: bytes, extract_images: bool
    ) -> tuple[str, List[Dict[str, Any]], int, List[str]]:
        """Extract text and optionally images from PDF."""
        import io

        warnings: List[str] = []
        images: List[Dict[str, Any]] = []
        pages_processed = 0

        try:
            from pypdf import PdfReader
        except Exception as e:
            raise RuntimeError("pypdf library is required for PDF parsing") from e

        try:
            reader = PdfReader(io.BytesIO(pdf_bytes))
        except Exception as e:
            raise RuntimeError("Invalid or corrupted PDF") from e
        texts: List[str] = []
        for page_number, page in enumerate(reader.pages, start=1):
            pages_processed += 1
            page_text = page.extract_text() or ""
            if not page_text.strip():
                ocr_text = self._ocr_page(pdf_bytes, page_number)
                if ocr_text:
                    page_text = ocr_text
                else:
                    warnings.append(
                        f"No text found on page {page_number}; OCR unavailable"
                    )
            texts.append(page_text)

            if extract_images:
                images.extend(self._extract_images_from_page(page, page_number))

        return "\n".join(texts), images, pages_processed, warnings

    def _ocr_page(self, pdf_bytes: bytes, page_number: int) -> str:
        """Attempt OCR on a PDF page. Returns extracted text or empty string."""
        try:
            import pytesseract  # type: ignore
            from pdf2image import convert_from_bytes  # type: ignore
        except Exception:
            return ""

        try:
            images = convert_from_bytes(
                pdf_bytes, first_page=page_number, last_page=page_number
            )
            if not images:
                return ""
            return pytesseract.image_to_string(images[0])
        except Exception:
            return ""

    def _extract_images_from_page(
        self, page: Any, page_number: int
    ) -> List[Dict[str, Any]]:
        """Extract images from a PDF page."""
        extracted: List[Dict[str, Any]] = []
        try:
            xobjects = page["/Resources"].get("/XObject")
            if not xobjects:
                return extracted
            xobjects = xobjects.get_object()
            for name in xobjects:
                xobj = xobjects[name]
                if xobj.get("/Subtype") != "/Image":
                    continue
                try:
                    import base64
                    import io as _io

                    from PIL import Image

                    data = xobj.get_data()
                    mode = "RGB"
                    if xobj.get("/ColorSpace") == "/DeviceCMYK":
                        mode = "CMYK"
                    elif xobj.get("/ColorSpace") == "/DeviceGray":
                        mode = "L"
                    img = Image.frombytes(mode, xobj["/Width"], xobj["/Height"], data)
                    buf = _io.BytesIO()
                    img.save(buf, format="PNG")
                    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
                    extracted.append(
                        {
                            "url": f"data:image/png;base64,{b64}",
                            "type": "image",
                            "description": "extracted",
                            "page": page_number,
                        }
                    )
                except Exception:
                    continue
        except Exception:
            pass
        return extracted

    async def _extract_specifications_ai(
        self, text: str, component_type: str, target_language: str
    ) -> tuple[Dict[str, Any], float]:
        """Use an AI model to extract structured specifications."""
        if not text.strip():
            raise RuntimeError("No text available for specification extraction")

        prompt = (
            "Extract the technical specifications for a {component} from the"
            " following datasheet text. Respond in JSON."
        ).format(component=component_type)
        prompt += f"\n{text}"

        try:
            from openai import AsyncOpenAI

            client = AsyncOpenAI()
            completion = await client.responses.create(
                model="gpt-4o-mini",
                input=[{"role": "user", "content": prompt}],
                max_output_tokens=500,
            )
            content = completion.output[0].content[0].text  # type: ignore
            specs = json.loads(content)
            return specs, 0.9
        except Exception as e:
            logger.warning(
                f"AI extraction failed, falling back to heuristic parsing: {e}"
            )
            return self._heuristic_extract(text, component_type), 0.5

    def _heuristic_extract(self, text: str, component_type: str) -> Dict[str, Any]:
        """Basic heuristic extraction if AI model unavailable."""
        import re

        specs: Dict[str, Any] = {
            "electrical": {},
            "mechanical": {},
            "thermal": {},
            "environmental": {},
            "certifications": [],
        }

        if component_type == "pv_module":
            m = re.search(r"Power STC:?\s*(\d+)\s*W", text, re.I)
            if m:
                specs["electrical"]["power_stc_w"] = int(m.group(1))
            m = re.search(r"Voltage MPP:?\s*(\d+\.?\d*)\s*V", text, re.I)
            if m:
                specs["electrical"]["voltage_mpp_v"] = float(m.group(1))
            m = re.search(r"Current MPP:?\s*(\d+\.?\d*)\s*A", text, re.I)
            if m:
                specs["electrical"]["current_mpp_a"] = float(m.group(1))
            m = re.search(r"Efficiency:?\s*(\d+\.?\d*)\s*%", text, re.I)
            if m:
                specs["electrical"]["efficiency_pct"] = float(m.group(1))

        return specs


class ComponentDeduplicationTool(BaseTool):
    """AI tool for detecting duplicate components using multiple matching strategies."""

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="deduplicate_components",
            version="1.0.0",
            description="Detect duplicate components using brand, part number, GTIN, and specification matching",
            category="component_management",
            inputs_schema={
                "type": "object",
                "properties": {
                    "component_data": {
                        "type": "object",
                        "description": "Component data to check for duplicates",
                        "properties": {
                            "brand": {"type": "string"},
                            "part_number": {"type": "string"},
                            "rating_w": {"type": "integer"},
                            "gtin": {"type": "string"},
                            "specifications": {"type": "object"},
                        },
                        "required": ["brand", "part_number", "rating_w"],
                    },
                    "similarity_threshold": {
                        "type": "number",
                        "minimum": 0.0,
                        "maximum": 1.0,
                        "default": 0.8,
                        "description": "Similarity threshold for fuzzy matching",
                    },
                    "check_specifications": {
                        "type": "boolean",
                        "default": True,
                        "description": "Include technical specifications in matching",
                    },
                },
                "required": ["component_data"],
                "additionalProperties": False,
            },
            outputs_schema={
                "type": "object",
                "properties": {
                    "is_duplicate": {"type": "boolean"},
                    "matches": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "component_id": {"type": "string"},
                                "match_type": {"type": "string"},
                                "similarity_score": {"type": "number"},
                                "differences": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                },
                            },
                        },
                    },
                    "suggested_action": {"type": "string"},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                },
                "required": ["is_duplicate", "matches", "confidence"],
                "additionalProperties": False,
            },
            side_effects="read",
            rbac_scope=["component_read"],
            execution_time_estimate_ms=1000,
            psu_cost_estimate=2,
            tags=["ai", "deduplication", "matching"],
        )

    async def execute(self, inputs: Dict[str, Any]) -> ToolResult:
        """Execute component deduplication."""
        start_time = datetime.utcnow()

        try:
            validated_inputs = self.validate_inputs(inputs)
            component_data = validated_inputs["component_data"]
            threshold = validated_inputs.get("similarity_threshold", 0.8)

            # TODO: Implement actual deduplication logic
            # This would:
            # - Query database for similar components
            # - Use fuzzy string matching for brand/part names
            # - Compare GTIN codes
            # - Use ML similarity for specifications
            # - Apply business rules for matching

            # Mock implementation
            mock_matches = []
            is_duplicate = len(mock_matches) > 0

            outputs = {
                "is_duplicate": is_duplicate,
                "matches": mock_matches,
                "suggested_action": (
                    "create_new" if not is_duplicate else "merge_or_variant"
                ),
                "confidence": 0.92,
            }

            processing_time = int(
                (datetime.utcnow() - start_time).total_seconds() * 1000
            )

            return ToolResult(
                success=True,
                outputs=self.validate_outputs(outputs),
                execution_time_ms=processing_time,
                intent=f"Checked for duplicates - {'found matches' if is_duplicate else 'no duplicates found'}",
            )

        except Exception as e:
            logger.error(f"Component deduplication failed: {str(e)}")
            return ToolResult(
                success=False,
                errors=[str(e)],
                execution_time_ms=int(
                    (datetime.utcnow() - start_time).total_seconds() * 1000
                ),
                intent="Failed to check for duplicate components",
            )


class ComponentClassificationTool(BaseTool):
    """AI tool for auto-classifying components using UNSPSC, eCl@ss, and HS codes."""

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="classify_component",
            version="1.0.0",
            description="Automatically classify components using international standards (UNSPSC, eCl@ss, HS codes)",
            category="component_management",
            inputs_schema={
                "type": "object",
                "properties": {
                    "component_data": {
                        "type": "object",
                        "properties": {
                            "brand": {"type": "string"},
                            "part_number": {"type": "string"},
                            "category": {"type": "string"},
                            "subcategory": {"type": "string"},
                            "description": {"type": "string"},
                            "specifications": {"type": "object"},
                        },
                        "required": ["brand", "part_number"],
                    },
                    "classification_systems": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["unspsc", "eclass", "hs_code"],
                        },
                        "default": ["unspsc", "eclass", "hs_code"],
                    },
                },
                "required": ["component_data"],
                "additionalProperties": False,
            },
            outputs_schema={
                "type": "object",
                "properties": {
                    "classifications": {
                        "type": "object",
                        "properties": {
                            "unspsc": {"type": "string", "pattern": "^\\d{8}$"},
                            "eclass": {"type": "string"},
                            "hs_code": {
                                "type": "string",
                                "pattern": "^\\d{6}(\\d{2,4})?$",
                            },
                            "gtin": {"type": "string"},
                        },
                    },
                    "confidence_scores": {
                        "type": "object",
                        "properties": {
                            "unspsc": {"type": "number", "minimum": 0, "maximum": 1},
                            "eclass": {"type": "number", "minimum": 0, "maximum": 1},
                            "hs_code": {"type": "number", "minimum": 0, "maximum": 1},
                        },
                    },
                    "suggested_category": {"type": "string"},
                    "suggested_subcategory": {"type": "string"},
                },
                "required": ["classifications", "confidence_scores"],
                "additionalProperties": False,
            },
            side_effects="none",
            rbac_scope=["component_read"],
            execution_time_estimate_ms=800,
            psu_cost_estimate=1,
            tags=["ai", "classification", "standards"],
        )

    async def execute(self, inputs: Dict[str, Any]) -> ToolResult:
        """Execute component classification."""
        start_time = datetime.utcnow()

        try:
            validated_inputs = self.validate_inputs(inputs)
            component_data = validated_inputs["component_data"]
            systems = validated_inputs.get(
                "classification_systems", ["unspsc", "eclass", "hs_code"]
            )

            # TODO: Implement actual classification logic
            # This would use:
            # - ML models trained on classification standards
            # - Keyword matching and semantic similarity
            # - Integration with official classification APIs
            # - Business rules for energy components

            # Mock implementation based on component type
            category = component_data.get("category", "").lower()
            subcategory = component_data.get("subcategory", "").lower()

            mock_classifications = {}
            mock_confidence = {}

            if "pv" in category or "solar" in category:
                mock_classifications = {
                    "unspsc": "26111701",  # Solar energy generation equipment
                    "eclass": "27-02-26-01",  # Photovoltaic modules
                    "hs_code": "854140",  # Photosensitive semiconductor devices
                }
                mock_confidence = {"unspsc": 0.95, "eclass": 0.92, "hs_code": 0.88}
            elif "inverter" in subcategory:
                mock_classifications = {
                    "unspsc": "26111702",  # Power inverters
                    "eclass": "27-02-26-02",  # Inverters
                    "hs_code": "850440",  # Static converters
                }
                mock_confidence = {"unspsc": 0.93, "eclass": 0.90, "hs_code": 0.85}
            else:
                # Generic electrical equipment
                mock_classifications = {
                    "unspsc": "26100000",  # Electrical equipment
                    "eclass": "27-00-00-00",  # Electrical engineering
                    "hs_code": "850000",  # Electrical machinery
                }
                mock_confidence = {"unspsc": 0.70, "eclass": 0.65, "hs_code": 0.60}

            outputs = {
                "classifications": mock_classifications,
                "confidence_scores": mock_confidence,
                "suggested_category": (
                    "generation" if "pv" in category else "conversion"
                ),
                "suggested_subcategory": (
                    "pv_module" if "pv" in category else "inverter"
                ),
            }

            processing_time = int(
                (datetime.utcnow() - start_time).total_seconds() * 1000
            )

            return ToolResult(
                success=True,
                outputs=self.validate_outputs(outputs),
                execution_time_ms=processing_time,
                intent=f"Classified component with {max(mock_confidence.values()):.0%} confidence",
            )

        except Exception as e:
            logger.error(f"Component classification failed: {str(e)}")
            return ToolResult(
                success=False,
                errors=[str(e)],
                execution_time_ms=int(
                    (datetime.utcnow() - start_time).total_seconds() * 1000
                ),
                intent="Failed to classify component",
            )


class ComponentRecommendationTool(BaseTool):
    """AI tool for recommending similar or compatible components."""

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="recommend_components",
            version="1.0.0",
            description="Recommend similar or compatible components based on specifications and project requirements",
            category="component_management",
            inputs_schema={
                "type": "object",
                "properties": {
                    "requirements": {
                        "type": "object",
                        "description": "Project requirements and constraints",
                        "properties": {
                            "domain": {"type": "string"},
                            "scale": {"type": "string"},
                            "power_range_w": {
                                "type": "object",
                                "properties": {
                                    "min": {"type": "number"},
                                    "max": {"type": "number"},
                                },
                            },
                            "voltage_range_v": {
                                "type": "object",
                                "properties": {
                                    "min": {"type": "number"},
                                    "max": {"type": "number"},
                                },
                            },
                            "budget_range": {
                                "type": "object",
                                "properties": {
                                    "min": {"type": "number"},
                                    "max": {"type": "number"},
                                },
                            },
                            "certifications_required": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "environmental_conditions": {"type": "object"},
                        },
                    },
                    "existing_component_id": {
                        "type": "string",
                        "description": "Find alternatives to this component",
                    },
                    "recommendation_type": {
                        "type": "string",
                        "enum": ["similar", "compatible", "alternative", "upgrade"],
                        "default": "similar",
                    },
                    "max_results": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 50,
                        "default": 10,
                    },
                },
                "additionalProperties": False,
            },
            outputs_schema={
                "type": "object",
                "properties": {
                    "recommendations": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "component_id": {"type": "string"},
                                "match_score": {
                                    "type": "number",
                                    "minimum": 0,
                                    "maximum": 1,
                                },
                                "match_reasons": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                },
                                "key_differences": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                },
                                "price_comparison": {"type": "string"},
                                "availability": {"type": "string"},
                            },
                        },
                    },
                    "search_strategy": {"type": "string"},
                    "total_candidates": {"type": "integer"},
                },
                "required": ["recommendations"],
                "additionalProperties": False,
            },
            side_effects="read",
            rbac_scope=["component_read"],
            execution_time_estimate_ms=1500,
            psu_cost_estimate=3,
            tags=["ai", "recommendation", "compatibility"],
        )

    async def execute(self, inputs: Dict[str, Any]) -> ToolResult:
        """Execute component recommendation."""
        start_time = datetime.utcnow()

        try:
            validated_inputs = self.validate_inputs(inputs)

            # TODO: Implement actual recommendation logic
            # This would use:
            # - Vector similarity search on specifications
            # - Compatibility matrices for component types
            # - Price and availability data
            # - User preference learning
            # - Project context and constraints

            # Mock implementation
            outputs = {
                "recommendations": [
                    {
                        "component_id": "CMP:JINKO:JKM400M:400W:REV1",
                        "match_score": 0.95,
                        "match_reasons": [
                            "Similar power rating",
                            "Same technology",
                            "Compatible voltage",
                        ],
                        "key_differences": [
                            "5W higher power",
                            "Slightly larger dimensions",
                        ],
                        "price_comparison": "5% higher",
                        "availability": "in_stock",
                    }
                ],
                "search_strategy": "specification_similarity",
                "total_candidates": 45,
            }

            processing_time = int(
                (datetime.utcnow() - start_time).total_seconds() * 1000
            )

            return ToolResult(
                success=True,
                outputs=self.validate_outputs(outputs),
                execution_time_ms=processing_time,
                intent=f"Found {len(outputs['recommendations'])} component recommendations",
            )

        except Exception as e:
            logger.error(f"Component recommendation failed: {str(e)}")
            return ToolResult(
                success=False,
                errors=[str(e)],
                execution_time_ms=int(
                    (datetime.utcnow() - start_time).total_seconds() * 1000
                ),
                intent="Failed to generate component recommendations",
            )

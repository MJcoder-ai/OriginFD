# ODL-SD v4.1 – Component Management Supplement (CMS)

**Version:** 1.0
**Scope:** This supplement defines the complete Component Management model, workflows, and standards alignment for the platform. It extends **ODL‑SD v4.1** by adding a well-bounded `component_management` object, designed to be embedded in each `libraries.components[]` record or referenced alongside it at the document root. It covers creation, deduplication, supplier & pricing, RFQ/bidding, orders & shipments, logistics tracking, inventory, installation, warranty, returns/RMA, compliance, approvals, audit, analytics, and AI‑assisted automation.

---

## 1) Compatibility & Integration Points with ODL‑SD v4.1

- **Primary anchor:** `libraries.components[]` — each component may include a `component_management` object.
- **Cross-links:**
  - `governance` (change requests, approvals, phase gates).
  - `operations` (commissioning & service actions; field instances).
  - `finance` (costs, taxes, budgets, currency units).
  - `instances` (per‑site, per‑serial placements and connections).
  - `audit` (who/what/when for every change).
- **RBAC:** Roles & rights (R/W/P/A/X/S) govern create, edit, approve, merge, execute.
- **Doc control:** All source documents (datasheets, certificates, warranty, installation) are versioned and immutable.

> **Usage pattern**: Embed `component_management` inside each `libraries.components[i]`. For shared/centralized operation, it may also be kept under a document‑root collection keyed by `component_id` and referenced from `libraries.components[i].component_ref`.

---

## 2) JSON Schema — Complete Component Management (Draft 2020‑12)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://odl-sd.org/schemas/v4.1/component_management.json",
  "title": "ODL-SD v4.1 – Component Management (Supplement)",
  "type": "object",
  "properties": {
    "component_management": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "version": { "type": "string", "default": "1.0" },
        "component_ref": {
          "type": "string",
          "description": "ID or JSON Pointer to libraries.components[] entry",
          "minLength": 1
        },
        "status": {
          "description": "Lifecycle state inside component management gate",
          "enum": [
            "draft","parsed","enriched","dedupe_pending","compliance_pending",
            "approved","available","rfq_open","rfq_awarded","purchasing",
            "ordered","shipped","received","installed","commissioned",
            "operational","warranty_active","retired","archived"
          ]
        },
        "component_identity": {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "component_id": {
              "type": "string",
              "description": "Canonical ID CMP:Brand:Part:Rating:Rev",
              "pattern": "^CMP:[A-Z0-9._-]{1,64}:[A-Z0-9._/-]{1,64}:[0-9]{1,7}W:[A-Z0-9._-]{1,16}$"
            },
            "brand": { "type": "string", "minLength": 1, "maxLength": 64 },
            "part_number": { "type": "string", "minLength": 1, "maxLength": 64 },
            "rating_w": { "type": "integer", "minimum": 1, "maximum": 1000000 },
            "name": {
              "type": "string",
              "description": "Unique name 'Brand_PartNumber_RatingW'",
              "pattern": "^[A-Za-z0-9][A-Za-z0-9 ._/-]*_[A-Za-z0-9 ._/-]+_[0-9]+W$"
            },
            "classification": {
              "type": "object",
              "additionalProperties": false,
              "properties": {
                "unspsc": { "type": "string", "pattern": "^\\d{8}$" },
                "eclass": { "type": "string", "maxLength": 32 },
                "hs_code": { "type": "string", "pattern": "^\\d{6}(\\d{2,4})?$" },
                "gtin": { "type": "string", "pattern": "^(?:\\d{8}|\\d{12}|\\d{13}|\\d{14})$" }
              }
            }
          },
          "required": ["component_id", "brand", "part_number", "rating_w", "name"]
        },
        "source_documents": {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "datasheet": { "$ref": "#/$defs/documentRef" },
            "additional": {
              "type": "array",
              "items": { "$ref": "#/$defs/documentRef" },
              "maxItems": 100
            },
            "images": {
              "type": "array",
              "items": {
                "type": "object",
                "additionalProperties": false,
                "properties": {
                  "source": { "type": "string", "maxLength": 64 },
                  "url": { "type": "string", "format": "uri" },
                  "description": { "type": "string", "maxLength": 200 }
                },
                "required": ["url"]
              },
              "maxItems": 200
            }
          },
          "required": ["datasheet"]
        },
        "tracking_policy": { "$ref": "#/$defs/trackingPolicy" },
        "approvals": {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "requested": { "type": "boolean" },
            "records": { "type": "array", "items": { "$ref": "#/$defs/approvalRecord" }, "maxItems": 200 }
          },
          "required": ["requested"]
        },
        "supplier_chain": {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "suppliers": { "type": "array", "items": { "$ref": "#/$defs/supplier" }, "minItems": 1 },
            "rfq": { "$ref": "#/$defs/rfq" },
            "commercials": {
              "type": "object",
              "additionalProperties": false,
              "properties": {
                "base_cost": { "type": "number", "minimum": 0 },
                "margins": {
                  "type": "object",
                  "additionalProperties": false,
                  "properties": {
                    "operations_pct": { "$ref": "#/$defs/percent" },
                    "it_pct": { "$ref": "#/$defs/percent" },
                    "distributor_pct": { "$ref": "#/$defs/percent" },
                    "commission_pct": { "$ref": "#/$defs/percent" },
                    "vat_pct": { "$ref": "#/$defs/percent" },
                    "import_tax_pct": { "$ref": "#/$defs/percent" },
                    "total_margin_pct": { "$ref": "#/$defs/percent" },
                    "currency": { "$ref": "#/$defs/currencyCode" },
                    "net_price": { "type": "number", "minimum": 0 }
                  },
                  "required": ["currency", "total_margin_pct", "net_price"]
                }
              }
            }
          },
          "required": ["suppliers"]
        },
        "order_management": {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "rfq_enabled": { "type": "boolean", "default": true },
            "bidding_fee_pct": { "$ref": "#/$defs/percent" },
            "orders": {
              "type": "array",
              "items": { "$ref": "#/$defs/purchaseOrder" },
              "maxItems": 100000
            },
            "shipments": {
              "type": "array",
              "items": { "$ref": "#/$defs/shipment" },
              "maxItems": 100000
            }
          }
        },
        "inventory": {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "stocks": { "type": "array", "items": { "$ref": "#/$defs/inventoryRecord" } }
          }
        },
        "warranty": {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "terms": {
              "type": "object",
              "additionalProperties": false,
              "properties": {
                "type": { "enum": ["product", "performance", "combined"] },
                "duration_years": { "type": "integer", "minimum": 0, "maximum": 50 },
                "coverage_min_pct": { "$ref": "#/$defs/percent" }
              },
              "required": ["type", "duration_years"]
            },
            "claims": { "type": "array", "items": { "$ref": "#/$defs/warrantyClaim" }, "maxItems": 100000 }
          }
        },
        "returns": {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "policies": {
              "type": "object",
              "additionalProperties": false,
              "properties": {
                "return_window_days": { "type": "integer", "minimum": 0, "maximum": 365 },
                "restocking_fee_pct": { "$ref": "#/$defs/percent" },
                "requires_rma": { "type": "boolean", "default": true },
                "allow_exchanges": { "type": "boolean", "default": true }
              }
            },
            "records": { "type": "array", "items": { "$ref": "#/$defs/returnRecord" }, "maxItems": 100000 }
          }
        },
        "traceability": {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "blockchain_tx": { "type": "string", "maxLength": 128 },
            "qr_uri": { "type": "string", "format": "uri" },
            "dpp": {
              "type": "object",
              "additionalProperties": false,
              "properties": {
                "enabled": { "type": "boolean", "default": false },
                "schema": { "type": "string", "maxLength": 64 },
                "uri": { "type": "string", "format": "uri" }
              }
            }
          }
        },
        "compliance": {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "standards": { "type": "array", "items": { "$ref": "#/$defs/standardRef" }, "maxItems": 200 },
            "certificates": { "type": "array", "items": { "$ref": "#/$defs/documentRef" }, "maxItems": 200 },
            "pv_checks": { "type": "object", "properties": { "iec_61215": { "type": "boolean" }, "iec_61730": { "type": "boolean" } } }
          }
        },
        "ai_logs": {
          "type": "array",
          "items": {
            "type": "object",
            "additionalProperties": false,
            "properties": {
              "action": {
                "enum": [
                  "parse_datasheet","extract_images","normalize_fields","dedupe_suggest",
                  "suggest_pricing","negotiate_bid","create_po","update_margins",
                  "classify_tracking","route_return"
                ]
              },
              "agent": { "type": "string", "maxLength": 64 },
              "timestamp": { "type": "string", "format": "date-time" },
              "changes": { "type": "string", "maxLength": 2000 }
            },
            "required": ["action", "timestamp"]
          },
          "maxItems": 100000
        },
        "audit": {
          "type": "array",
          "items": { "$ref": "#/$defs/auditRecord" },
          "maxItems": 100000
        },
        "analytics": {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "kpis": {
              "type": "object",
              "properties": {
                "cost_saving_pct": { "$ref": "#/$defs/percent" },
                "on_time_delivery_pct": { "$ref": "#/$defs/percent" },
                "avg_dwell_hours": { "type": "number", "minimum": 0 },
                "return_rate_pct": { "$ref": "#/$defs/percent" },
                "warranty_claim_rate_pct": { "$ref": "#/$defs/percent" }
              }
            }
          }
        }
      },
      "required": [
        "status","component_identity","source_documents","tracking_policy","supplier_chain"
      ]
    }
  },
  "required": ["component_management"],
  "$defs": {
    "percent": { "type": "number", "minimum": 0, "maximum": 100 },
    "currencyCode": { "type": "string", "pattern": "^[A-Z]{3}$", "examples": ["USD","EUR","GBP","AUD"] },
    "roleEnum": { "enum": ["engineer","expert","supplier_manager","project_manager","compliance_officer","asset_owner"] },
    "uomCode": { "enum": ["pcs","m","kg","set","pair","roll"] },

    "documentRef": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "type": { "enum": ["datasheet","warranty","installation","faq","certificate","test_report","other"] },
        "url": { "type": "string", "format": "uri" },
        "hash": { "type": "string", "pattern": "^sha256:[0-9a-f]{64}$" },
        "parsed_at": { "type": "string", "format": "date-time" },
        "pages": { "type": "array", "items": { "type": "integer", "minimum": 1 }, "maxItems": 300 }
      },
      "required": ["type","url"]
    },

    "standardRef": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "code": { "type": "string", "maxLength": 32 },
        "title": { "type": "string", "maxLength": 200 },
        "edition": { "type": "string", "maxLength": 32 },
        "status": { "enum": ["required","recommended","optional"] }
      },
      "required": ["code","title"]
    },

    "approvalRecord": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "role": { "$ref": "#/$defs/roleEnum" },
        "outcome": { "enum": ["approved","rejected","waived"] },
        "comment": { "type": "string", "maxLength": 500 },
        "timestamp": { "type": "string", "format": "date-time" }
      },
      "required": ["role","outcome","timestamp"]
    },

    "supplier": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "id": { "type": "string", "pattern": "^SUP-[A-Z0-9]{3,}$" },
        "name": { "type": "string", "minLength": 2, "maxLength": 120 },
        "gln": { "type": "string", "pattern": "^\\d{13}$" },
        "contact": {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "email": { "type": "string", "format": "email" },
            "phone": { "type": "string", "maxLength": 32 }
          }
        },
        "status": { "enum": ["draft","approved","inactive"] },
        "approved_at": { "type": "string", "format": "date-time" }
      },
      "required": ["id","name","status"]
    },

    "price": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "amount": { "type": "number", "minimum": 0 },
        "currency": { "$ref": "#/$defs/currencyCode" }
      },
      "required": ["amount","currency"]
    },

    "bid": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "id": { "type": "string", "pattern": "^BID-[A-Z0-9]{5,}$" },
        "supplier_id": { "type": "string" },
        "price": { "$ref": "#/$defs/price" },
        "incoterms": { "enum": ["EXW","FOB","CIF","DAP","DDP"] },
        "valid_until": { "type": "string", "format": "date-time" },
        "date": { "type": "string", "format": "date-time" },
        "status": { "enum": ["won","lost","pending"] }
      },
      "required": ["id","supplier_id","price","date","status"]
    },

    "rfq": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "rfq_id": { "type": "string", "pattern": "^RFQ-[A-Z0-9]{5,}$" },
        "status": { "enum": ["draft","issued","bidding","evaluating","awarded","cancelled"] },
        "round": { "type": "integer", "minimum": 1 },
        "deadline": { "type": "string", "format": "date-time" },
        "lines": {
          "type": "array",
          "items": {
            "type": "object",
            "additionalProperties": false,
            "properties": {
              "rfq_line_id": { "type": "string", "pattern": "^RFL-[A-Z0-9]{5,}$" },
              "component_ref": { "type": "string" },
              "spec_summary": { "type": "string", "maxLength": 500 },
              "qty": { "type": "number", "minimum": 0 },
              "uom": { "$ref": "#/$defs/uomCode" }
            },
            "required": ["rfq_line_id","component_ref","qty","uom"]
          }
        },
        "bids": { "type": "array", "items": { "$ref": "#/$defs/bid" }, "maxItems": 10000 }
      },
      "required": ["rfq_id","status","round"]
    },

    "purchaseOrder": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "po_id": { "type": "string", "pattern": "^PO-[A-Z0-9]{6,}$" },
        "supplier_id": { "type": "string" },
        "issued_at": { "type": "string", "format": "date-time" },
        "currency": { "$ref": "#/$defs/currencyCode" },
        "lines": {
          "type": "array",
          "items": {
            "type": "object",
            "additionalProperties": false,
            "properties": {
              "po_line_id": { "type": "string", "pattern": "^POL-[A-Z0-9]{5,}$" },
              "component_ref": { "type": "string" },
              "description": { "type": "string", "maxLength": 300 },
              "qty": { "type": "number", "minimum": 0 },
              "uom": { "$ref": "#/$defs/uomCode" },
              "unit_price": { "type": "number", "minimum": 0 },
              "tracking_level_resolved": { "enum": ["quantity","lot","serial"] },
              "return_window_days": { "type": "integer", "minimum": 0, "maximum": 365 },
              "restocking_fee_pct": { "$ref": "#/$defs/percent" },
              "returns_allowed": { "type": "boolean", "default": true }
            },
            "required": ["po_line_id","component_ref","qty","uom","unit_price","tracking_level_resolved"]
          }
        },
        "delivery": {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "mode": { "enum": ["pickup","collection_point","direct"] },
            "address": { "type": "string", "maxLength": 300 },
            "collection_point_id": { "type": "string", "maxLength": 64 }
          },
          "required": ["mode"]
        },
        "waybill": { "type": "string", "maxLength": 64 },
        "status": { "enum": ["open","partially_received","closed","cancelled"] }
      },
      "required": ["po_id","supplier_id","issued_at","currency","lines","delivery"]
    },

    "geoJSONPoint": {
      "type": "object",
      "properties": { "type": { "const": "Point" }, "coordinates": { "type": "array", "items": [{"type":"number"},{"type":"number"}], "minItems": 2, "maxItems": 2 } },
      "required": ["type","coordinates"],
      "additionalProperties": false
    },
    "gln": { "type": "string", "pattern": "^\\d{13}$" },
    "sscc": { "type": "string", "pattern": "^\\d{18}$" },

    "partyRef": {
      "type": "object",
      "properties": { "name": { "type": "string", "maxLength": 120 }, "gln": { "$ref": "#/$defs/gln" } },
      "required": ["name"]
    },
    "personRef": {
      "type": "object",
      "properties": { "full_name": { "type": "string", "maxLength": 120 }, "employee_id": { "type": "string", "maxLength": 64 }, "contact": { "type": "string", "maxLength": 120 } },
      "required": ["full_name"]
    },

    "sensorReading": {
      "type": "object",
      "properties": { "type": { "enum": ["temperature_c","humidity_pct","shock_g","tilt_deg","battery_pct","gps_hdop"] }, "value": { "type": "number" }, "unit": { "type": "string", "maxLength": 16 } },
      "required": ["type","value"]
    },

    "trackingEvent": {
      "type": "object",
      "properties": {
        "event_id": { "type": "string", "pattern": "^EVT-[A-Z0-9]{8,}$" },
        "event_time": { "type": "string", "format": "date-time" },
        "event_type": { "enum": ["pickup","loaded","departed","arrived","handover","out_for_delivery","delivered","delivery_exception","inventory_move","observed"] },
        "biz_step": { "type": "string", "maxLength": 200 },
        "disposition": { "type": "string", "maxLength": 200 },
        "read_point": { "oneOf": [ { "type": "object", "properties": { "gln": { "$ref": "#/$defs/gln" } }, "required": ["gln"] }, { "$ref": "#/$defs/geoJSONPoint" } ] },
        "biz_location": { "oneOf": [ { "type": "object", "properties": { "gln": { "$ref": "#/$defs/gln" } }, "required": ["gln"] }, { "$ref": "#/$defs/geoJSONPoint" } ] },
        "handling_units": { "type": "array", "items": { "$ref": "#/$defs/sscc" }, "minItems": 1 },
        "from_party": { "$ref": "#/$defs/partyRef" },
        "to_party": { "$ref": "#/$defs/partyRef" },
        "courier_driver": { "$ref": "#/$defs/personRef" },
        "sensors": { "type": "array", "items": { "$ref": "#/$defs/sensorReading" }, "maxItems": 50 },
        "evidence": { "type": "array", "items": { "type": "string", "format": "uri" }, "maxItems": 20 },
        "notes": { "type": "string", "maxLength": 500 },
        "epcis_raw": { "type": "object", "additionalProperties": true }
      },
      "required": ["event_id","event_time","event_type","handling_units"]
    },

    "handlingUnit": {
      "type": "object",
      "properties": {
        "sscc": { "$ref": "#/$defs/sscc" },
        "parent_sscc": { "$ref": "#/$defs/sscc" },
        "label_uri": { "type": "string", "format": "uri" },
        "contents": {
          "type": "array",
          "items": {
            "type": "object",
            "additionalProperties": false,
            "properties": { "po_line_id": { "type": "string" }, "qty": { "type": "number", "minimum": 0 } },
            "required": ["po_line_id","qty"]
          }
        }
      },
      "required": ["sscc"]
    },

    "shipment": {
      "type": "object",
      "properties": {
        "shipment_id": { "type": "string", "pattern": "^SHP-[A-Z0-9]{6,}$" },
        "waybill": { "type": "string", "maxLength": 64 },
        "consignment_ref": { "type": "string", "maxLength": 64 },
        "carrier": { "$ref": "#/$defs/partyRef" },
        "origin": { "$ref": "#/$defs/partyRef" },
        "destination": { "$ref": "#/$defs/partyRef" },
        "eta": { "type": "string", "format": "date-time" },
        "status": { "enum": ["planned","in_transit","delivered","exception","cancelled"] },
        "handling_units": { "type": "array", "items": { "$ref": "#/$defs/handlingUnit" } },
        "events": { "type": "array", "items": { "$ref": "#/$defs/trackingEvent" } },
        "last_known": {
          "type": "object",
          "properties": {
            "time": { "type": "string", "format": "date-time" },
            "location": { "$ref": "#/$defs/geoJSONPoint" },
            "source": { "enum": ["carrier_api","device_gps","scan","manual"] }
          }
        }
      },
      "required": ["shipment_id","status"]
    },

    "inventoryRecord": {
      "type": "object",
      "properties": {
        "location": { "$ref": "#/$defs/partyRef" },
        "status": { "enum": ["in_stock","reserved","quarantine","installed","scrap"] },
        "uom": { "$ref": "#/$defs/uomCode" },
        "on_hand_qty": { "type": "number", "minimum": 0 },
        "lots": {
          "type": "array",
          "items": { "type": "object", "properties": { "lot": { "type": "string", "maxLength": 64 }, "qty": { "type": "number", "minimum": 0 }, "expiry": { "type": "string", "format": "date-time" } }, "required": ["lot","qty"] }
        },
        "serials": { "type": "array", "items": { "type": "string", "maxLength": 64 }, "maxItems": 100000 }
      },
      "required": ["location","status","uom"]
    },

    "warrantyClaim": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "id": { "type": "string", "pattern": "^CLAIM-[A-Z0-9]{4,}$" },
        "status": { "enum": ["open","in_review","resolved","rejected"] },
        "linked_supplier": { "type": "string" },
        "opened_at": { "type": "string", "format": "date-time" },
        "closed_at": { "type": "string", "format": "date-time" },
        "evidence": { "type": "array", "items": { "type": "string", "format": "uri" }, "maxItems": 50 }
      },
      "required": ["id","status","opened_at"]
    },

    "returnRecord": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "rma_id": { "type": "string", "pattern": "^RMA-[A-Z0-9]{5,}$" },
        "status": { "enum": ["requested","authorized","in_transit","received","credited","rejected","cancelled"] },
        "reason_code": { "enum": ["wrong_item","over_order","defect","damage_transit","other"] },
        "po_id": { "type": "string" },
        "po_line_id": { "type": "string" },
        "qty": { "type": "number", "minimum": 0 },
        "uom": { "$ref": "#/$defs/uomCode" },
        "lots": { "type": "array", "items": { "type": "string", "maxLength": 64 } },
        "serials": { "type": "array", "items": { "type": "string", "maxLength": 64 } },
        "evidence": { "type": "array", "items": { "type": "string", "format": "uri" }, "maxItems": 20 },
        "credit_note_ref": { "type": "string", "maxLength": 64 },
        "shipment": { "$ref": "#/$defs/shipment" }
      },
      "required": ["rma_id","status","reason_code"]
    },

    "trackingPolicy": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "level": { "enum": ["quantity","lot","serial"] },
        "auto_rules": {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "regulatory_serial_required": { "type": "boolean", "default": false },
            "warranty_sn_required": { "type": "boolean", "default": false },
            "safety_critical": { "type": "boolean", "default": false },
            "min_unit_price_for_serial": { "type": "number", "minimum": 0, "default": 5000 },
            "min_lead_time_days_for_serial": { "type": "integer", "minimum": 0, "default": 21 },
            "lot_expected": { "type": "boolean", "default": false },
            "expiry_expected": { "type": "boolean", "default": false }
          }
        },
        "gs1": {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "gtin": { "type": "string" },
            "lot_ai10": { "type": "boolean", "default": true },
            "serial_ai21": { "type": "boolean", "default": true },
            "sscc_for_logistics": { "type": "boolean", "default": true }
          }
        },
        "capture_points": {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "receipt": { "type": "boolean", "default": true },
            "install": { "type": "boolean", "default": true },
            "service": { "type": "boolean", "default": true }
          }
        }
      },
      "required": ["level"]
    },

    "auditRecord": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "id": { "type": "string", "pattern": "^AUD-[A-Z0-9]{6,}$" },
        "actor_role": { "$ref": "#/$defs/roleEnum" },
        "actor": { "type": "string", "maxLength": 120 },
        "action": { "type": "string", "maxLength": 64 },
        "timestamp": { "type": "string", "format": "date-time" },
        "diff": { "type": "string" }
      },
      "required": ["id","actor_role","action","timestamp"]
    }
  }
}
```

---

## 3) End‑to‑End Workflows (RACI aligned)

**A. Creation & Cataloging**
1. *Create generic component* → Engineer (R), Expert (A)
2. *Upload datasheet & parse* → Engineer (R), Expert (A)
3. *Dedup & canonicalize (GTIN/UNSPSC/eCl@ss/HS)* → Engineer (R), Expert (A), Compliance (C)
4. *Publish to summary portal* → Engineer (R), Project Manager (I)

**B. Supplier & Pricing**
5. *Supplier definition* → Supplier Manager (R), Project Manager (A), Expert (C)
6. *Margins/Taxes (VAT/Import)* → Supplier Manager (R), Project Manager (A), Compliance (C)
7. *Approval gate → Available* → Expert (A)

**C. RFQ/Bidding & Ordering**
8. *Issue RFQ, collect bids, AI follow‑ups* → Supplier Manager (R), Project Manager (A)
9. *Award & PO generation* → Supplier Manager (R), Project Manager (A)
10. *Waybill & label (QR/Digital Link)* → Project Manager (R), Supplier Manager (C)

**D. Logistics & Inventory**
11. *Shipments & SSCC handling units; EPCIS events* → Supplier Manager (R), PM (A)
12. *Receipt → inventory (quantity/lot/serial)* → Engineer (R), PM (C)
13. *Install/commission (phase gate)* → Engineer (R), Expert (A)

**E. Warranty, Returns, RMA**
14. *Warranty claims* → Tech Ops (R), Compliance (A), Supplier Manager (C)
15. *Returns/Exchanges (RMA)* → Supplier Manager (R), Project Manager (A), Compliance (C)

> Legend: **R** Responsible, **A** Accountable, **C** Consulted, **I** Informed.

---

## 4) Auto‑Tracking Decision Engine (ATDE) — Built‑in

Ordered rules to resolve `tracking_policy.level`:
1. **Regulatory serialization** (e.g., battery passport/DPP scope) ⇒ `serial`
2. **Warranty mandates serial** ⇒ `serial`
3. **Safety‑critical/unique in graph** (inverters/PCS/BESS/modules/meters) ⇒ `serial`
4. **High value or long lead time** (thresholds) ⇒ `serial`
5. **Shelf‑life or lot-labelled** consumables ⇒ `lot`
6. **BoS bulk** (fasteners, rails, trunking, etc.) ⇒ `quantity`
7. **Aggregation inference** maintains location for quantity/lot items via SSCC events.

---

## 5) Returns & Exchanges (Reverse Logistics)

- **Policies** per component/PO line (window, restocking fee, exchanges).
- **RMA records** track status, reason, evidence, shipment back, and `credit_note_ref`.
- **Partial returns** supported at quantity/lot/serial level.
- **Quarantine → restock/scrap** decision with audit and financial linkage.

---

## 6) Standards & Best Practices (Mapped) — Expanded

> This section is **normative** for platform behaviour. Words like **MUST**, **SHOULD**, and **MAY** follow RFC‑2119 style. The guidance below is intended to be copy‑visible inside admin/settings pages and developer docs.

### 6.1 Identification & Classification (GS1, UNSPSC, eCl@ss, HS/HTS)
**Policy**
- Every component **MUST** have a category code (UNSPSC or eCl@ss).
- Physical tradable items **SHOULD** store a GS1 **GTIN** when available; otherwise set `gtin=null`.
- All logistics handling units **MUST** be identified by **SSCC** (pallet/case/parcel).
- All sites/nodes/depots **SHOULD** carry **GLN** identifiers.
- Import/exported items **MUST** store a 6‑digit **HS** root; destination‑specific **HTS** MAY be computed at ordering time.

**Experience notes**
- Don’t force GTIN on industrial parts that don’t have it; rely on brand+part and certificate numbers.
- HS classification is often tied to **function** & **materials**; store key attributes (e.g., material, voltage class) to support classifier models.
- Use **SGTIN (GTIN+serial)** for serialised items when partners require GS1 encoding.

**Data quality gates**
- Name uniqueness = `Brand_Part_RatingW`; conflicts trigger dedupe review.
- HS present for cross‑border orders; GLN present for any warehouse/depot location you control.

---

### 6.2 Procurement Transactions (UBL 2.3 first; cXML/EDI as adapters)
**Document map**
- RFQ → **Quotation**; Award → **Order** (PO); Ship → **DespatchAdvice** + **Waybill**; In‑transit → **TransportationStatus**; Receipt → **ReceiptAdvice**; Returns → **CreditNote**.

**Platform MUST**
- Generate valid UBL documents with consistent IDs (e.g., `PO-XXXXXX`) and ISO currency codes.
- Preserve line‑level references to `component_ref`, `qty`, `uom`, `unit_price`, and `tracking_level_resolved`.
- Attach controlled documents (datasheet, certificates) as binary parts with content hashes.
- Sign outgoing business docs where partner requires (XMLDSig) and archive immutable copies.

**Experience notes**
- Use **Incoterms** defaults (e.g., DAP) to avoid misaligned responsibility for import duties; make it explicit on each PO.
- Include payment terms and return policy mirrors on each PO line to de‑risk RMAs.

---

### 6.3 Logistics Eventing (EPCIS 2.0 JSON/JSON‑LD)
**Minimum capture**
- For each shipment: **pickup, departed, arrived, delivered**, plus any **handover**.
- Each event **MUST** include `event_time`, `read_point` (GLN or GPS), and SSCC(s).
- Sensor data (temp/shock) **SHOULD** be captured for sensitive equipment (inverters, BESS).

**Operational SLAs**
- Event latency < 15 minutes to keep “last known” reliable.
- Time sources **MUST** be NTP‑synced; offline capture queues into store‑and‑forward.

**Experience notes**
- Use **aggregation events**: you don’t need to scan every serial when a pallet (SSCC) is sealed; the supplier will disaggregate at receipt.
- If GPS is flaky, fall back to GLN + photo evidence at gates.

---

### 6.4 QR & Resolver (GS1 Digital Link)
**Policy**
- All outward‑facing labels **SHOULD** use Digital Link URIs that resolve to the correct **shipment/SSCC** or **component** page with role‑based access.
- QR codes **MUST NOT** contain PII; use anonymised tokens.
- For serialised equipment, QR **SHOULD** link to the **component instance** and show warranty/commissioning state.

**Experience notes**
- Provide an **offline fallback** (short code) for sites without data; queue scans and resolve later.
- Consider **dynamic QR** for revocable links when devices are stolen or reassigned.

---

### 6.5 Quality & Document Control (ISO 9001)
**Policy**
- Every datasheet/certificate **MUST** be immutable, content‑hashed, and revisioned.
- Changes to `libraries.components` **MUST** occur via governed change requests with approver roles.
- Records retention **MUST** meet contractual/regulatory minima (typ. 7–10 years).

**Experience notes**
- Watermark **DRAFT** on unapproved renders to prevent accidental use.
- Add **training tips** inline in the UI near upload forms (e.g., “shoot nameplate straight‑on, keep glare low”).

---

### 6.6 Sustainable Procurement (ISO 20400) & Compliance (RoHS/REACH/WEEE)
**Policy**
- Supplier selection **SHOULD** include environmental & social criteria (weight 15–30%).
- Store compliance evidence (RoHS/REACH/WEEE declarations) under `compliance.certificates`.
- High‑impact categories **SHOULD** include basic LCA fields (embodied CO₂e per unit, if supplier provides).

**Experience notes**
- Make sustainability **visible** in bid scoring; suppliers will surface better data if it affects awards.

---

### 6.7 Electrical Safety & Performance (IEC & Grid Codes)
**PV modules**: verify IEC 61215 (design qualification) and IEC 61730 (safety); store certificate numbers and test report links. Capture **module serials** at install for warranty traceability.
**Inverters/PCS**: verify product safety (e.g., IEC 62109 series) and EMC; store **grid code** compliance (e.g., IEEE 1547/EN 50549) where applicable; keep **firmware** version in instance records.
**BoS**: for breakers, combiner boxes, cables—record voltage class, short‑circuit ratings, temperature ratings; ensure wiring guides reflect verified limits.

**Experience notes**
- Block commissioning package generation until mandatory certificates are attached.

---

### 6.8 Digital Product Passport (DPP) / Battery Regulation Readiness
**Policy**
- Components in scope (e.g., certain batteries) **MUST** set `traceability.dpp.enabled=true` and store QR/DPP URI.
- Minimum DPP payload fields: manufacturer, model, capacity/rating, hazardous substance flags, repairability/serviceability notes, end‑of‑life instructions.

**Experience notes**
- Start collecting DPP‑like data **now**, even if not mandated—retrofit is costly once products are deployed.

---

### 6.9 Cybersecurity & Data Protection
**Policy**
- All media with potential PII **MUST** pass privacy checks (face/plate blur where appropriate).
- Access to shipments/instances is **least‑privilege**; signed URLs for media; encryption at rest & in transit.
- Admin exports **MUST** be audit‑logged and time‑boxed.

**Experience notes**
- Use different buckets/keys for **restricted raw** vs **redacted** assets; only redacted leaves the org by default.

---

### 6.10 Accessibility & Localisation
**Policy**
- Generate **alt_text** for all externally‑facing images; localise proposals and client portal labels.
- Prefer **vector** for symbols/diagrams; keep raster fallbacks.
- Units **MUST** respect project settings (SI/imperial) with explicit unit labels.

**Experience notes**
- Keep template‑level **doc_bindings** so content teams don’t hunt for images; the platform auto‑selects per rules.

---

### 6.11 Data Quality (DQ) Rules & Acceptance Criteria
**Mandatory fields to approve a component**: `brand`, `part_number`, `classification`, `datasheet`, `tracking_policy.level`, at least one supplier **OR** an approved equivalence link.
**PO line acceptance**: `qty>0`, `uom`, `unit_price` ≥ 0, `tracking_level_resolved` set.
**Shipment acceptance**: at least one SSCC, origin/destination GLN, and initial `pickup` event.

**Experience notes**
- Show **why** a record fails DQ (inline) and one‑click **fix** actions (e.g., auto‑classify UNSPSC).

---

### 6.12 Interoperability & Conformance Tests
**Must‑pass tests**
- UBL validation for each doc type; EPCIS event schema validation; JSON Schema validation for CMS; QR/Digital Link decoding; barcode scan legibility test (print @ 203 dpi).
- Partner loopback tests (send, receive, reconcile) before go‑live.

**Experience notes**
- Keep a **golden sample pack** (RFQ→PO→Ship→Receive→Return) for regression testing.

---

### 6.13 Performance, Scale & Retention
**Targets**
- EPCIS ingest ≥ 200 events/sec/project (burst); media rendition within 3s P95; search across 100k components in < 1s P95.
- Retention: live EPCIS 180 days hot, then archive; media originals retained per contract.

**Experience notes**
- Paginate aggressively; store derived KPIs to avoid re‑scanning large logs.

---

### 6.14 Operational Playbooks (Field‑Tested Tips)
- **Photos**: avoid back‑light; include a coin/screwdriver for scale on small parts; shoot nameplates square; retry if blur score > threshold.
- **Serials**: prefer OCR from close‑ups; scan QR if provided; confirm against expected count before leaving the depot.
- **Connectivity**: offline capture queues photos/events; the app shows a **sync debt** counter per work package.
- **Exceptions**: if packaging is damaged, capture 4‑sides + top, include SSCC label & context; auto‑open a case with the supplier.

---

### 6.15 Code Lists & Glossary (for UI/Docs)
- **Reason codes (returns)**: wrong_item, over_order, defect, damage_transit, other.
- **Delivery modes**: pickup, collection_point, direct.
- **Tracking levels**: quantity, lot, serial.
- **Event types**: pickup, loaded, departed, arrived, handover, out_for_delivery, delivered, delivery_exception, inventory_move, observed.

---

## 7) Implementation Notes Implementation Notes

- **Where to store**: Embed `component_management` in each component; keep heavy logs (EPCIS, AI, audit) paged/segmented for scale.
- **Approvals**: Use `approvals.records[]` and gate state transitions (`status`) via RBAC.
- **Connect to instances**: On delivery/installation, update `instances[]` with serial/lot placement and commissioning results.
- **Analytics**: Compute KPIs from `orders`, `shipments.events`, `returns.records`, `warranty.claims`.
- **Interoperability**: Expose EPCIS capture/query endpoints, and export UBL docs where partners require them.

---

## 8) Minimal Data Flow (Happy Paths)

1) **Create & Approve**: upload datasheet → parse → enrich → dedupe → approve → available.
2) **Buy & Track**: RFQ → bids → award → PO → shipments (SSCC, events) → receipt → inventory.
3) **Install & Operate**: pick to site → scan (Geo/GLN) → install → commission → operational.
4) **Service & Return**: claim or wrong order → RMA → ship back (SSCC) → credit note → restock/scrap.

---

**## 9) Media, Symbols & Imaging (MSI) Framework — End‑to‑End

This section formalizes the **image/symbol handling** across the full lifecycle and integrates it with approvals, logistics events, installation, QC, service, warranty, and document generation. It adds a dedicated `media` subsystem to `component_management` and prescribes **capture policies**, **usage bindings**, **renditions**, **privacy controls**, and **AI automation**.

### 9.1 Goals
- Make images/symbols **first‑class data**: verifiable, versioned, queryable, auto‑selectable.
- Cover **IEC symbols for SLD/wiring**, **photos for delivery/installation/QC/service/warranty**, and **component hero/images** for proposals & portals.
- Auto‑trigger captures at the right **workflow events** (e.g., receipt, install, commissioning, claim).
- Ensure assets are **reusable** across documents (proposal, SLD, wiring guide, fault finding, client portal) via explicit **bindings**.

---

### 9.2 Schema Addendum — `media` (to be added inside `component_management`)

```json
{
  "component_management": {
    "media": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "library": {
          "type": "array",
          "items": { "$ref": "#/$defs/mediaAsset" },
          "maxItems": 20000
        },
        "capture_policy": { "$ref": "#/$defs/mediaCapturePolicy" },
        "doc_bindings": { "$ref": "#/$defs/mediaDocBindings" },
        "renditions": {
          "type": "array",
          "items": { "$ref": "#/$defs/renditionSpec" },
          "maxItems": 200
        }
      },
      "required": ["library","capture_policy","doc_bindings"]
    }
  }
}
```

> **Placement**: add `media` alongside existing properties (e.g., `source_documents`, `supplier_chain`, `order_management`).

---

### 9.3 `$defs` — Media Types & Policies

Append the following definitions to `$defs` in the schema:

```json
{
  "$defs": {
    "mediaAsset": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "asset_id": { "type": "string", "pattern": "^MED-[A-Z0-9]{6,}$" },
        "type": {
          "enum": [
            "component_photo_hero", "component_photo_detail", "datasheet_image", "brand_logo",
            "iec_symbol", "schematic_symbol", "wiring_diagram_svg", "sld_svg",
            "delivery_pod", "delivery_package_condition", "delivery_label_serial",
            "install_pre_site", "install_mounting", "install_connections", "install_grounding",
            "install_nameplate", "commissioning_screen", "qc_visual", "qc_thermal",
            "service_fault", "service_after_fix", "warranty_evidence"
          ]
        },
        "scope": {
          "enum": [
            "component_generic", "component_instance", "shipment", "handling_unit",
            "site_location", "work_package"
          ]
        },
        "link": {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "component_id": { "type": "string" },
            "serial": { "type": "string" },
            "lot": { "type": "string" },
            "shipment_id": { "type": "string" },
            "sscc": { "type": "string" },
            "site_gln": { "type": "string" },
            "work_package_id": { "type": "string" }
          }
        },
        "uri": { "type": "string", "format": "uri" },
        "hash": { "type": "string", "pattern": "^sha256:[0-9a-f]{64}$" },
        "mime": { "type": "string", "maxLength": 100 },
        "width_px": { "type": "integer", "minimum": 0 },
        "height_px": { "type": "integer", "minimum": 0 },
        "vector": { "type": "boolean", "default": false },
        "exif": { "type": "object", "additionalProperties": true },
        "captured_at": { "type": "string", "format": "date-time" },
        "captured_by": { "type": "string", "maxLength": 120 },
        "gps": { "$ref": "#/$defs/geoJSONPoint" },
        "alt_text": { "type": "string", "maxLength": 300 },
        "language": { "type": "string", "maxLength": 8 },
        "license": { "type": "string", "maxLength": 64 },
        "approved_for_external": { "type": "boolean", "default": false },
        "privacy": {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "contains_faces": { "type": "boolean", "default": false },
            "contains_pii": { "type": "boolean", "default": false },
            "blur_applied": { "type": "boolean", "default": false },
            "redaction_notes": { "type": "string", "maxLength": 300 }
          }
        },
        "overlays": {
          "type": "array",
          "description": "Callouts/labels mapped onto the image/SVG",
          "items": {
            "type": "object",
            "additionalProperties": false,
            "properties": {
              "shape": { "enum": ["rect","circle","polygon","path","leader"] },
              "coords": { "type": "array", "items": { "type": "number" }, "minItems": 2 },
              "label": { "type": "string", "maxLength": 120 },
              "port_ref": { "type": "string", "description": "ODL-SD port ID if linked" },
              "severity": { "enum": ["info","warn","hazard"] }
            },
            "required": ["shape","coords"]
          }
        },
        "symbol_ref": {
          "type": "object",
          "description": "For IEC/diagram symbols",
          "additionalProperties": false,
          "properties": {
            "standard": { "enum": ["IEC 60617","IEC 60417","ISO 7010","Custom"] },
            "code": { "type": "string", "maxLength": 32 },
            "svg_uri": { "type": "string", "format": "uri" },
            "keywords": { "type": "array", "items": { "type": "string", "maxLength": 32 }, "maxItems": 20 }
          }
        },
        "tags": { "type": "array", "items": { "type": "string", "maxLength": 32 }, "maxItems": 50 }
      },
      "required": ["asset_id","type","uri","hash"]
    },

    "mediaCapturePolicy": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "required_at": {
          "type": "array",
          "description": "When images must be captured",
          "items": {
            "type": "object",
            "additionalProperties": false,
            "properties": {
              "trigger": {
                "enum": [
                  "rfq_awarded","picking","loaded","departed","arrived","delivered",
                  "install_start","mounting_complete","connections_complete","grounding_check",
                  "commissioning","qc_check","service_call","warranty_claim"
                ]
              },
              "asset_types": {
                "type": "array",
                "items": { "$ref": "#/$defs/mediaAssetType" },
                "minItems": 1
              },
              "min_resolution_px": { "type": "integer", "minimum": 0 },
              "notes": { "type": "string", "maxLength": 300 }
            },
            "required": ["trigger","asset_types"]
          }
        },
        "quality": {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "min_long_edge_px": { "type": "integer", "minimum": 0, "default": 1600 },
            "allow_formats": { "type": "array", "items": { "type": "string" }, "default": ["image/jpeg","image/png","image/svg+xml"] },
            "require_geo_for_delivery": { "type": "boolean", "default": true }
          }
        },
        "privacy_rules": {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "auto_detect_faces": { "type": "boolean", "default": true },
            "auto_blur_house_numbers": { "type": "boolean", "default": true },
            "store_raw_restricted": { "type": "boolean", "default": true }
          }
        }
      },
      "required": ["required_at","quality"]
    },

    "mediaAssetType": {
      "type": "string",
      "enum": [
        "component_photo_hero","component_photo_detail","datasheet_image","brand_logo",
        "iec_symbol","schematic_symbol","wiring_diagram_svg","sld_svg",
        "delivery_pod","delivery_package_condition","delivery_label_serial",
        "install_pre_site","install_mounting","install_connections","install_grounding",
        "install_nameplate","commissioning_screen","qc_visual","qc_thermal",
        "service_fault","service_after_fix","warranty_evidence"
      ]
    },

    "mediaDocBindings": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "bindings": {
          "type": "array",
          "items": {
            "type": "object",
            "additionalProperties": false,
            "properties": {
              "target": {
                "enum": [
                  "proposal_summary","technical_proposal","financial_proposal",
                  "single_line_diagram","wiring_guide","fault_finding_guide",
                  "marketing_datasheet","portal_component_card","client_portal_gallery"
                ]
              },
              "selection": {
                "type": "object",
                "additionalProperties": false,
                "properties": {
                  "preferred_types": { "type": "array", "items": { "$ref": "#/$defs/mediaAssetType" }, "minItems": 1 },
                  "prefer_latest": { "type": "boolean", "default": true },
                  "min_resolution_px": { "type": "integer", "minimum": 0 },
                  "aspect_ratio": { "type": "string", "pattern": "^
?(?:1:1|3:2|4:3|16:9)$" },
                  "require_approved_for_external": { "type": "boolean", "default": false }
                },
                "required": ["preferred_types"]
              },
              "placeholders": {
                "type": "array",
                "description": "Named slots used by template engines",
                "items": { "type": "string", "maxLength": 64 }
              }
            },
            "required": ["target","selection"]
          },
          "maxItems": 200
        }
      },
      "required": ["bindings"]
    },

    "renditionSpec": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "name": { "type": "string", "maxLength": 64 },
        "usage": { "enum": ["icon","thumb","card","hero","doc_inline","diagram_layer"] },
        "width_px": { "type": "integer", "minimum": 1 },
        "height_px": { "type": "integer", "minimum": 1 },
        "fit": { "enum": ["contain","cover","fill"] },
        "background": { "enum": ["transparent","white","black","auto"] },
        "remove_background": { "type": "boolean", "default": false },
        "watermark": { "type": "boolean", "default": false }
      },
      "required": ["name","usage","width_px","height_px","fit"]
    }
  }
}
```

**Design choices**
- **Symbols as vectors** (`iec_symbol`, `schematic_symbol`, `wiring_diagram_svg`, `sld_svg`) keep diagrams crisp and scriptable. Each symbol references a **standard code** (e.g., IEC 60617) and an SVG.
- **Overlays** let us position callouts/labels and even link them to ODL‑SD **ports** for auto‑wiring guides and fault‑finding.
- **Bindings** decouple **where** an image appears from **which** image is chosen, enabling consistent doc automation.
- **Privacy** enforces blurring/redaction logic when assets leave the org.

---

### 9.4 Workflow Triggers — When to Capture & Use

**Logistics**
- *Departed (supplier)*: pallet overview, label/serial, packaging integrity.
- *Arrived depot*: package condition (4 sides + top), damage exceptions.
- *Delivered (site)*: Proof‑of‑Delivery (POD) with QR scan, package condition, serial plate.

**Installation**
- *Pre‑site*: array area overview and hazard signage.
- *Mounting complete*: rails/brackets, torque evidence (photo of wrench screen/dial), earthing bonds.
- *Connections complete*: DC strings, polarity labels, conduit routing, gland seals.
- *Nameplate*: clear shot for warranty.

**Commissioning / QC**
- Inverter/PCS screen with parameters; IV curve screenshots; insulation test readings; **thermal imaging** (modules, combiner, inverter under load).

**Service / Warranty**
- Fault evidence; replaced part serial; after‑fix verification; return packaging; courier label.

**Document auto‑use**
- Proposal hero: `component_photo_hero` (brand‑clean) → `proposal_summary`.
- SLD: vector `iec_symbol` + `sld_svg` with port overlays.
- Wiring guide: `wiring_diagram_svg` + overlays bound to ports.
- Fault guide: `service_fault` + callouts + links to test steps.
- Client portal gallery: curated set (hero, install, commissioning, thermal).

---

### 9.5 AI Automation
- **Classification** of uploads into `asset_type` and `scope`.
- **OCR** of nameplates/serials; auto‑associate to `component_instance`.
- **EXIF/GPS** extraction; geo‑fence checks (e.g., site GLN radius).
- **Quality scoring** (blur, exposure, resolution) to block inadequate images.
- **Accessibility**: generate `alt_text` in project language; multi‑lingual support for client‑facing docs.
- **Dup‑merge**: hash‑based dedupe; best‑quality selection.

---

### 9.6 Governance, Rights & Storage
- Each asset has `approved_for_external` and `license` flags; external use is gated by approvers.
- Storage is **content‑addressed** (`hash`) with lifecycle retention; renditions are derived assets.
- Sensitive raw images remain in a **restricted tier**; redacted renditions serve external docs.

---

### 9.7 Minimal Example — Capture Policy Snippet

```json
{
  "media": {
    "capture_policy": {
      "required_at": [
        { "trigger": "delivered", "asset_types": ["delivery_pod","delivery_package_condition","delivery_label_serial"], "min_resolution_px": 1600 },
        { "trigger": "install_start", "asset_types": ["install_pre_site"] },
        { "trigger": "mounting_complete", "asset_types": ["install_mounting","install_grounding"] },
        { "trigger": "connections_complete", "asset_types": ["install_connections","install_nameplate"] },
        { "trigger": "commissioning", "asset_types": ["commissioning_screen","qc_thermal"] }
      ],
      "quality": { "min_long_edge_px": 1600, "allow_formats": ["image/jpeg","image/png","image/svg+xml"], "require_geo_for_delivery": true },
      "privacy_rules": { "auto_detect_faces": true, "auto_blur_house_numbers": true, "store_raw_restricted": true }
    },
    "doc_bindings": {
      "bindings": [
        { "target": "proposal_summary", "selection": { "preferred_types": ["component_photo_hero","brand_logo"], "require_approved_for_external": true }, "placeholders": ["hero","brand"] },
        { "target": "single_line_diagram", "selection": { "preferred_types": ["sld_svg","iec_symbol"], "min_resolution_px": 1200 }, "placeholders": ["diagram","symbols"] },
        { "target": "wiring_guide", "selection": { "preferred_types": ["wiring_diagram_svg","schematic_symbol"] }, "placeholders": ["wiring"] }
      ]
    }
  }
}
```

---

### 9.8 Best‑Practice Symbol Sets (Reference)
- **IEC 60617**: Graphical symbols for diagrams (SLD, wiring).
- **IEC 60417**: Symbols for use on equipment (nameplates, markings).
- **ISO 7010**: Safety signs (site photos, hazard overlays).

---

### 9.9 Operational Guidance
- Enforce capture tasks via mobile app at each trigger; block next task until required photos are uploaded & pass quality checks.
- Use **port‑linked overlays** to auto‑generate wiring and fault‑finding guides from the same images/SVG.
- Publish external documents only from **approved** and **redacted** assets.

---

End of Document**


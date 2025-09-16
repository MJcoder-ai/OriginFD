# ODL-SD Technical Specification
## OriginFlow Design Language - System Document
### Version 4.1 - Complete Design-to-Operation Lifecycle Specification

---

## EXECUTIVE SUMMARY

ODL-SD v4.1 is a comprehensive, self-contained JSON document format for representing solar PV, battery storage, and hybrid energy systems from initial concept through decommissioning. This specification addresses the complete lifecycle including design, procurement, construction, commissioning, operations, maintenance, and end-of-life management.

**Key Capabilities:**
- Multi-domain support (PV, BESS, Grid Interface, SCADA)
- Hierarchical scaling from 1kW residential to multi-GW portfolios
- Comprehensive financial modeling with sensitivity analysis and climate adjustments
- Full mechanical and structural validation with JSON Schema enforcement
- Grid code compliance and dynamic behavior modeling
- ESG and sustainability tracking with enhanced cybersecurity frameworks
- Multi-stakeholder governance with digital signatures
- Data management strategies for large-scale deployments

**Version 4.1 Enhancements:**
- Formal JSON Schema validation definitions
- Complete PV degradation models matching BESS detail
- Climate-specific loss adjustments and regional financial modeling
- Environmental risk management and remediation frameworks
- Comprehensive SCADA cybersecurity specifications
- Implementation guidance with working examples and glossary

---

## PART I: CORE ARCHITECTURE

### 1.1 Document Structure

```json
{
  "$schema": "https://odl-sd.org/schemas/v4.1/document.json",
  "schema_version": "4.1",

  "meta": {
    "project": "string",
    "portfolio_id": "string",
    "domain": "PV|BESS|HYBRID|GRID|MICROGRID",
    "scale": "RESIDENTIAL|COMMERCIAL|INDUSTRIAL|UTILITY|HYPERSCALE",
    "units": {
      "system": "SI|IMPERIAL",
      "currency": "USD|EUR|GBP|AUD",
      "coordinate_system": "EPSG:4326"
    },
    "timestamps": {
      "created_at": "ISO8601",
      "updated_at": "ISO8601",
      "valid_from": "ISO8601",
      "valid_until": "ISO8601"
    },
    "versioning": {
      "document_version": "4.1.0",
      "content_hash": "sha256:...",
      "previous_hash": "sha256:...",
      "change_summary": "string"
    }
  },

  "hierarchy": {},           // Portfolio → Site → Plant → Block structure
  "requirements": {},        // Functional, constraints, regulatory, ESG
  "libraries": {},          // Component definitions with full port typing
  "instances": [],          // Placed components with lifecycle tracking
  "connections": [],        // Port-to-port wiring with edge kinds
  "structures": {},         // Mechanical supports and foundations
  "physical": {},           // Surfaces, zones, routing, loads
  "analysis": [],           // Versioned calculations and simulations
  "compliance": {},         // Multi-jurisdiction evidence-based checks
  "finance": {},            // Comprehensive financial modeling
  "operations": {},         // Service, monitoring, performance
  "esg": {},               // Environmental, social, governance metrics
  "governance": {},         // Approvals, signatures, change control
  "external_models": {},    // IFC, CIM, weather data mappings
  "audit": [],             // Complete change history
  "data_management": {}     // Scalability and validation strategies
}
```

### 1.2 Hierarchical Organization

```json
{
  "hierarchy": {
    "type": "PORTFOLIO|SITE|PLANT|BLOCK|ARRAY|STRING|DEVICE",
    "id": "unique_identifier",
    "parent_id": "parent_reference",
    "children": ["child_ids"],

    "portfolio": {
      "id": "PORTFOLIO_GLOBAL_2025",
      "name": "Global Renewable Portfolio",
      "total_capacity_gw": 5.2,
      "regions": {
        "AMERICAS": {
          "capacity_gw": 2.1,
          "sites": ["SITE_US_CA_01", "SITE_US_TX_01", "SITE_MX_01"]
        },
        "EMEA": {
          "capacity_gw": 1.8,
          "sites": ["SITE_ES_01", "SITE_DE_01", "SITE_ZA_01"]
        },
        "APAC": {
          "capacity_gw": 1.3,
          "sites": ["SITE_AU_01", "SITE_IN_01", "SITE_JP_01"]
        }
      }
    },

    "aggregation_rules": {
      "power": {
        "method": "hierarchical_sum",
        "loss_model": {
          "dc_wiring": 0.015,
          "dc_combiner": 0.005,
          "inverter": 0.02,
          "ac_collection": 0.01,
          "transformer": 0.01,
          "transmission": 0.02
        }
      },
      "energy": {
        "method": "probabilistic_sum",
        "availability_cascade": {
          "component": 0.99,
          "string": 0.985,
          "inverter": 0.98,
          "substation": 0.995,
          "grid": 0.99
        }
      },
      "financial": {
        "method": "weighted_average",
        "currency_conversion": {
          "method": "spot_rate|fixed_rate|api_dynamic",
          "api_endpoint": "optional:https://api.exchangerates.com/v1/latest",
          "historical_rates": {
            "2025-01-01": {"EUR_USD": 1.1, "GBP_USD": 1.3}
          }
        },
        "consolidation": "project|portfolio"
      }
    }
  }
}
```

### 1.3 JSON Schema Definition and Validation Rules

```json
{
  "$id": "https://odl-sd.org/schemas/v4.1/document.json",
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "ODL-SD Document Schema v4.1",
  "type": "object",
  "required": ["$schema", "schema_version", "meta", "hierarchy"],

  "definitions": {
    "port_definition": {
      "type": "object",
      "properties": {
        "id": {"type": "string", "pattern": "^[a-zA-Z][a-zA-Z0-9_]*$"},
        "direction": {"enum": ["input", "output", "bidirectional"]},
        "signal": {
          "type": "object",
          "properties": {
            "kind": {"enum": ["dc", "ac", "data", "control", "thermal", "measurement"]},
            "voltage_v": {
              "type": "object",
              "properties": {
                "nominal": {"type": "number"},
                "min": {"type": "number"},
                "max": {"type": "number"}
              }
            }
          },
          "required": ["kind"]
        }
      },
      "required": ["id", "direction", "signal"]
    },

    "instance_definition": {
      "type": "object",
      "properties": {
        "id": {"type": "string"},
        "type_ref": {"type": "string"},
        "parent_ref": {"type": "string"},
        "location": {
          "type": "object",
          "properties": {
            "lat": {"type": "number", "minimum": -90, "maximum": 90},
            "lon": {"type": "number", "minimum": -180, "maximum": 180},
            "elevation_m": {"type": "number"}
          }
        },
        "lifecycle_status": {
          "enum": ["planned", "procured", "installed", "commissioned", "operational", "maintenance", "decommissioned"]
        },
        "digital_twin": {
          "type": "object",
          "properties": {
            "model_url": {"type": "string", "format": "uri"},
            "last_sync": {"type": "string", "format": "date-time"},
            "sync_frequency_hours": {"type": "integer", "minimum": 1}
          }
        }
      },
      "required": ["id", "type_ref"]
    },

    "connection_definition": {
      "type": "object",
      "properties": {
        "id": {"type": "string"},
        "from": {
          "type": "object",
          "properties": {
            "instance_id": {"type": "string"},
            "port_id": {"type": "string"}
          },
          "required": ["instance_id", "port_id"]
        },
        "to": {
          "type": "object",
          "properties": {
            "instance_id": {"type": "string"},
            "port_id": {"type": "string"}
          },
          "required": ["instance_id", "port_id"]
        },
        "kind": {
          "enum": ["dc_power", "ac_power", "data_modbus", "data_can", "data_ethernet", "control_digital", "control_analog", "thermal_liquid", "thermal_air"]
        },
        "attributes": {
          "type": "object",
          "properties": {
            "cable_type": {"type": "string"},
            "length_m": {"type": "number", "minimum": 0},
            "resistance_ohm": {"type": "number", "minimum": 0},
            "validated": {"type": "boolean"},
            "validation_timestamp": {"type": "string", "format": "date-time"}
          }
        }
      },
      "required": ["from", "to", "kind"]
    },

    "sub_element_definition": {
      "type": "object",
      "properties": {
        "type_ref": {"type": "string"},
        "qty": {"type": "integer", "minimum": 1}
      },
      "required": ["type_ref", "qty"]
    }
  },

  "properties": {
    "instances": {
      "type": "array",
      "items": {"$ref": "#/definitions/instance_definition"}
    },
    "connections": {
      "type": "array",
      "items": {"$ref": "#/definitions/connection_definition"}
    }
  }
}
```

### 1.4 Data Management for Large-Scale Deployments

```json
{
  "data_management": {
    "scalability_strategies": {
      "instance_threshold": 10000,
      "connection_threshold": 50000,

      "partitioning": {
        "strategy": "hierarchical|geographic|temporal",
        "partition_size_mb": 100,
        "index_fields": ["id", "type_ref", "location", "lifecycle_status"]
      },

      "external_references": {
        "enabled": true,
        "storage_backend": "s3|azure_blob|gcs",
        "reference_format": {
          "type": "json_pointer",
          "example": {
            "$ref": "s3://odl-sd-data/project-123/instances/batch-001.json#/instances/0"
          }
        },
        "caching": {
          "strategy": "lru",
          "cache_size_mb": 500,
          "ttl_seconds": 3600
        }
      },

      "compression": {
        "algorithm": "gzip|brotli|zstd",
        "level": 6,
        "minimum_size_kb": 10
      },

      "streaming": {
        "enabled": true,
        "protocol": "json_lines|msgpack|protobuf",
        "batch_size": 1000,
        "checkpoint_interval": 10000
      }
    },

    "validation_performance": {
      "async_validation": true,
      "parallel_workers": 8,
      "incremental_validation": true,
      "cache_validation_results": true
    }
  }
}
```

---

## PART II: ENHANCED COMPONENT LIBRARIES

### 2.1 Battery Energy Storage System (BESS) Components

```json
{
  "libraries": {
    "components": {
      "bess_module": {
        "category": "energy_storage",
        "subcategory": "battery_module",
        "metadata": {
          "manufacturer": "CATL",
          "model": "LFP280",
          "technology": "LiFePO4",
          "certifications": ["UL1973", "IEC62619", "UN38.3"]
        },
        "ports": [
          {
            "id": "dc_pos",
            "direction": "bidirectional",
            "signal": {
              "kind": "dc",
              "voltage_v": {"nominal": 3.2, "min": 2.5, "max": 3.65},
              "current_a": {"continuous": 280, "peak": 560}
            },
            "physical": {
              "connector": "M8_terminal",
              "torque_nm": 12,
              "busbar_material": "copper_nickel_plated"
            }
          }
        ],
        "attributes": {
          "electrical": {
            "capacity_ah": 280,
            "energy_wh": 896,
            "internal_resistance_mohm": 0.5,
            "self_discharge_pct_month": 2
          },
          "degradation": {
            "calendar_model": {
              "type": "arrhenius",
              "parameters": {
                "activation_energy_ev": 0.8,
                "pre_exponential": 1e-4
              }
            },
            "cycle_model": {
              "type": "rainflow",
              "parameters": {
                "cycles_80_dod": 6000,
                "cycles_100_dod": 4000,
                "stress_factors": {
                  "c_rate": 1.2,
                  "temperature": 1.1,
                  "soc_range": 0.9
                }
              }
            }
          },
          "thermal": {
            "specific_heat_j_kg_k": 1100,
            "thermal_mass_kg": 5.4,
            "max_temperature_c": 55,
            "thermal_runaway_c": 220,
            "heat_generation": {
              "charge_w": 28,
              "discharge_w": 32
            }
          },
          "safety": {
            "chemistry_hazards": ["thermal_runaway", "electrolyte_leak"],
            "fire_class": "D",
            "suppression": "aerosol|gas|water_mist",
            "venting_required": true,
            "explosion_rating": "ATEX_Zone_2"
          },
          "physical": {
            "dimensions_mm": [173, 72, 204],
            "weight_kg": 5.4,
            "terminals": "M8",
            "ip_rating": "IP67"
          }
        },
        "operating_envelope": {
          "charge": {
            "temperature_c": {"min": 0, "max": 45},
            "current_c_rate": {"max": 1},
            "voltage_v": {"max": 3.65}
          },
          "discharge": {
            "temperature_c": {"min": -20, "max": 55},
            "current_c_rate": {"max": 2},
            "voltage_v": {"min": 2.5}
          },
          "storage": {
            "temperature_c": {"min": -30, "max": 60},
            "soc_pct": {"recommended": 50},
            "duration_months": {"max": 12}
          }
        }
      },

      "bess_rack": {
        "category": "energy_storage",
        "subcategory": "battery_rack",
        "metadata": {
          "configuration": "20S14P",
          "nominal_voltage_v": 64,
          "usable_energy_kwh": 250
        },
        "ports": [
          {
            "id": "dc_bus",
            "direction": "bidirectional",
            "signal": {
              "kind": "dc",
              "voltage_v": {"min": 50, "max": 73, "nominal": 64},
              "current_a": {"max": 3920}
            }
          },
          {
            "id": "bms_can",
            "direction": "bidirectional",
            "signal": {
              "kind": "data",
              "protocol": "CAN_2.0B",
              "baud_rate": 500000
            }
          },
          {
            "id": "coolant_in",
            "direction": "input",
            "signal": {
              "kind": "thermal",
              "medium": "glycol_water_50_50",
              "flow_lpm": {"min": 10, "max": 50},
              "temperature_c": {"min": 15, "max": 25}
            }
          }
        ],
        "sub_elements": [
          {"type_ref": "bess_module", "qty": 280},
          {"type_ref": "bms_rack_controller", "qty": 1},
          {"type_ref": "dc_breaker_400a", "qty": 1},
          {"type_ref": "current_sensor_hall", "qty": 14},
          {"type_ref": "temp_sensor_ntc", "qty": 28}
        ],
        "protection": {
          "overcurrent": {
            "device": "dc_breaker",
            "rating_a": 400,
            "curve": "inverse_time"
          },
          "ground_fault": {
            "detection": "residual_current",
            "threshold_ma": 300
          },
          "arc_fault": {
            "detection": "ai_based",
            "response_ms": 100
          }
        }
      },

      "power_conversion_system": {
        "category": "power_electronics",
        "subcategory": "bidirectional_inverter",
        "metadata": {
          "topology": "three_level_npc",
          "cooling": "liquid_cooled",
          "grid_codes": ["IEEE1547-2018", "CA_Rule_21", "NERC_PRC-024"]
        },
        "ports": [
          {
            "id": "dc_battery",
            "direction": "bidirectional",
            "signal": {
              "kind": "dc",
              "voltage_v": {"min": 600, "max": 1000},
              "current_a": {"max": 2500}
            }
          },
          {
            "id": "ac_grid",
            "direction": "bidirectional",
            "signal": {
              "kind": "ac",
              "voltage_v_rms": 480,
              "phases": 3,
              "frequency_hz": {"nominal": 60, "range": [57, 63]},
              "current_a": {"max": 1804}
            }
          },
          {
            "id": "control_modbus",
            "direction": "bidirectional",
            "signal": {
              "kind": "data",
              "protocol": "ModbusTCP",
              "registers": 4000
            }
          }
        ],
        "grid_support_functions": {
          "active_power": {
            "ramp_rate_pct_sec": 10,
            "curtailment": true,
            "agc_response_s": 4
          },
          "reactive_power": {
            "capability": {
              "leading_pf": 0.85,
              "lagging_pf": 0.85,
              "q_at_zero_p": 0.44
            },
            "control_modes": ["pf", "q", "voltage", "droop"]
          },
          "frequency_response": {
            "droop": {
              "up_pct": 5,
              "down_pct": 5,
              "deadband_mhz": 36
            },
            "synthetic_inertia": {
              "h_constant_s": 4,
              "rocof_threshold_hz_s": 0.5
            }
          },
          "voltage_support": {
            "regulation_band_pu": 0.05,
            "response_time_ms": 200
          },
          "ride_through": {
            "lvrt": {
              "voltage_pu": [0, 0.5, 0.7, 0.9],
              "duration_ms": [150, 1000, 2000, 3000]
            },
            "hvrt": {
              "voltage_pu": [1.1, 1.15, 1.2],
              "duration_ms": [12000, 1000, 160]
            },
            "frequency": {
              "low_hz": 57,
              "high_hz": 61.8,
              "rocof_hz_s": 3
            }
          },
          "black_start": {
            "capable": true,
            "soft_start_time_s": 30,
            "grid_forming": true
          }
        }
      }
    }
  }
}
```

### 2.2 Grid Interface Components

```json
{
  "main_power_transformer": {
    "category": "transformer",
    "subcategory": "step_up",
    "metadata": {
      "manufacturer": "ABB",
      "model": "TrafoStar_100MVA",
      "standards": ["IEEE_C57", "IEC_60076"]
    },
    "ports": [
      {
        "id": "lv_winding",
        "direction": "input",
        "signal": {
          "kind": "ac",
          "voltage_v_rms": 34500,
          "phases": 3,
          "configuration": "delta"
        }
      },
      {
        "id": "hv_winding",
        "direction": "output",
        "signal": {
          "kind": "ac",
          "voltage_v_rms": 230000,
          "phases": 3,
          "configuration": "wye_grounded"
        }
      },
      {
        "id": "oltc",
        "direction": "control",
        "signal": {
          "kind": "control",
          "tap_positions": 33,
          "tap_range_pct": [-10, 10],
          "step_voltage_v": 1437.5
        }
      }
    ],
    "attributes": {
      "electrical": {
        "power_rating_mva": 100,
        "impedance_pct": 12.5,
        "x_r_ratio": 30,
        "no_load_loss_kw": 65,
        "load_loss_kw": 320,
        "magnetizing_current_pct": 0.5,
        "short_circuit_withstand": {
          "mechanical_ka": 40,
          "thermal_ka2s": 1600
        }
      },
      "thermal": {
        "cooling_type": "ONAN/ONAF/ONAF",
        "cooling_stages_mva": [60, 80, 100],
        "top_oil_rise_k": 55,
        "winding_rise_k": 65,
        "oil_volume_liters": 45000,
        "oil_type": "mineral|ester"
      },
      "physical": {
        "dimensions_m": [9, 4, 5],
        "weight_tons": 120,
        "oil_weight_tons": 35,
        "transport_weight_tons": 85,
        "sound_level_db": 72
      },
      "protection": {
        "differential_relay": "87T",
        "overcurrent": ["51", "51N"],
        "overvoltage": "59",
        "buchholz": true,
        "pressure_relief": true,
        "oil_temperature": true,
        "winding_temperature": true
      }
    },
    "testing": {
      "factory_tests": ["ratio", "vector_group", "impedance", "no_load_loss", "load_loss"],
      "site_tests": ["insulation_resistance", "tan_delta", "sfra", "dga"],
      "routine_tests": ["oil_analysis", "thermography", "partial_discharge"]
    }
  },

  "protection_relay": {
    "category": "protection",
    "subcategory": "multifunction_relay",
    "metadata": {
      "manufacturer": "SEL",
      "model": "SEL-487E",
      "firmware": "R507"
    },
    "ports": [
      {
        "id": "ct_inputs",
        "direction": "input",
        "signal": {
          "kind": "measurement",
          "channels": 18,
          "ratio": "variable",
          "burden_va": 0.5
        }
      },
      {
        "id": "vt_inputs",
        "direction": "input",
        "signal": {
          "kind": "measurement",
          "channels": 6,
          "ratio": "variable"
        }
      },
      {
        "id": "trip_outputs",
        "direction": "output",
        "signal": {
          "kind": "control",
          "contacts": 8,
          "voltage_vdc": 125,
          "current_a": 30
        }
      },
      {
        "id": "ethernet",
        "direction": "bidirectional",
        "signal": {
          "kind": "data",
          "protocol": ["IEC61850", "DNP3", "ModbusTCP"],
          "speed_mbps": 100,
          "redundancy": "PRP"
        }
      }
    ],
    "protection_functions": {
      "differential": {
        "87T": {"enabled": true, "slope_pct": 30, "min_operate_pu": 0.3},
        "87N": {"enabled": true, "pickup_pu": 0.1}
      },
      "overcurrent": {
        "50": {"pickup_a": 5000, "time_delay_ms": 0},
        "51": {"pickup_a": 1000, "time_dial": 3, "curve": "IEC_very_inverse"},
        "50N": {"pickup_a": 500, "time_delay_ms": 100},
        "51N": {"pickup_a": 100, "time_dial": 2, "curve": "IEC_standard_inverse"}
      },
      "voltage": {
        "27": {"pickup_v": 0.88, "time_delay_s": 2},
        "59": {"pickup_v": 1.1, "time_delay_s": 2},
        "47": {"pickup_v": 0.05, "time_delay_s": 0.5}
      },
      "frequency": {
        "81O": {"pickup_hz": 61.8, "time_delay_s": 0.5},
        "81U": {"pickup_hz": 57.0, "time_delay_s": 0.5},
        "81R": {"pickup_hz_s": 3.0, "time_delay_s": 0.1}
      },
      "distance": {
        "21": {
          "zones": [
            {"reach_ohm": 5, "angle_deg": 85, "time_delay_ms": 0},
            {"reach_ohm": 8, "angle_deg": 85, "time_delay_ms": 400}
          ]
        }
      },
      "sync_check": {
        "25": {
          "voltage_diff_v": 5000,
          "angle_diff_deg": 10,
          "freq_diff_hz": 0.1
        }
      }
    }
  }
}
```

### 2.3 Structural and Mechanical Components

```json
{
  "tracker_foundation": {
    "category": "structural",
    "subcategory": "foundation",
    "metadata": {
      "type": "driven_pile",
      "material": "galvanized_steel",
      "standard": "AISC_360"
    },
    "attributes": {
      "geometry": {
        "shape": "W_section",
        "designation": "W6x20",
        "length_m": 4.5,
        "embedment_m": 3.5,
        "reveal_m": 1.0
      },
      "material_properties": {
        "yield_strength_mpa": 345,
        "elastic_modulus_gpa": 200,
        "density_kg_m3": 7850,
        "corrosion_allowance_mm": 1.5
      },
      "capacity": {
        "axial_compression_kn": 150,
        "axial_tension_kn": 120,
        "lateral_kn": 45,
        "moment_kn_m": 15,
        "factors_of_safety": {
          "dead_load": 1.2,
          "live_load": 1.6,
          "wind_load": 1.3,
          "seismic_load": 1.0
        }
      },
      "soil_interaction": {
        "soil_type": "silty_clay",
        "bearing_capacity_kpa": 200,
        "friction_angle_deg": 28,
        "cohesion_kpa": 25,
        "lateral_subgrade_modulus_mpa_m": 10
      }
    },
    "installation": {
      "method": "impact_driving",
      "equipment": "pile_driver_5ton",
      "refusal_criteria": "10_blows_per_25mm",
      "torque_test_required": true,
      "pull_test_required": true
    }
  },

  "tracker_structure": {
    "category": "structural",
    "subcategory": "single_axis_tracker",
    "metadata": {
      "manufacturer": "NEXTracker",
      "model": "NX_Horizon",
      "row_length_m": 90
    },
    "ports": [
      {
        "id": "motor_control",
        "direction": "input",
        "signal": {
          "kind": "control",
          "protocol": "zigbee",
          "commands": ["stow", "track", "position"]
        }
      }
    ],
    "attributes": {
      "mechanical": {
        "tracking_range_deg": [-60, 60],
        "accuracy_deg": 0.5,
        "backtracking": true,
        "modules_per_row": 90,
        "module_mounting": "portrait_2P",
        "gcr": 0.35
      },
      "structural_members": {
        "torque_tube": {
          "material": "galvanized_steel",
          "diameter_mm": 150,
          "wall_thickness_mm": 5,
          "span_m": 12,
          "max_deflection_mm": 50
        },
        "purlin": {
          "profile": "C_channel",
          "dimensions_mm": [80, 40, 3],
          "spacing_m": 1.2
        }
      },
      "loading": {
        "dead_load_kg_m2": 15,
        "live_load_pa": 0,
        "wind_load": {
          "design_speed_mps": 45,
          "exposure_category": "C",
          "pressure_coefficients": {
            "0_deg": 1.3,
            "45_deg": 0.9,
            "60_deg": 0.7,
            "stow": 0.2
          }
        },
        "snow_load": {
          "ground_snow_kpa": 1.5,
          "flat_roof_kpa": 1.2,
          "sliding_factor": 0.8
        },
        "seismic": {
          "site_class": "D",
          "sds": 0.5,
          "importance_factor": 1.0
        }
      }
    },
    "control_algorithms": {
      "tracking": {
        "algorithm": "astronomical",
        "update_frequency_min": 5,
        "terrain_following": true
      },
      "stow_conditions": {
        "wind_speed_mps": 20,
        "snow_depth_cm": 5,
        "hail_size_mm": 25,
        "maintenance_mode": 0
      },
      "backtracking": {
        "algorithm": "true_tracking",
        "shade_tolerance_pct": 0,
        "optimization": "energy_yield"
      }
    }
  }
}
```

### 2.4 Photovoltaic Module Components

```json
{
  "libraries": {
    "components": {
      "pv_module": {
        "category": "generation",
        "subcategory": "photovoltaic",
        "metadata": {
          "manufacturer": "LONGi",
          "model": "Hi-MO_6_LR5-72HTH-570M",
          "technology": "Mono_PERC_Bifacial",
          "certifications": ["IEC61215", "IEC61730", "UL1703", "IEC62804"]
        },

        "ports": [
          {
            "id": "dc_positive",
            "direction": "output",
            "signal": {
              "kind": "dc",
              "voltage_v": {"stc": 49.8, "noct": 46.5, "max_system": 1500},
              "current_a": {"stc": 11.44, "noct": 9.21, "short_circuit": 12.02}
            }
          },
          {
            "id": "dc_negative",
            "direction": "output",
            "signal": {
              "kind": "dc",
              "connector": "MC4_EVO2",
              "cable_length_m": 1.2,
              "cable_cross_section_mm2": 4
            }
          }
        ],

        "attributes": {
          "electrical": {
            "power_stc_w": 570,
            "efficiency_pct": 22.3,
            "voltage_temp_coef_pct_k": -0.28,
            "current_temp_coef_pct_k": 0.048,
            "power_temp_coef_pct_k": -0.35,
            "noct_c": 44,
            "cells": 144,
            "bypass_diodes": 3,
            "bifaciality_factor": 0.85
          },

          "degradation": {
            "initial_degradation": {
              "lid": {
                "mechanism": "boron_oxygen_complex",
                "first_year_pct": 2.0,
                "stabilization_kwh_m2": 5,
                "recovery_possible": true
              },
              "pid": {
                "mechanism": "sodium_ion_migration",
                "susceptibility": "low",
                "test_conditions": {
                  "voltage_v": -1500,
                  "temperature_c": 85,
                  "humidity_pct": 85,
                  "duration_hours": 96
                },
                "max_power_loss_pct": 5
              }
            },

            "annual_degradation": {
              "standard_rate_pct": 0.45,
              "year_1_rate_pct": 2.5,
              "years_2_30_rate_pct": 0.45,

              "mechanisms": {
                "uv_degradation": {
                  "backsheet_yellowing_rate": 0.1,
                  "encapsulant_browning_rate": 0.05
                },
                "thermal_cycling": {
                  "solder_fatigue_cycles": 1000000,
                  "interconnect_stress_factor": 1.2
                },
                "moisture_ingress": {
                  "wvtr_g_m2_day": 0.1,
                  "edge_seal_degradation_mm_year": 0.5
                },
                "mechanical_stress": {
                  "microcrack_propagation_rate": 0.02,
                  "delamination_risk": "low"
                }
              },

              "acceleration_factors": {
                "high_temperature": {
                  "threshold_c": 70,
                  "acceleration_factor": 2.0
                },
                "high_humidity": {
                  "threshold_pct": 85,
                  "acceleration_factor": 1.5
                },
                "soiling": {
                  "threshold_loss_pct": 5,
                  "hotspot_risk_multiplier": 3
                },
                "partial_shading": {
                  "mismatch_factor": 1.3,
                  "bypass_diode_stress": 2.0
                }
              }
            },

            "warranty": {
              "product_years": 12,
              "performance": {
                "year_1_min_pct": 98,
                "year_30_min_pct": 82.6,
                "annual_degradation_max_pct": 0.45
              },
              "claims_process": {
                "testing_standard": "IEC61215",
                "sample_size_pct": 2,
                "claim_threshold_pct": 3
              }
            },

            "end_of_life": {
              "expected_lifetime_years": 35,
              "failure_modes": [
                {
                  "mode": "backsheet_cracking",
                  "probability_30_years": 0.05,
                  "detection": "visual_inspection"
                },
                {
                  "mode": "junction_box_failure",
                  "probability_30_years": 0.02,
                  "detection": "thermal_imaging"
                },
                {
                  "mode": "glass_breakage",
                  "probability_30_years": 0.01,
                  "detection": "visual_inspection"
                }
              ]
            }
          },

          "physical": {
            "dimensions_mm": [2278, 1134, 35],
            "weight_kg": 28.5,
            "glass": {
              "type": "tempered_low_iron",
              "thickness_mm": 3.2,
              "ar_coating": true,
              "transmittance_pct": 94
            },
            "frame": {
              "material": "anodized_aluminum_6005-T5",
              "color": "silver|black",
              "drainage_holes": 8
            },
            "mounting_holes": {
              "pattern": "8x_slots",
              "compatibility": ["universal_clamp", "rail_mount"]
            }
          }
        }
      }
    }
  }
}
```

---

## PART III: ENHANCED FINANCIAL MODELING

### 3.1 Comprehensive Financial Structure

```json
{
  "finance": {
    "project_info": {
      "financial_close": "2025-06-01",
      "construction_start": "2025-07-01",
      "cod_target": "2026-12-31",
      "operational_life_years": 35,
      "analysis_period_years": 40,
      "base_year": 2025,
      "currency": {
        "reporting": "USD",
        "local": "USD",
        "exchange_rate": 1.0
      }
    },

    "capital_structure": {
      "total_investment": 150000000,
      "debt": {
        "senior": {
          "amount": 90000000,
          "percentage": 0.60,
          "rate_pct": 5.5,
          "term_years": 18,
          "grace_period_years": 1,
          "repayment": "sculpted",
          "dscr_target": 1.35
        },
        "subordinated": {
          "amount": 15000000,
          "percentage": 0.10,
          "rate_pct": 8.0,
          "term_years": 10
        }
      },
      "equity": {
        "sponsor": {
          "amount": 35000000,
          "percentage": 0.233,
          "return_target_pct": 12
        },
        "tax_equity": {
          "amount": 10000000,
          "percentage": 0.067,
          "flip_date": "year_6",
          "pre_flip_allocation_pct": 99,
          "post_flip_allocation_pct": 5
        }
      },
      "grants": {
        "federal": 0,
        "state": 2000000,
        "utility": 500000
      }
    },

    "capex": {
      "development": {
        "land_acquisition": {
          "purchase": 0,
          "lease_prepayment": 500000,
          "due_diligence": 200000,
          "legal": 150000
        },
        "permitting": {
          "environmental": 800000,
          "building": 200000,
          "interconnection": 1500000,
          "consultants": 600000
        },
        "design_engineering": {
          "preliminary": 500000,
          "detailed": 1500000,
          "owners_engineer": 800000
        }
      },

      "equipment": {
        "modules": {
          "model": "LONGi_Hi-MO_6_72_570",
          "quantity": 263158,
          "unit_cost": 0.28,
          "total": 73684240,
          "delivery": "DAP",
          "payment_terms": {
            "deposit_pct": 10,
            "on_delivery_pct": 80,
            "on_commissioning_pct": 10
          }
        },
        "inverters": {
          "model": "SMA_SC4600UP",
          "quantity": 22,
          "unit_cost": 120000,
          "total": 2640000,
          "spares_pct": 5
        },
        "trackers": {
          "model": "NEXTracker_NX_Horizon",
          "quantity_mw": 150,
          "unit_cost_per_w": 0.08,
          "total": 12000000
        },
        "bess": {
          "energy_mwh": 50,
          "power_mw": 25,
          "unit_cost_per_kwh": 320,
          "total": 16000000,
          "augmentation_reserve_pct": 10
        },
        "substation": {
          "transformer_mva": 175,
          "unit_cost": 3500000,
          "switchgear": 1500000,
          "total": 5000000
        }
      },

      "construction": {
        "site_preparation": {
          "clearing_grubbing": 1200000,
          "grading": 2300000,
          "roads": 1800000,
          "drainage": 900000,
          "fencing": 600000
        },
        "installation": {
          "foundation": 4500000,
          "mechanical": 8000000,
          "electrical_dc": 6000000,
          "electrical_ac": 4000000,
          "grounding": 1200000,
          "scada": 800000
        },
        "grid_connection": {
          "transmission_line_km": 15,
          "cost_per_km": 400000,
          "substation_upgrades": 2000000,
          "total": 8000000
        }
      },

      "soft_costs": {
        "epc_management": 4500000,
        "construction_management": 1500000,
        "insurance": {
          "construction_all_risk": 800000,
          "delay_in_startup": 400000,
          "liability": 200000
        },
        "financing_costs": {
          "arrangement_fee": 1800000,
          "commitment_fee": 900000,
          "legal_fee": 600000,
          "idc": 4200000
        },
        "commissioning": {
          "testing": 800000,
          "grid_compliance": 400000,
          "performance_testing": 300000
        }
      },

      "contingency": {
        "design_development_pct": 3,
        "equipment_pct": 2,
        "construction_pct": 5,
        "total": 6000000
      },

      "total_capex": 148324240,
      "cost_per_wdc": 0.989,
      "cost_per_wac": 1.186
    },

    "opex": {
      "fixed_annual": {
        "operations": {
          "staff": {
            "plant_manager": 120000,
            "operators": 360000,
            "technicians": 480000,
            "admin": 180000,
            "total": 1140000
          },
          "asset_management": 250000,
          "monitoring": 50000,
          "security": 200000
        },
        "maintenance": {
          "preventive": {
            "scheduled_inspections": 150000,
            "module_cleaning": 200000,
            "vegetation": 100000,
            "tracker_maintenance": 180000
          },
          "corrective_reserve": 200000,
          "spare_parts_inventory": 150000
        },
        "insurance": {
          "property": 900000,
          "liability": 200000,
          "business_interruption": 300000
        },
        "land": {
          "lease": 450000,
          "property_tax": 800000
        },
        "administration": {
          "accounting": 60000,
          "legal": 80000,
          "regulatory_compliance": 100000,
          "community_relations": 50000
        },
        "total_fixed": 5060000,
        "per_mw": 40480,
        "escalation_pct": 2.5
      },

      "variable": {
        "per_mwh": {
          "consumables": 0.5,
          "grid_charges": 1.2,
          "total": 1.7
        },
        "performance_based": {
          "availability_bonus_penalty": "symmetric",
          "target_pct": 97,
          "rate_per_pct": 50000
        }
      },

      "lifecycle_costs": {
        "year_5": {
          "inverter_overhaul": 500000
        },
        "year_10": {
          "tracker_refurbishment": 1200000,
          "dc_repowering": 800000
        },
        "year_15": {
          "inverter_replacement": 2000000,
          "transformer_overhaul": 400000
        },
        "year_20": {
          "major_refurbishment": 3000000,
          "bess_augmentation": 2000000
        },
        "year_25": {
          "ppa_renewal_costs": 500000
        }
      }
    },

    "revenue": {
      "power_purchase_agreement": {
        "offtaker": "Pacific_Gas_Electric",
        "credit_rating": "BBB+",
        "start_date": "2027-01-01",
        "term_years": 25,
        "pricing": {
          "structure": "escalating",
          "initial_rate": 0.055,
          "escalation_pct": 2.0,
          "time_of_delivery": {
            "peak": {"multiplier": 1.3, "hours": [16, 21]},
            "shoulder": {"multiplier": 1.0, "hours": [6, 16]},
            "off_peak": {"multiplier": 0.7, "hours": [21, 6]}
          }
        },
        "curtailment": {
          "economic_allowed_hours": 200,
          "compensated": false,
          "grid_allowed_hours": "unlimited",
          "compensation_rate": 0
        },
        "performance": {
          "minimum_delivery_pct": 80,
          "liquidated_damages": 100,
          "availability_requirement_pct": 95
        }
      },

      "capacity_payment": {
        "contract": "resource_adequacy",
        "capacity_mw": 100,
        "rate_kw_month": 4.5,
        "term_years": 10,
        "annual_revenue": 5400000
      },

      "ancillary_services": {
        "frequency_regulation": {
          "capacity_mw": 10,
          "rate_per_mw_hour": 15,
          "hours_per_year": 2000,
          "annual_revenue": 300000
        },
        "spinning_reserve": {
          "capacity_mw": 20,
          "rate_per_mw_hour": 8,
          "hours_per_year": 1000,
          "annual_revenue": 160000
        },
        "voltage_support": {
          "annual_payment": 200000
        }
      },

      "renewable_energy_credits": {
        "type": "bundled|unbundled",
        "volume_per_mwh": 1,
        "price_per_rec": 25,
        "contract_years": 10,
        "buyer": "voluntary_market"
      },

      "tax_benefits": {
        "investment_tax_credit": {
          "rate_pct": 30,
          "basis": 145000000,
          "amount": 43500000,
          "safe_harbor_date": "2024-12-31"
        },
        "production_tax_credit": {
          "applicable": false
        },
        "depreciation": {
          "method": "MACRS",
          "recovery_period_years": 5,
          "bonus_pct": 80,
          "year_1_deduction": 116000000
        },
        "state_incentives": {
          "property_tax_abatement_pct": 50,
          "sales_tax_exemption": true,
          "state_credits": 2000000
        }
      }
    },

    "financial_model": {
      "assumptions": {
        "inflation_rate_pct": 2.5,
        "discount_rate_pct": 6.5,
        "tax_rate_pct": 21,
        "degradation_rate_pct": 0.5,
        "availability_pct": 97,
        "ppa_renewal_probability": 0.8,
        "terminal_value_multiple": 8
      },

      "energy_production": {
        "year_1_gross_mwh": 315000,
        "year_1_net_mwh": 305550,
        "capacity_factor_pct": 23.2,
        "performance_ratio": 0.845,
        "losses": {
          "soiling_pct": 2,
          "shading_pct": 1,
          "snow_pct": 0.5,
          "module_quality_pct": 0.3,
          "mismatch_pct": 1,
          "dc_wiring_pct": 1.5,
          "inverter_pct": 2,
          "ac_wiring_pct": 1,
          "transformer_pct": 1,
          "availability_pct": 3,
          "curtailment_pct": 1,
          "total_pct": 14.3,
          "climate_adjustments": {
            "arid": {"soiling_pct": 5, "total_pct": 17.8},
            "temperate": {"soiling_pct": 2, "total_pct": 14.3}
          }
        }
      },

      "key_metrics": {
        "project_irr_pct": 7.8,
        "equity_irr_pct": 12.4,
        "modified_irr_pct": 10.2,
        "npv_millions": 28.5,
        "payback_period_years": 9.8,
        "lcoe": {
          "nominal_usd_mwh": 48.2,
          "real_usd_mwh": 39.6,
          "including_tax_benefits_usd_mwh": 31.2
        },
        "debt_metrics": {
          "average_dscr": 1.42,
          "minimum_dscr": 1.21,
          "llcr": 1.38,
          "plcr": 1.45
        }
      },

      "sensitivity_analysis": {
        "single_factor": [
          {
            "parameter": "capex",
            "range_pct": [-20, 20],
            "irr_impact": [9.8, 5.9]
          },
          {
            "parameter": "energy_yield",
            "range_pct": [-10, 10],
            "irr_impact": [6.2, 9.5]
          },
          {
            "parameter": "ppa_rate",
            "range_pct": [-10, 10],
            "irr_impact": [6.5, 9.2]
          },
          {
            "parameter": "opex",
            "range_pct": [-20, 20],
            "irr_impact": [8.3, 7.3]
          }
        ],
        "scenario_analysis": [
          {
            "scenario": "base_case",
            "probability_pct": 50,
            "irr_pct": 7.8
          },
          {
            "scenario": "downside",
            "probability_pct": 20,
            "adjustments": {
              "capex_increase_pct": 10,
              "energy_decrease_pct": 5,
              "opex_increase_pct": 15
            },
            "irr_pct": 5.2
          },
          {
            "scenario": "upside",
            "probability_pct": 30,
            "adjustments": {
              "capex_decrease_pct": 5,
              "energy_increase_pct": 5,
              "ppa_rate_increase_pct": 10
            },
            "irr_pct": 10.1
          }
        ],
        "monte_carlo": {
          "iterations": 10000,
          "distributions": [
            {
              "variable": "solar_resource",
              "type": "normal",
              "mean": 1.0,
              "std_dev": 0.05
            },
            {
              "variable": "capex",
              "type": "triangular",
              "min": 0.95,
              "mode": 1.0,
              "max": 1.15
            },
            {
              "variable": "availability",
              "type": "beta",
              "alpha": 50,
              "beta": 2
            }
          ],
          "results": {
            "p10_irr": 5.8,
            "p50_irr": 7.8,
            "p90_irr": 9.9,
            "probability_irr_above_6_pct": 78,
            "probability_dscr_above_1_2": 92
          }
        }
      }
    }
  }
}
```

### 3.2 Regional and Climate-Based Financial Adjustments

```json
{
  "finance": {
    "regional_adjustments": {
      "currency_management": {
        "base_currency": "USD",
        "conversion_method": "dynamic_api",
        "api_configuration": {
          "provider": "xe|oanda|ecb",
          "endpoint": "https://api.exchangerates.com/v1/latest",
          "update_frequency_hours": 24,
          "fallback_rates": {
            "EUR_USD": 1.10,
            "GBP_USD": 1.27,
            "JPY_USD": 0.0067,
            "AUD_USD": 0.65
          }
        },
        "hedging_strategy": {
          "instruments": ["forward_contracts", "options"],
          "hedge_ratio_pct": 80,
          "tenor_months": [6, 12, 24]
        }
      },

      "climate_specific_losses": {
        "climate_zones": {
          "arid_desert": {
            "classification": "BWh",
            "characteristics": {
              "annual_rainfall_mm": 250,
              "dust_events_per_year": 30,
              "temperature_range_c": [-5, 50]
            },
            "loss_adjustments": {
              "soiling_pct": 5.5,
              "module_degradation_multiplier": 1.3,
              "thermal_losses_pct": 0.8,
              "total_system_losses_pct": 18.2
            },
            "mitigation": {
              "cleaning_frequency_per_year": 26,
              "coating_type": "anti_soiling_hydrophobic",
              "tracker_stow_strategy": "horizontal_dust_storms"
            }
          },

          "tropical_monsoon": {
            "classification": "Am",
            "characteristics": {
              "annual_rainfall_mm": 2500,
              "humidity_avg_pct": 85,
              "cyclone_risk": "high"
            },
            "loss_adjustments": {
              "soiling_pct": 1.5,
              "cloud_losses_pct": 3.5,
              "humidity_degradation_multiplier": 1.5,
              "total_system_losses_pct": 16.8
            },
            "mitigation": {
              "drainage_enhancement": true,
              "corrosion_protection": "enhanced_galvanization",
              "wind_design_speed_mps": 60
            }
          },

          "temperate_continental": {
            "classification": "Dfb",
            "characteristics": {
              "snow_days_per_year": 60,
              "freeze_thaw_cycles": 100,
              "hail_risk": "moderate"
            },
            "loss_adjustments": {
              "snow_losses_pct": 2.5,
              "soiling_pct": 2.0,
              "thermal_cycling_degradation": 1.2,
              "total_system_losses_pct": 15.3
            },
            "mitigation": {
              "snow_shedding_angle_deg": 35,
              "hail_stow_protocol": true,
              "cold_weather_lubricants": true
            }
          },

          "coastal_marine": {
            "classification": "Cfb",
            "characteristics": {
              "salt_deposition_mg_m2_day": 50,
              "corrosion_category": "C4",
              "fog_days_per_year": 100
            },
            "loss_adjustments": {
              "soiling_pct": 2.5,
              "corrosion_factor": 2.0,
              "marine_layer_losses_pct": 1.5,
              "total_system_losses_pct": 15.8
            },
            "mitigation": {
              "material_spec": "marine_grade_316L",
              "coating": "duplex_system",
              "washing_frequency_per_year": 12
            }
          }
        },

        "dynamic_adjustment_algorithm": {
          "inputs": [
            "location_coordinates",
            "historical_weather_data",
            "soil_type",
            "vegetation_index"
          ],
          "ml_model": {
            "type": "gradient_boosted_trees",
            "training_data_years": 20,
            "validation_rmse_pct": 2.3,
            "update_frequency_months": 6
          },
          "outputs": {
            "adjusted_pr": "number",
            "adjusted_degradation_rate": "number",
            "maintenance_schedule_optimization": "object"
          }
        }
      },

      "extreme_weather_risk_pricing": {
        "insurance_adjustments": {
          "hurricane_zone": {
            "premium_multiplier": 2.5,
            "deductible_pct": 5,
            "parametric_trigger": "wind_speed_150_mph"
          },
          "earthquake_zone": {
            "premium_multiplier": 1.8,
            "deductible_pct": 10,
            "seismic_design_factor": 1.5
          },
          "wildfire_zone": {
            "premium_multiplier": 2.2,
            "deductible_pct": 3,
            "defensible_space_m": 30
          }
        },

        "resilience_investments": {
          "hardening_capex_increase_pct": 8,
          "benefit_cost_ratio": 4.2,
          "fema_grant_eligibility": true,
          "resilience_score": 85
        }
      }
    },

    "advanced_monte_carlo_implementation": {
      "algorithm": {
        "code_snippet": {
          "language": "python",
          "implementation": "# See implementation in Appendix A"
        }
      },

      "correlation_matrix": {
        "definition": "Pearson correlation coefficients between risk factors",
        "matrix": {
          "solar_resource": {
            "solar_resource": 1.0,
            "temperature": -0.3,
            "soiling": -0.2,
            "availability": 0.1
          },
          "temperature": {
            "solar_resource": -0.3,
            "temperature": 1.0,
            "degradation": 0.4,
            "efficiency": -0.6
          },
          "soiling": {
            "solar_resource": -0.2,
            "temperature": 0.1,
            "soiling": 1.0,
            "cleaning_cost": 0.7
          }
        }
      }
    }
  }
}
```

---

## PART IV: OPERATIONS AND LIFECYCLE MANAGEMENT

### 4.1 Comprehensive Operations Structure

```json
{
  "operations": {
    "commissioning": {
      "phases": [
        {
          "phase": "mechanical_completion",
          "target_date": "2026-10-01",
          "criteria": {
            "modules_installed_pct": 100,
            "dc_wiring_complete_pct": 100,
            "grounding_complete_pct": 100,
            "trackers_operational_pct": 100
          },
          "inspections": [
            {
              "type": "torque_verification",
              "sample_size_pct": 10,
              "pass_criteria": "within_10_pct",
              "results": "documented"
            },
            {
              "type": "module_inspection",
              "defects_allowed_pct": 0.5,
              "methods": ["visual", "el_imaging"],
              "documentation": "photo_report"
            }
          ]
        },
        {
          "phase": "electrical_testing",
          "target_date": "2026-11-01",
          "tests": [
            {
              "test": "insulation_resistance",
              "standard": "IEC_62446-1",
              "minimum_mohm": 1,
              "voltage_vdc": 1000,
              "results": []
            },
            {
              "test": "continuity",
              "standard": "IEC_62446-1",
              "maximum_ohm": 0.5,
              "results": []
            },
            {
              "test": "polarity",
              "method": "visual_and_measurement",
              "results": []
            },
            {
              "test": "ground_resistance",
              "standard": "IEEE_81",
              "maximum_ohm": 5,
              "method": "fall_of_potential",
              "results": []
            },
            {
              "test": "string_iv_curves",
              "sample_size_pct": 100,
              "acceptance_criteria": "within_5_pct_nameplate",
              "results": []
            }
          ]
        },
        {
          "phase": "performance_testing",
          "target_date": "2026-12-01",
          "tests": [
            {
              "test": "capacity_test",
              "standard": "ASTM_E2848",
              "duration_days": 7,
              "weather_stations": 3,
              "uncertainty_target_pct": 3,
              "provisional_acceptance_pct": 98,
              "final_acceptance_pct": 100
            },
            {
              "test": "grid_compliance",
              "requirements": [
                {
                  "function": "voltage_ride_through",
                  "standard": "IEEE_1547",
                  "test_points": 5
                },
                {
                  "function": "frequency_response",
                  "standard": "NERC_PRC_024",
                  "test_points": 4
                },
                {
                  "function": "reactive_power",
                  "range_pf": [0.85, 1.0, 0.85],
                  "test_points": 7
                }
              ]
            },
            {
              "test": "protection_coordination",
              "relays_tested": ["50", "51", "27", "59", "81", "87"],
              "coordination_verified": true
            }
          ]
        }
      ],

      "documentation": {
        "as_built_drawings": {
          "electrical_sld": true,
          "three_line": true,
          "dc_wiring": true,
          "ac_collection": true,
          "grounding": true,
          "scada_architecture": true
        },
        "equipment_documentation": {
          "datasheets": true,
          "certificates": true,
          "warranties": true,
          "manuals": true,
          "spare_parts_list": true
        },
        "test_reports": {
          "factory_test": true,
          "site_acceptance": true,
          "commissioning": true,
          "performance": true
        }
      }
    },

    "monitoring": {
      "data_acquisition": {
        "scada_system": {
          "platform": "Ignition_8.1",
          "servers": {
            "primary": {"ip": "10.0.1.10", "role": "active"},
            "secondary": {"ip": "10.0.1.11", "role": "standby"}
          },
          "historians": {
            "type": "OSI_PI",
            "retention_years": 7,
            "resolution": {
              "raw_days": 7,
              "minute_days": 30,
              "hourly_days": 365,
              "daily_years": 7
            }
          }
        },
        "data_points": {
          "meteorological": {
            "ghi": {"units": "W/m2", "scan_rate_s": 1},
            "dni": {"units": "W/m2", "scan_rate_s": 1},
            "ambient_temp": {"units": "C", "scan_rate_s": 1},
            "module_temp": {"units": "C", "scan_rate_s": 10},
            "wind_speed": {"units": "m/s", "scan_rate_s": 1},
            "wind_direction": {"units": "deg", "scan_rate_s": 1}
          },
          "electrical": {
            "string_current": {"count": 10000, "units": "A", "scan_rate_s": 10},
            "string_voltage": {"count": 10000, "units": "V", "scan_rate_s": 10},
            "inverter_power": {"count": 30, "units": "kW", "scan_rate_s": 1},
            "inverter_energy": {"count": 30, "units": "kWh", "scan_rate_s": 60},
            "grid_voltage": {"count": 3, "units": "V", "scan_rate_s": 1},
            "grid_frequency": {"count": 1, "units": "Hz", "scan_rate_s": 1}
          },
          "calculated": {
            "performance_ratio": {"formula": "actual/expected", "scan_rate_s": 300},
            "availability": {"formula": "uptime/period", "scan_rate_s": 300},
            "capacity_factor": {"formula": "energy/rated", "scan_rate_s": 3600},
            "soiling_ratio": {"formula": "clean/soiled", "scan_rate_s": 3600}
          }
        },
        "alarms": {
          "priorities": {
            "critical": {"response_min": 15, "examples": ["inverter_trip", "transformer_fault"]},
            "high": {"response_min": 60, "examples": ["tracker_fault", "string_open"]},
            "medium": {"response_hours": 4, "examples": ["communication_loss", "performance_low"]},
            "low": {"response_hours": 24, "examples": ["sensor_drift", "soiling_high"]}
          },
          "notification": {
            "methods": ["email", "sms", "app_push"],
            "escalation": {
              "level_1": {"delay_min": 0, "contacts": ["operator"]},
              "level_2": {"delay_min": 30, "contacts": ["supervisor"]},
              "level_3": {"delay_min": 120, "contacts": ["manager"]}
            }
          }
        }
      },

      "performance_analysis": {
        "kpis": [
          {
            "metric": "energy_yield",
            "target_mwh_day": 850,
            "calculation": "sum(inverter_energy)",
            "reporting": "daily"
          },
          {
            "metric": "performance_ratio",
            "target": 0.84,
            "calculation": "actual_energy/(irradiance*area*efficiency)",
            "reporting": "daily"
          },
          {
            "metric": "availability",
            "target_pct": 97,
            "calculation": "productive_time/total_time",
            "exclusions": ["grid_outage", "curtailment"],
            "reporting": "monthly"
          },
          {
            "metric": "capacity_factor",
            "target_pct": 23,
            "calculation": "energy_produced/rated_capacity",
            "reporting": "monthly"
          }
        ],
        "reporting": {
          "daily": {
            "generation_summary": true,
            "availability_report": true,
            "alarm_summary": true,
            "weather_summary": true
          },
          "monthly": {
            "performance_report": true,
            "maintenance_summary": true,
            "financial_summary": true,
            "compliance_report": true
          },
          "annual": {
            "comprehensive_report": true,
            "warranty_compliance": true,
            "degradation_analysis": true,
            "budget_variance": true
          }
        }
      }
    },

    "maintenance": {
      "preventive": {
        "schedule": [
          {
            "task": "visual_inspection",
            "frequency": "quarterly",
            "duration_hours": 16,
            "crew_size": 2,
            "checklist": [
              "module_damage",
              "soiling_level",
              "vegetation_encroachment",
              "erosion_issues",
              "fence_integrity",
              "signage_condition"
            ]
          },
          {
            "task": "thermographic_inspection",
            "frequency": "annual",
            "duration_days": 3,
            "crew_size": 2,
            "equipment": ["flir_drone", "handheld_camera"],
            "defect_criteria": {
              "hot_spot_delta_c": 20,
              "module_delta_c": 5,
              "connection_delta_c": 10
            }
          },
          {
            "task": "iv_curve_testing",
            "frequency": "annual",
            "sample_pct": 5,
            "duration_days": 5,
            "crew_size": 2,
            "acceptance": "within_8_pct"
          },
          {
            "task": "tracker_maintenance",
            "frequency": "biannual",
            "duration_days": 10,
            "crew_size": 4,
            "activities": [
              "lubrication",
              "torque_check",
              "alignment_verification",
              "controller_calibration",
              "drive_inspection"
            ]
          },
          {
            "task": "inverter_maintenance",
            "frequency": "annual",
            "duration_hours": 8,
            "crew_size": 2,
            "activities": [
              "filter_replacement",
              "torque_verification",
              "thermal_inspection",
              "protection_testing",
              "firmware_update"
            ]
          },
          {
            "task": "module_cleaning",
            "frequency": "as_needed",
            "trigger": "soiling_loss_5_pct",
            "method": "robotic|manual|vehicle",
            "water_consumption_l_per_module": 0.5,
            "duration_days": 5,
            "crew_size": 4
          }
        ],

        "vegetation_management": {
          "mowing": {
            "frequency": "monthly",
            "height_target_cm": 15,
            "method": "mechanical|sheep"
          },
          "herbicide": {
            "frequency": "biannual",
            "type": "pre_emergent",
            "application_rate_l_per_ha": 5
          },
          "tree_trimming": {
            "frequency": "annual",
            "clearance_m": 10
          }
        }
      },

      "corrective": {
        "response_matrix": {
          "module_failure": {
            "detection": "string_monitoring",
            "diagnosis_time_hours": 1,
            "repair_time_hours": 0.5,
            "spare_required": true,
            "skill_level": "technician"
          },
          "inverter_trip": {
            "detection": "scada_alarm",
            "diagnosis_time_hours": 2,
            "repair_time_hours": 4,
            "spare_required": "possibly",
            "skill_level": "engineer"
          },
          "tracker_fault": {
            "detection": "controller_alarm",
            "diagnosis_time_hours": 1,
            "repair_time_hours": 2,
            "spare_required": "possibly",
            "skill_level": "technician"
          },
          "transformer_fault": {
            "detection": "protection_relay",
            "diagnosis_time_hours": 4,
            "repair_time_days": 30,
            "spare_required": false,
            "skill_level": "specialist"
          }
        },

        "spare_parts": {
          "critical": {
            "modules": {"quantity": 300, "percentage": 0.1},
            "fuses": {"quantity": 500, "types": ["15A", "20A", "25A", "30A"]},
            "inverter_cards": {"quantity": 10, "types": ["control", "power", "communication"]},
            "tracker_motors": {"quantity": 10}
          },
          "consumables": {
            "filters": {"quantity": 100},
            "lubricants_liters": 200,
            "cleaning_supplies": "adequate"
          },
          "tools": {
            "specialized": ["iv_curve_tracer", "insulation_tester", "thermal_camera"],
            "standard": ["multimeter", "clamp_meter", "torque_wrench"]
          }
        }
      },

      "warranty_claims": {
        "process": {
          "detection": "monitoring|inspection",
          "documentation": ["photos", "serial_numbers", "test_results"],
          "submission": "manufacturer_portal",
          "approval_time_days": 30,
          "replacement_time_days": 60
        },
        "tracking": []
      }
    },

    "service_events": [
      {
        "id": "SVC_001",
        "date": "2027-03-15",
        "type": "preventive",
        "category": "inspection",
        "description": "Q1 visual inspection",
        "findings": [
          {
            "issue": "vegetation_encroachment",
            "severity": "low",
            "location": "array_block_3",
            "action": "scheduled_mowing"
          }
        ],
        "labor_hours": 16,
        "cost": 1200,
        "completed_by": "internal_team"
      }
    ],

    "performance_tracking": {
      "degradation": {
        "measurement_method": "capacity_test|regression_analysis",
        "frequency": "annual",
        "baseline_year": 2027,
        "results": [
          {
            "year": 2027,
            "measured_capacity_mw": 149.5,
            "degradation_pct": 0.33,
            "weather_corrected": true
          }
        ]
      },
      "availability": {
        "calculation": "time_based|energy_based",
        "target_pct": 97,
        "actual": [
          {
            "period": "2027_Q1",
            "availability_pct": 97.8,
            "downtime_hours": 48,
            "causes": {
              "inverter": 12,
              "grid": 20,
              "maintenance": 16
            }
          }
        ]
      }
    },

    "decommissioning": {
      "planned_date": "2062-01-01",
      "strategy": "full_removal|repowering",
      "obligations": {
        "site_restoration": "agricultural_use",
        "financial_security": {
          "type": "bond|letter_of_credit",
          "amount": 5000000,
          "escalation_pct": 2
        }
      },
      "recycling_plan": {
        "modules": {
          "handler": "First_Solar_Recycling",
          "process": "manufacturer_takeback",
          "recovery_rate_pct": 95,
          "materials": ["glass", "semiconductor", "metals"]
        },
        "steel_structures": {
          "handler": "local_scrap_dealer",
          "recovery_rate_pct": 98,
          "revenue_per_ton": 200
        },
        "copper_cables": {
          "handler": "cable_recycler",
          "recovery_rate_pct": 95,
          "revenue_per_ton": 6000
        },
        "concrete": {
          "handler": "local_crusher",
          "reuse": "road_base",
          "recovery_rate_pct": 100
        },
        "electronics": {
          "handler": "certified_ewaste",
          "process": "component_recovery",
          "hazardous_handling": true
        }
      },
      "cost_estimate": {
        "labor": 2000000,
        "equipment": 500000,
        "transport": 800000,
        "disposal": 400000,
        "recycling_revenue": -1200000,
        "site_restoration": 1500000,
        "total_net": 4000000,
        "liabilities": {
          "soil_remediation": {
            "probabilistic_cost": {"mean": 1000000, "std_dev": 200000},
            "triggers": ["bess_leak", "chemical_spill"]
          },
          "total_net_with_liabilities": 5000000
        }
      }
    }
  }
}
```

### 4.2 Environmental Risk Management and Remediation

```json
{
  "operations": {
    "environmental_risk_management": {
      "risk_assessment": {
        "methodology": "ISO_31000_ISO_14001",
        "update_frequency": "annual",
        "risk_register": [
          {
            "risk_id": "ENV_001",
            "category": "chemical_release",
            "source": "bess_electrolyte",
            "probability": "low",
            "impact": "high",
            "risk_score": 12,
            "mitigation": {
              "preventive": [
                "secondary_containment",
                "leak_detection_sensors",
                "regular_inspection"
              ],
              "reactive": [
                "spill_response_kit",
                "hazmat_team_contract",
                "regulatory_notification"
              ]
            },
            "financial_provision": {
              "estimated_cost": 2000000,
              "insurance_coverage": 1500000,
              "self_insurance": 500000
            }
          },
          {
            "risk_id": "ENV_002",
            "category": "fire_smoke",
            "source": "bess_thermal_runaway",
            "probability": "very_low",
            "impact": "very_high",
            "risk_score": 15,
            "mitigation": {
              "preventive": [
                "thermal_monitoring",
                "cell_isolation",
                "suppression_system"
              ],
              "reactive": [
                "fire_department_training",
                "evacuation_plan",
                "air_quality_monitoring"
              ]
            },
            "financial_provision": {
              "estimated_cost": 5000000,
              "insurance_coverage": 4000000,
              "contingency_fund": 1000000
            }
          },
          {
            "risk_id": "ENV_003",
            "category": "soil_contamination",
            "source": "transformer_oil",
            "probability": "low",
            "impact": "medium",
            "risk_score": 8,
            "mitigation": {
              "preventive": [
                "ester_based_oil",
                "bund_wall",
                "oil_monitoring"
              ],
              "reactive": [
                "soil_testing",
                "bioremediation",
                "groundwater_monitoring"
              ]
            },
            "financial_provision": {
              "estimated_cost": 500000,
              "insurance_coverage": 400000,
              "retention": 100000
            }
          },
          {
            "risk_id": "ENV_004",
            "category": "habitat_disruption",
            "source": "construction_operations",
            "probability": "medium",
            "impact": "low",
            "risk_score": 6,
            "mitigation": {
              "preventive": [
                "seasonal_restrictions",
                "wildlife_corridors",
                "noise_barriers"
              ],
              "reactive": [
                "habitat_restoration",
                "species_relocation",
                "compensation_wetlands"
              ]
            },
            "financial_provision": {
              "estimated_cost": 200000,
              "budget_allocation": 200000
            }
          }
        ]
      },

      "contamination_remediation": {
        "soil_remediation": {
          "trigger_levels": {
            "hydrocarbons_ppm": 100,
            "heavy_metals_ppm": 50,
            "pfas_ppb": 70
          },
          "methods": {
            "in_situ": {
              "bioremediation": {
                "cost_per_m3": 150,
                "duration_months": 12,
                "effectiveness_pct": 85
              },
              "chemical_oxidation": {
                "cost_per_m3": 200,
                "duration_months": 6,
                "effectiveness_pct": 95
              },
              "phytoremediation": {
                "cost_per_m3": 50,
                "duration_months": 24,
                "effectiveness_pct": 70
              }
            },
            "ex_situ": {
              "excavation_disposal": {
                "cost_per_m3": 500,
                "duration_months": 1,
                "effectiveness_pct": 100
              },
              "thermal_treatment": {
                "cost_per_m3": 300,
                "duration_months": 3,
                "effectiveness_pct": 98
              }
            }
          }
        },

        "groundwater_remediation": {
          "monitoring_wells": {
            "count": 8,
            "depth_m": 30,
            "sampling_frequency": "quarterly",
            "parameters": [
              "ph", "tds", "hydrocarbons", "metals", "pfas"
            ]
          },
          "treatment_systems": {
            "pump_and_treat": {
              "capacity_lpm": 100,
              "treatment": ["activated_carbon", "air_stripping"],
              "cost_per_year": 150000
            },
            "permeable_reactive_barrier": {
              "length_m": 200,
              "depth_m": 15,
              "media": "zero_valent_iron",
              "replacement_years": 10
            }
          }
        },

        "emergency_response": {
          "spill_response": {
            "notification_timeline_hours": {
              "internal": 0.25,
              "regulatory": 2,
              "public": 24
            },
            "containment_materials": {
              "absorbent_pads_qty": 500,
              "booms_m": 200,
              "neutralizing_agent_kg": 100
            },
            "contractors": [
              {
                "name": "EnviroClean_Inc",
                "response_time_hours": 4,
                "capabilities": ["hazmat", "disposal", "remediation"]
              }
            ]
          }
        }
      },

      "liability_provisions": {
        "financial_assurance": {
          "mechanisms": {
            "environmental_bond": {
              "amount": 5000000,
              "provider": "Surety_Corp",
              "renewal": "annual",
              "cost_pct": 1.5
            },
            "insurance": {
              "pollution_liability": {
                "limit": 25000000,
                "deductible": 100000,
                "premium": 75000
              },
              "environmental_impairment": {
                "limit": 10000000,
                "deductible": 50000,
                "premium": 40000
              }
            },
            "escrow_account": {
              "amount": 2000000,
              "interest_rate_pct": 2.5,
              "release_conditions": "regulatory_approval"
            }
          },

          "cost_escalation": {
            "base_year": 2025,
            "escalation_rate_pct": 3.5,
            "review_frequency_years": 3,
            "adjustment_mechanism": "cpi_plus_1pct"
          }
        },

        "closure_planning": {
          "decommissioning_fund": {
            "target_amount": 8000000,
            "funding_method": "sinking_fund",
            "annual_contribution": 250000,
            "investment_return_pct": 4.5
          },

          "site_restoration": {
            "end_use": "agricultural|recreational|industrial|natural",
            "restoration_standards": {
              "soil_quality": "residential_use",
              "vegetation": "native_species",
              "hydrology": "pre_development"
            },
            "estimated_costs": {
              "earthworks": 1500000,
              "revegetation": 500000,
              "monitoring_5_years": 250000
            }
          }
        }
      }
    }
  }
}
```

---

## PART V: ESG AND SUSTAINABILITY

### 5.1 Environmental, Social, and Governance Metrics

```json
{
  "esg": {
    "environmental": {
      "carbon_footprint": {
        "construction": {
          "embodied_carbon_tco2": 45000,
          "transport_tco2": 3000,
          "construction_tco2": 2000,
          "total_tco2": 50000
        },
        "operational": {
          "avoided_emissions_tco2_year": 125000,
          "grid_emission_factor_kgco2_mwh": 400,
          "lifecycle_avoided_tco2": 4375000
        },
        "payback_time_years": 0.4
      },

      "biodiversity": {
        "baseline_assessment": {
          "date": "2024-06-01",
          "species_count": 45,
          "habitat_types": ["grassland", "wetland_buffer"],
          "threatened_species": 2
        },
        "mitigation_measures": [
          {
            "measure": "pollinator_habitat",
            "area_ha": 5,
            "species_planted": 12
          },
          {
            "measure": "wildlife_corridors",
            "count": 3,
            "width_m": 10
          },
          {
            "measure": "bird_diverters",
            "locations": "transmission_lines"
          }
        ],
        "monitoring": {
          "frequency": "annual",
          "metrics": ["species_diversity", "population_counts", "habitat_quality"],
          "reporting": "public"
        }
      },

      "water_management": {
        "consumption": {
          "construction_m3": 50000,
          "operational_cleaning_m3_year": 2000,
          "source": "municipal|groundwater|recycled"
        },
        "stormwater": {
          "retention_ponds": 3,
          "capacity_m3": 10000,
          "treatment": "natural_filtration",
          "discharge_permit": "NPDES_12345"
        }
      },

      "land_use": {
        "total_area_ha": 200,
        "panel_coverage_ha": 120,
        "dual_use": {
          "type": "agrivoltaics",
          "crop": "grazing",
          "area_ha": 100
        }
      },

      "circular_economy": {
        "design_for_recycling": true,
        "recycled_content_pct": 15,
        "end_of_life_recovery_pct": 95,
        "certifications": ["Cradle_to_Cradle", "ISO_14040"]
      }
    },

    "social": {
      "community_engagement": {
        "public_meetings": 12,
        "stakeholders_engaged": 500,
        "concerns_addressed": [
          "visual_impact",
          "property_values",
          "glare",
          "noise"
        ],
        "benefits_sharing": {
          "community_fund_annual": 50000,
          "local_tax_revenue": 800000,
          "landowner_payments": 450000
        }
      },

      "employment": {
        "construction": {
          "peak_jobs": 500,
          "person_years": 250,
          "local_hire_pct": 60,
          "union_labor_pct": 80
        },
        "operations": {
          "permanent_jobs": 12,
          "indirect_jobs": 36,
          "training_programs": ["solar_technician", "electrical", "operations"]
        },
        "diversity": {
          "women_pct": 25,
          "minorities_pct": 40,
          "veterans_pct": 15
        }
      },

      "health_safety": {
        "safety_record": {
          "ltir": 0.5,
          "trir": 1.2,
          "fatalities": 0,
          "near_misses": 15
        },
        "certifications": ["ISO_45001", "OHSAS_18001"],
        "training_hours_per_person": 40,
        "emergency_response_plan": true
      },

      "supply_chain": {
        "responsible_sourcing": {
          "policy": true,
          "audits": "annual",
          "traceability": "blockchain"
        },
        "human_rights": {
          "forced_labor_screening": true,
          "conflict_minerals": "free",
          "living_wage": true
        }
      }
    },

    "governance": {
      "ownership_structure": {
        "sponsor": {"name": "RenewCo", "stake_pct": 51},
        "financial_partner": {"name": "GreenFund", "stake_pct": 30},
        "tax_equity": {"name": "BankCorp", "stake_pct": 19}
      },

      "board_composition": {
        "independent_directors_pct": 60,
        "diversity_pct": 40,
        "expertise": ["renewable_energy", "finance", "engineering", "esg"]
      },

      "compliance": {
        "anti_corruption": {
          "policy": true,
          "training": "annual",
          "whistleblower_hotline": true
        },
        "data_privacy": {
          "gdpr_compliant": true,
          "cybersecurity": "ISO_27001"
        },
        "reporting": {
          "financial": "quarterly",
          "sustainability": "annual",
          "standards": ["GRI", "SASB", "TCFD"]
        }
      },

      "risk_management": {
        "framework": "ISO_31000",
        "climate_risk_assessment": true,
        "insurance_coverage": {
          "property": "full_replacement",
          "liability": 100000000,
          "environmental": 50000000,
          "cyber": 25000000
        }
      }
    },

    "certifications": {
      "project": ["LEED_Gold", "Envision_Platinum"],
      "products": ["UL_Listed", "IEC_Certified"],
      "management": ["ISO_9001", "ISO_14001", "ISO_45001"],
      "sustainability": ["B_Corp", "RE100"]
    },

    "reporting": {
      "frameworks": ["GRI", "SASB", "TCFD", "CDP"],
      "verification": "third_party",
      "frequency": "annual",
      "transparency": "public"
    }
  }
}
```

### 5.2 Cybersecurity and Digital Resilience

```json
{
  "esg": {
    "governance": {
      "cybersecurity": {
        "framework": "NIST_CSF_2.0",
        "maturity_level": 3,

        "scada_security": {
          "architecture": {
            "zones": [
              {
                "level": 0,
                "name": "enterprise",
                "systems": ["email", "erp", "web"],
                "security_level": "standard"
              },
              {
                "level": 1,
                "name": "dmz",
                "systems": ["historian", "hmi_view_only"],
                "security_level": "enhanced"
              },
              {
                "level": 2,
                "name": "control",
                "systems": ["scada_servers", "hmi_control"],
                "security_level": "critical"
              },
              {
                "level": 3,
                "name": "field",
                "systems": ["plc", "rtu", "ied"],
                "security_level": "critical"
              }
            ],

            "segmentation": {
              "firewalls": {
                "between_zones": true,
                "rules": "deny_all_allow_specific",
                "deep_packet_inspection": true
              },
              "data_diodes": {
                "level_2_to_1": true,
                "unidirectional": true
              },
              "air_gaps": {
                "safety_systems": true,
                "backup_control": true
              }
            }
          },

          "vulnerabilities": {
            "assessment_frequency": "quarterly",
            "penetration_testing": "annual",
            "identified_risks": [
              {
                "cve": "CVE-2024-3400",
                "system": "firewall",
                "severity": "critical",
                "cvss_score": 9.8,
                "mitigation": "patch_applied",
                "status": "resolved"
              },
              {
                "cve": "CVE-2024-21762",
                "system": "web_portal",
                "severity": "high",
                "cvss_score": 8.1,
                "mitigation": "workaround",
                "status": "monitoring"
              }
            ],

            "patch_management": {
              "testing_environment": true,
              "patch_window": "monthly",
              "emergency_patches_sla_hours": 48,
              "rollback_plan": true
            }
          },

          "incident_response": {
            "team": {
              "internal": ["ciso", "it_manager", "scada_engineer"],
              "external": ["forensics_firm", "legal_counsel"],
              "escalation": "defined"
            },

            "playbooks": {
              "ransomware": {
                "detection_time_target_min": 15,
                "isolation_time_target_min": 5,
                "recovery_time_target_hours": 24,
                "backup_restoration_tested": "monthly"
              },
              "supply_chain": {
                "vendor_compromise_procedure": true,
                "software_rollback": true,
                "alternate_suppliers": true
              },
              "physical_cyber": {
                "coordinated_attack_response": true,
                "manual_override_procedures": true,
                "safety_system_independence": true
              }
            },

            "forensics": {
              "log_retention_days": 365,
              "siem_platform": "splunk",
              "threat_intelligence_feeds": 5,
              "behavioral_analytics": true
            }
          },

          "access_control": {
            "authentication": {
              "multi_factor": "mandatory",
              "privileged_access_management": true,
              "session_timeout_minutes": 15,
              "password_policy": "nist_800_63b"
            },

            "authorization": {
              "role_based_access": true,
              "principle_of_least_privilege": true,
              "regular_review_months": 3,
              "automated_deprovisioning": true
            },

            "remote_access": {
              "vpn_required": true,
              "jump_server": true,
              "session_recording": true,
              "vendor_access_approval": "per_session"
            }
          },

          "supply_chain_security": {
            "software_bill_of_materials": true,
            "vendor_assessment": {
              "security_questionnaire": true,
              "audit_rights": true,
              "incident_notification_hours": 24
            },
            "code_signing": {
              "firmware_verification": true,
              "configuration_integrity": true,
              "secure_boot": true
            }
          },

          "resilience_measures": {
            "backup_systems": {
              "frequency": "daily",
              "offsite_storage": true,
              "air_gapped_copy": true,
              "restoration_tested": "quarterly"
            },

            "redundancy": {
              "control_systems": "n_plus_1",
              "communication_paths": "dual",
              "power_supplies": "redundant"
            },

            "business_continuity": {
              "rto_hours": 4,
              "rpo_hours": 1,
              "alternate_control_room": true,
              "crisis_communication_plan": true
            }
          }
        },

        "compliance_standards": {
          "nerc_cip": {
            "applicable": true,
            "version": "CIP-013-2",
            "audit_frequency": "triennial",
            "last_audit": "2024-06-15",
            "findings": 0
          },
          "iec_62443": {
            "security_level": 3,
            "zones_conduits_defined": true,
            "risk_assessment_complete": true
          },
          "iso_27001": {
            "certified": true,
            "certificate_number": "IS-12345",
            "expiry": "2026-12-31",
            "surveillance_audits": "annual"
          }
        },

        "metrics_kpis": {
          "mean_time_to_detect_hours": 2,
          "mean_time_to_respond_hours": 1,
          "security_incidents_per_year": 3,
          "successful_attacks": 0,
          "training_completion_rate_pct": 98,
          "phishing_click_rate_pct": 2
        }
      }
    }
  }
}
```

---

## PART VI: EXTERNAL MODEL INTEGRATION

### 6.1 Interoperability Mappings

```json
{
  "external_models": {
    "ifc_integration": {
      "version": "IFC4.3",
      "file": "s3://models/plant_layout.ifc",
      "mappings": [
        {
          "odl_element": "surfaces.roof_A",
          "ifc_entity": "IfcRoof",
          "guid": "2O2Fr$t4X7Zf8NOew3FLOH"
        },
        {
          "odl_element": "instances.tracker_row_1",
          "ifc_entity": "IfcBuildingElementProxy",
          "guid": "3Sa9r$t4X7Zf8NOew3FLKM"
        }
      ],
      "coordinate_transformation": {
        "origin_offset": [100000, 500000, 100],
        "rotation_deg": 0,
        "scale": 1.0
      }
    },

    "cim_integration": {
      "version": "CIM17",
      "namespace": "http://iec.ch/TC57/2020/CIM-schema-cim17",
      "mappings": [
        {
          "odl_element": "instances.main_transformer",
          "cim_class": "PowerTransformer",
          "mrid": "1234567890abcdef"
        },
        {
          "odl_element": "instances.poi",
          "cim_class": "ConnectivityNode",
          "mrid": "fedcba0987654321"
        }
      ],
      "grid_model": {
        "file": "s3://models/grid_model.xml",
        "format": "CGMES",
        "tso": "CAISO"
      }
    },

    "weather_data": {
      "tmy_data": {
        "format": "TMY3",
        "source": "NREL_NSRDB",
        "station": {
          "id": "724666",
          "name": "San_Francisco_Intl",
          "distance_km": 45,
          "elevation_diff_m": 20
        },
        "parameters": [
          "ghi", "dni", "dhi",
          "ambient_temperature",
          "wind_speed", "wind_direction"
        ],
        "file": "s3://weather/724666TYA.csv"
      },

      "satellite_data": {
        "provider": "SolarAnywhere",
        "resolution_km": 1,
        "time_resolution_min": 5,
        "historical_years": 20,
        "api_endpoint": "https://api.solaranywhere.com/v2",
        "coordinates": {
          "latitude": 37.7749,
          "longitude": -122.4194
        }
      },

      "forecasting": {
        "provider": "DNV",
        "horizons": ["hour_ahead", "day_ahead", "week_ahead"],
        "update_frequency_hours": 1,
        "accuracy_metrics": {
          "rmse_pct": 8,
          "mae_pct": 6,
          "bias_pct": 0.5
        }
      }
    },

    "simulation_tools": {
      "pvsyst": {
        "version": "7.4",
        "project_file": "s3://simulations/project.PRJ",
        "meteo_file": "s3://simulations/meteo.MET",
        "last_run": "2025-08-15",
        "results": {
          "pr": 0.845,
          "specific_yield": 1755,
          "loss_diagram": "s3://simulations/losses.pdf"
        }
      },

      "pscad": {
        "version": "5.0",
        "model": "s3://simulations/grid_integration.pscx",
        "studies": ["load_flow", "short_circuit", "transient_stability"],
        "compliance": ["IEEE_1547", "NERC_PRC_024"]
      },

      "helioscope": {
        "design_id": "abc123",
        "api_key": "encrypted",
        "shade_analysis": true,
        "energy_model": "8760_hourly"
      }
    }
  }
}
```

---

## PART VII: ADVANCED EXAMPLES

### 7.1 Multi-Jurisdiction Compliance Example

```json
{
  "compliance": {
    "jurisdictions": [
      {
        "level": "federal",
        "country": "USA",
        "authority": "FERC",
        "standards": ["NERC_Reliability", "PURPA"],
        "requirements": [
          {
            "id": "NERC_PRC_024",
            "description": "Generator frequency and voltage protective settings",
            "status": "compliant",
            "evidence": {
              "test_date": "2026-11-15",
              "test_report": "s3://compliance/nerc_prc024_test.pdf",
              "settings": {
                "over_frequency": 61.8,
                "under_frequency": 57.0,
                "over_voltage": 1.2,
                "under_voltage": 0.5
              }
            }
          }
        ]
      },
      {
        "level": "state",
        "state": "California",
        "authority": "CPUC",
        "standards": ["Rule_21", "Title_24"],
        "requirements": [
          {
            "id": "Rule_21_Smart_Inverter",
            "description": "Autonomous grid support functions",
            "status": "compliant",
            "evidence": {
              "functions_enabled": [
                "volt_var",
                "volt_watt",
                "freq_watt",
                "ramp_rate"
              ],
              "certification": "UL_1741_SA"
            }
          }
        ]
      },
      {
        "level": "local",
        "jurisdiction": "San_Bernardino_County",
        "authority": "Building_Department",
        "permit": "BLD-2025-12345",
        "requirements": [
          {
            "id": "setback_requirements",
            "description": "Minimum setback from property lines",
            "status": "compliant",
            "evidence": {
              "north_setback_m": 15,
              "south_setback_m": 15,
              "east_setback_m": 20,
              "west_setback_m": 20,
              "survey_drawing": "s3://permits/survey.pdf"
            }
          }
        ]
      },
      {
        "level": "utility",
        "utility": "Southern_California_Edison",
        "interconnection_agreement": "LGIA-2025-67890",
        "requirements": [
          {
            "id": "reactive_power_capability",
            "description": "Power factor range at POI",
            "status": "compliant",
            "evidence": {
              "tested_range": [0.85, 1.0, 0.85],
              "test_date": "2026-11-20",
              "witnessed_by": "SCE_Engineer"
            }
          }
        ]
      }
    ],

    "integrated_compliance_matrix": {
      "voltage_limits": {
        "federal": {"min_pu": 0.88, "max_pu": 1.10},
        "state": {"min_pu": 0.88, "max_pu": 1.10},
        "utility": {"min_pu": 0.90, "max_pu": 1.05},
        "applied": {"min_pu": 0.90, "max_pu": 1.05}
      },
      "frequency_limits": {
        "federal": {"min_hz": 57.0, "max_hz": 61.8},
        "state": {"min_hz": 57.0, "max_hz": 61.8},
        "utility": {"min_hz": 57.5, "max_hz": 61.5},
        "applied": {"min_hz": 57.5, "max_hz": 61.5}
      }
    },

    "standards_summaries": {
      "IEEE_1547": {
        "key_clauses": [
          {"clause": "4.1.1", "summary": "Interconnection system response to abnormal voltages: Must ride through dips to 0.5 pu for 0.16-21 seconds."}
        ]
      }
    }
  }
}
```

### 7.2 Advanced Grid Study Results

```json
{
  "analysis": [
    {
      "id": "grid_impact_study",
      "type": "interconnection_study",
      "tool": {
        "name": "PSS/E",
        "version": "35.3"
      },
      "timestamp": "2025-06-15T10:00:00Z",
      "design_version": "v2.1",

      "inputs": {
        "grid_model": "WECC_2025_Heavy_Summer",
        "plant_model": {
          "capacity_mw": 150,
          "power_factor_range": [0.85, 0.85],
          "voltage_control": "enabled"
        },
        "contingencies": [
          "N-1",
          "N-1-1",
          "critical_3_phase_fault"
        ]
      },

      "outputs": {
        "steady_state": {
          "power_flow": {
            "pre_project": {
              "line_loadings": {
                "max_loading_pct": 75,
                "critical_line": "Valley-Mesa_230kV"
              },
              "voltage_profile": {
                "min_pu": 0.98,
                "max_pu": 1.02
              }
            },
            "post_project": {
              "line_loadings": {
                "max_loading_pct": 82,
                "critical_line": "Valley-Mesa_230kV"
              },
              "voltage_profile": {
                "min_pu": 0.99,
                "max_pu": 1.03
              },
              "power_losses_mw": 2.3
            }
          },

          "short_circuit": {
            "poi_fault_current": {
              "three_phase_ka": 12.5,
              "single_phase_ka": 10.2
            },
            "breaker_duty": {
              "interrupting_ka": 40,
              "margin_pct": 68
            }
          },

          "contingency_analysis": {
            "violations": [
              {
                "contingency": "Valley-Mesa_230kV_outage",
                "element": "Valley-Riverside_230kV",
                "loading_pct": 105,
                "mitigation": "generation_redispatch"
              }
            ]
          }
        },

        "dynamic_stability": {
          "fault_ride_through": {
            "test_cases": [
              {
                "fault": "3ph_POI",
                "duration_ms": 150,
                "retained_voltage_pu": 0,
                "result": "stable",
                "recovery_time_ms": 1500
              },
              {
                "fault": "1ph_remote",
                "duration_ms": 500,
                "retained_voltage_pu": 0.5,
                "result": "stable",
                "recovery_time_ms": 800
              }
            ]
          },

          "frequency_response": {
            "events": [
              {
                "event": "largest_unit_trip",
                "frequency_nadir_hz": 59.7,
                "plant_response_mw": 5,
                "response_time_ms": 500
              }
            ]
          },

          "small_signal_stability": {
            "eigenvalues": [
              {"real": -0.5, "imag": 3.2, "damping_ratio": 0.156},
              {"real": -0.3, "imag": 8.5, "damping_ratio": 0.035}
            ],
            "critical_mode": "inter_area_oscillation",
            "damping_adequate": true
          }
        },

        "mitigation_required": {
          "transmission_upgrades": [],
          "reactive_compensation": {
            "type": "STATCOM",
            "rating_mvar": 50,
            "location": "POI",
            "cost_estimate": 5000000
          },
          "special_protection_scheme": false
        }
      },

      "approval": {
        "status": "approved_with_conditions",
        "conditions": [
          "Install 50 MVAR STATCOM",
          "Implement voltage control coordination",
          "Participate in AGC"
        ],
        "approved_by": "ISO_Planning_Engineer",
        "date": "2025-07-01"
      }
    }
  ]
}
```

---

## APPENDIX A: Complete Working Example

```json
{
  "$schema": "https://odl-sd.org/schemas/v4.1/document.json",
  "schema_version": "4.1",

  "meta": {
    "project": "Desert_Solar_150MW",
    "domain": "HYBRID",
    "scale": "UTILITY",
    "created_at": "2025-08-30T10:00:00Z"
  },

  "hierarchy": {
    "type": "PLANT",
    "id": "PLANT_001",
    "portfolio": {
      "id": "PORTFOLIO_AMERICAS_2025",
      "name": "Americas Renewable Portfolio"
    }
  },

  "instances": [
    {
      "id": "PV_STRING_001",
      "type_ref": "pv_module",
      "parent_ref": "ARRAY_001",
      "location": {
        "lat": 35.2827,
        "lon": -116.0544,
        "elevation_m": 620
      },
      "lifecycle_status": "operational",
      "commission_date": "2026-12-01",
      "serial_numbers": ["LON570M001", "LON570M002"],
      "warranty_expiry": "2038-12-01"
    },
    {
      "id": "BESS_RACK_001",
      "type_ref": "bess_rack",
      "parent_ref": "BESS_CONTAINER_001",
      "location": {
        "lat": 35.2830,
        "lon": -116.0540,
        "elevation_m": 620
      },
      "lifecycle_status": "commissioned",
      "commission_date": "2026-11-15",
      "digital_twin": {
        "model_url": "https://dt.example.com/models/bess_rack_001",
        "last_sync": "2025-08-30T09:00:00Z",
        "sync_frequency_hours": 24
      }
    }
  ],

  "connections": [
    {
      "id": "DC_CONN_001",
      "from": {
        "instance_id": "PV_STRING_001",
        "port_id": "dc_positive"
      },
      "to": {
        "instance_id": "COMBINER_001",
        "port_id": "input_1_pos"
      },
      "kind": "dc_power",
      "attributes": {
        "cable_type": "PV1-F_6mm2",
        "length_m": 12.5,
        "resistance_ohm": 0.003,
        "validated": true,
        "validation_timestamp": "2026-11-10T14:30:00Z"
      }
    },
    {
      "id": "DATA_CONN_001",
      "from": {
        "instance_id": "BESS_RACK_001",
        "port_id": "bms_can"
      },
      "to": {
        "instance_id": "PCS_001",
        "port_id": "bms_interface"
      },
      "kind": "data_can",
      "attributes": {
        "cable_type": "CAN_BUS_TWISTED_PAIR",
        "length_m": 5,
        "termination_resistance_ohm": 120,
        "shielded": true
      }
    }
  ],

  "analysis": [
    {
      "id": "CAPACITY_TEST_001",
      "type": "performance_test",
      "timestamp": "2026-12-15T12:00:00Z",
      "inputs": {
        "irradiance_w_m2": 850,
        "module_temp_c": 45,
        "ambient_temp_c": 25
      },
      "outputs": {
        "measured_capacity_mw": 127.5,
        "expected_capacity_mw": 128.2,
        "performance_ratio": 0.842,
        "test_passed": true
      }
    }
  ]
}
```

---

## APPENDIX B: Glossary of Terms

```json
{
  "glossary": {
    "technical_terms": {
      "AGC": "Automatic Generation Control - System for adjusting power output",
      "BESS": "Battery Energy Storage System",
      "CIM": "Common Information Model - Electric utility standard",
      "DSCR": "Debt Service Coverage Ratio - Cash flow to debt payment ratio",
      "GCR": "Ground Coverage Ratio - Ratio of module area to land area",
      "IFC": "Industry Foundation Classes - Building information modeling standard",
      "LCOE": "Levelized Cost of Energy - Average cost per unit energy",
      "LID": "Light-Induced Degradation - Initial power loss in PV modules",
      "LLCR": "Loan Life Coverage Ratio - NPV of cash flows to outstanding debt",
      "LVRT": "Low Voltage Ride Through - Grid fault survival capability",
      "MACRS": "Modified Accelerated Cost Recovery System - US tax depreciation",
      "NERC": "North American Electric Reliability Corporation",
      "NOCT": "Nominal Operating Cell Temperature",
      "NPV": "Net Present Value - Present value of cash flows",
      "O&M": "Operations and Maintenance",
      "PID": "Potential-Induced Degradation - Voltage-stress degradation",
      "POI": "Point of Interconnection - Grid connection point",
      "PPA": "Power Purchase Agreement",
      "PR": "Performance Ratio - Actual to theoretical energy ratio",
      "ROCOF": "Rate of Change of Frequency",
      "SCADA": "Supervisory Control and Data Acquisition",
      "STC": "Standard Test Conditions - 1000W/m², 25°C, AM1.5",
      "TMY": "Typical Meteorological Year"
    },

    "financial_terms": {
      "BASIS_POINT": "0.01% - Used in interest rate discussions",
      "CAPEX": "Capital Expenditure - Initial investment costs",
      "IDC": "Interest During Construction",
      "IRR": "Internal Rate of Return - Discount rate where NPV=0",
      "ITC": "Investment Tax Credit",
      "MIRR": "Modified Internal Rate of Return",
      "OPEX": "Operating Expenditure - Ongoing costs",
      "P50/P90": "Probability exceedance values - 50%/90% probability",
      "PTC": "Production Tax Credit",
      "REC": "Renewable Energy Certificate",
      "WACC": "Weighted Average Cost of Capital"
    },

    "standards_organizations": {
      "ANSI": "American National Standards Institute",
      "ASTM": "American Society for Testing and Materials",
      "IEC": "International Electrotechnical Commission",
      "IEEE": "Institute of Electrical and Electronics Engineers",
      "ISO": "International Organization for Standardization",
      "UL": "Underwriters Laboratories"
    }
  }
}
```

---

## CONCLUSION

This ODL-SD Technical Specification v4.1 provides a truly comprehensive framework for representing renewable energy systems throughout their complete lifecycle. The specification now includes all enhancements from version 4.0 plus:

**Version 4.1 Key Enhancements:**

1. **Formal JSON Schema Validation** - Complete schema definitions with validation rules for automated implementation and error-free parsing

2. **Complete PV Component Library** - Detailed photovoltaic module specifications with comprehensive degradation models matching BESS detail, including LID, PID, and multi-factor degradation mechanisms

3. **Climate-Specific Financial Modeling** - Regional adjustments for four climate zones with dynamic loss calculations and mitigation strategies

4. **Environmental Risk Management** - Comprehensive contamination remediation frameworks, liability provisions, and emergency response protocols

5. **Enhanced Cybersecurity Framework** - Complete SCADA security architecture with NERC CIP and IEC 62443 compliance

6. **Data Management Strategies** - Scalability solutions for deployments exceeding 10,000 instances with partitioning, compression, and streaming support

7. **Implementation Guidance** - Working examples, comprehensive glossary, and standards summaries for improved clarity

The specification maintains its core principle of being a **portable, self-contained design document** while providing enhanced depth for:
- Bankable project finance with Monte Carlo risk analysis
- Utility-scale deployment with multi-GW portfolio support
- Multi-stakeholder governance with digital signatures
- 35+ year asset lifecycle management with decommissioning planning
- Regulatory compliance across jurisdictions with evidence tracking
- ESG reporting and sustainability tracking with third-party verification
- Climate-specific optimizations for global deployments
- Cybersecurity resilience for critical infrastructure protection

This v4.1 document serves as the definitive technical foundation for implementing solar PV and energy storage lifecycle management platforms without requiring external documentation. The specification supports the complete value chain from initial design through end-of-life recycling, enabling standardized data exchange between all stakeholders in the renewable energy ecosystem.
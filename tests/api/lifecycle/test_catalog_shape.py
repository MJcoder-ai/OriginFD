import re

from services.api.domain.lifecycle_catalog import LIFECYCLE_CATALOG


def test_catalog_has_expected_length_and_codes():
    assert len(LIFECYCLE_CATALOG) == 12

    phase_codes = [spec.phase_code for spec in LIFECYCLE_CATALOG]
    assert phase_codes == list(range(12)), "Phase codes must be contiguous from 0 to 11"


def test_catalog_gate_codes_and_roles_are_defined():
    gate_pattern = re.compile(r"^G\d{1,2}$")

    for spec in LIFECYCLE_CATALOG:
        assert spec.required_entry_roles, f"Phase {spec.phase_code} must declare entry roles"
        assert spec.required_exit_roles, f"Phase {spec.phase_code} must declare exit roles"
        assert spec.odl_sd_sections, f"Phase {spec.phase_code} must map to ODL-SD sections"
        assert gate_pattern.match(spec.entry_gate_code), "Entry gate codes must follow G# pattern"
        assert gate_pattern.match(spec.exit_gate_code), "Exit gate codes must follow G# pattern"


def test_catalog_gate_snapshot():
    snapshot = [
        (spec.phase_code, spec.phase_key, spec.entry_gate_code, spec.exit_gate_code)
        for spec in LIFECYCLE_CATALOG
    ]
    assert snapshot == [
        (0, "phase.discovery", "G0", "G1"),
        (1, "phase.concept_feasibility", "G1", "G2"),
        (2, "phase.requirements_scope", "G2", "G3"),
        (3, "phase.preliminary_design", "G3", "G4"),
        (4, "phase.detailed_design", "G4", "G5"),
        (5, "phase.procurement_planning", "G5", "G6"),
        (6, "phase.supplier_selection", "G6", "G7"),
        (7, "phase.construction_installation", "G7", "G8"),
        (8, "phase.qa_precommission", "G8", "G9"),
        (9, "phase.commissioning_handover", "G9", "G10"),
        (10, "phase.operations_optimization", "G10", "G11"),
        (11, "phase.closeout", "G11", "G12"),
    ]

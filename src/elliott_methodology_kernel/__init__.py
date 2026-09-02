"""Public surface for the Phase 1 Methodology Kernel contract."""

from .api import MethodologyKernel
from .brain import BrainIntegrityError, BrainManifest, load_brain_manifest
from .contracts import (
    AnalysisRequest,
    AnalysisResultEnvelope,
    AnalyzedWaveSubject,
    CertifiedStructuralInvalidity,
    CertifiedValidatedInternalFamily,
    InternalFamilyKind,
    InternalFamilyValidatorResult,
    KernelStatus,
    NormalImpulseFiveSlotCandidateView,
    NormalImpulseFiveSlotCardinalityError,
    OrderedChildBinding,
    StructuralInvalidityCertificationError,
    StructuralValidatorResult,
    SubjectBoundObservedPriceEndpointPair,
    SubjectBoundObservedPriceObservation,
    ValidatedInternalFamilyCertificationError,
    certify_validated_internal_family,
    certify_structural_invalidity,
)
from .degree_peer_consistency import (
    DegreePeerCheckStatus,
    DegreePeerConsistencyInput,
    DegreePeerConsistencyResult,
    DegreePeerExecutionRole,
    check_degree_peer_consistency,
)
from .p004 import (
    CandidateScope,
    ExecutionRole,
    ImpulseDirection,
    P004Input,
    P004Result,
    RuleCheckStatus,
    check_p004,
)
from .p023_visibility_guard import (
    P023VisibilityCheckStatus,
    P023VisibilityExecutionRole,
    P023VisibilityInput,
    P023VisibilityResult,
    P023VisibilityState,
    check_p023_visibility_guard,
)
from .parent_child_degree_adjacency import (
    ParentChildDegreeCheckStatus,
    ParentChildDegreeExecutionRole,
    ParentChildDegreeInput,
    ParentChildDegreeResult,
    check_parent_child_degree_adjacency,
)
from .p007_single_zigzag_cardinality import (
    P007CandidateScope,
    P007CardinalityStatus,
    P007ExecutionRole,
    P007SingleZigzagCardinalityInput,
    P007SingleZigzagCardinalityResult,
    check_p007_single_zigzag_cardinality,
)
from ._structural_invalidity_certification import (
    _seal_structural_validator_registry,
)
from ._validated_internal_family_certification import (
    _seal_internal_family_validator_registry,
)


_seal_structural_validator_registry(
    expected_result_types=(
        P004Result,
        DegreePeerConsistencyResult,
        ParentChildDegreeResult,
        P007SingleZigzagCardinalityResult,
    )
)
del _seal_structural_validator_registry

_seal_internal_family_validator_registry(expected_result_types=())
del _seal_internal_family_validator_registry

from .structural_invalidity_evidence_no_rescue import (
    StructuralInvalidityEvidenceNoRescueExecutionRole,
    StructuralInvalidityEvidenceNoRescuePolicyStatus,
    StructuralInvalidityEvidenceNoRescueResult,
    apply_structural_invalidity_evidence_no_rescue,
)
from .p003_one_larger_degree_theme import (
    P003ExecutionRole,
    P003OneLargerDegreeRelation,
    P003OneLargerDegreeThemeInput,
    P003OneLargerDegreeThemeResult,
    P003SearchTheme,
    P003ThemeMappingStatus,
    map_p003_one_larger_degree_theme,
)

__all__ = [
    "AnalysisRequest",
    "AnalysisResultEnvelope",
    "AnalyzedWaveSubject",
    "BrainIntegrityError",
    "BrainManifest",
    "CandidateScope",
    "CertifiedStructuralInvalidity",
    "CertifiedValidatedInternalFamily",
    "DegreePeerCheckStatus",
    "DegreePeerConsistencyInput",
    "DegreePeerConsistencyResult",
    "DegreePeerExecutionRole",
    "ExecutionRole",
    "ImpulseDirection",
    "InternalFamilyKind",
    "InternalFamilyValidatorResult",
    "KernelStatus",
    "MethodologyKernel",
    "NormalImpulseFiveSlotCandidateView",
    "NormalImpulseFiveSlotCardinalityError",
    "OrderedChildBinding",
    "P003ExecutionRole",
    "P003OneLargerDegreeRelation",
    "P003OneLargerDegreeThemeInput",
    "P003OneLargerDegreeThemeResult",
    "P003SearchTheme",
    "P003ThemeMappingStatus",
    "P004Input",
    "P004Result",
    "P007CandidateScope",
    "P007CardinalityStatus",
    "P007ExecutionRole",
    "P007SingleZigzagCardinalityInput",
    "P007SingleZigzagCardinalityResult",
    "P023VisibilityCheckStatus",
    "P023VisibilityExecutionRole",
    "P023VisibilityInput",
    "P023VisibilityResult",
    "P023VisibilityState",
    "ParentChildDegreeCheckStatus",
    "ParentChildDegreeExecutionRole",
    "ParentChildDegreeInput",
    "ParentChildDegreeResult",
    "RuleCheckStatus",
    "StructuralInvalidityCertificationError",
    "StructuralInvalidityEvidenceNoRescueExecutionRole",
    "StructuralInvalidityEvidenceNoRescuePolicyStatus",
    "StructuralInvalidityEvidenceNoRescueResult",
    "StructuralValidatorResult",
    "SubjectBoundObservedPriceEndpointPair",
    "SubjectBoundObservedPriceObservation",
    "ValidatedInternalFamilyCertificationError",
    "apply_structural_invalidity_evidence_no_rescue",
    "check_degree_peer_consistency",
    "check_p023_visibility_guard",
    "check_parent_child_degree_adjacency",
    "check_p004",
    "check_p007_single_zigzag_cardinality",
    "certify_structural_invalidity",
    "certify_validated_internal_family",
    "load_brain_manifest",
    "map_p003_one_larger_degree_theme",
]

# PRS Metric v1 Specification

**Placement Readiness Score**

## Formula

PRS = (0.4 × Visibility) + (0.3 × Stability) + (0.2 × Quality) + (0.1 × Context)

Where:
- **Visibility**: Surface visibility score (0-100)
- **Stability**: Tracking stability across frames (0-100)  
- **Quality**: Technical quality metrics (0-100)
- **Context**: Contextual appropriateness (0-100)

## Thresholds

- PRS ≥ 85: Excellent placement opportunity
- PRS 70-85: Good placement opportunity
- PRS < 70: Poor placement opportunity (reject)

## Calibration

TODO: Define human MOS panel procedures for metric validation.
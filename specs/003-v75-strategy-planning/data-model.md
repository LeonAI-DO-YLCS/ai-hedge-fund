# Data Model: V75 Strategy Planning Docs

## Overview

This feature is documentation-only. Its data model describes the planning artifacts and conceptual entities that the documents must define consistently.

## Entities

### PlanningIndex

**Purpose**: Represents the entry document for the detector planning package.

**Fields**:
- `document_path` - Path to the planning index file
- `document_title` - Human-readable title
- `listed_documents` - Named references to the PRD and roadmap
- `purpose_summary` - Short explanation of what each listed document provides

**Validation rules**:
- Must list every required planning document in the package
- Must explain the role of each listed document clearly

**Relationships**:
- One `PlanningIndex` references one `StrategyResearchPRD`
- One `PlanningIndex` references one `StrategyResearchRoadmap`

### StrategyResearchPRD

**Purpose**: Represents the primary decision document for the next V75 strategy-research phase.

**Fields**:
- `document_path` - Path to the PRD file
- `problem_statement` - Why the next research phase is needed
- `vision` - Desired product or research outcome
- `goals` - Primary and secondary goals
- `non_goals` - Explicit exclusions
- `scope_constraints` - Detector-only and repo-boundary controls
- `strategy_families` - Named candidate families to research
- `validation_model` - Required validation framework summary
- `success_measures` - Decision-quality and robustness-oriented outcomes

**Validation rules**:
- Must include both goals and non-goals
- Must include explicit scope boundaries
- Must explain how current detector findings inform the next phase

**Relationships**:
- One `StrategyResearchPRD` informs one `StrategyResearchRoadmap`

### StrategyResearchRoadmap

**Purpose**: Represents the phased execution document for the future detector strategy-research work.

**Fields**:
- `document_path` - Path to the roadmap file
- `phase_list` - Ordered phases of delivery
- `phase_outcomes` - Intended result of each phase
- `exit_gates` - Conditions required before moving to the next phase
- `milestones` - Major decision checkpoints
- `risks` - Delivery or research risks and mitigations

**Validation rules**:
- Phases must be ordered logically
- Every phase must define an outcome and an exit gate
- Milestones must align with the PRD validation model

**Relationships**:
- One `StrategyResearchRoadmap` operationalizes one `StrategyResearchPRD`

### StrategyFamily

**Purpose**: Represents a named class of candidate trading logic described in the planning package.

**Fields**:
- `family_name` - Name of the candidate family
- `research_objective` - What behavior it aims to test
- `filters` - High-level conditional filters or context requirements
- `rationale` - Why it belongs in the research shortlist

**Validation rules**:
- Must be described in plain language
- Must align with the PRD's conditional research hypothesis

**Relationships**:
- Many `StrategyFamily` records may be described by one `StrategyResearchPRD`

### ValidationGate

**Purpose**: Represents a named decision checkpoint described in the planning package.

**Fields**:
- `gate_name` - Name of the checkpoint
- `phase_name` - Roadmap phase where it applies
- `required_evidence` - What evidence must exist
- `decision_outcome` - What decision the gate supports

**Validation rules**:
- Must be clearly tied to a roadmap phase
- Must define a visible decision consequence

**Relationships**:
- Many `ValidationGate` records belong to one `StrategyResearchRoadmap`

## Relationship Summary

- `PlanningIndex` -> references -> `StrategyResearchPRD`
- `PlanningIndex` -> references -> `StrategyResearchRoadmap`
- `StrategyResearchPRD` -> describes -> many `StrategyFamily`
- `StrategyResearchRoadmap` -> includes -> many `ValidationGate`
- `StrategyResearchRoadmap` -> operationalizes -> `StrategyResearchPRD`

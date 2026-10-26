# Requirements: REA Feature Discovery

## Introduction

This feature provides a reusable process for studying a selected capability in an existing application through REA and turning the findings into a Starwave specification for another application. The process covers investigation, evidence, and planning; each destination application owns its resulting product requirements and implementation. This repository owns the reusable workflow and MCP integration.

**Status:** implementation authorised by the user's instruction to create the skill on 2026-10-26.

## Non-Goals

- Implementing the destination application's feature in this repository.
- A Libre-specific MCP server, glucose adapter, or other app-specific integration.
- Automatically cloning an entire application or treating recovered code as the destination design.
- Adding a second specification lifecycle alongside Starwave.
- Building a hosted analysis service, device extraction utility, or replacement analysis engine.
- Claiming access to an installed mobile app when the required artifact or runtime connection is unavailable.

## Requirements

### 1. Reusable Investigation Entry Point

**User Story:** As a developer, I want to investigate a feature in an existing app, so that I can understand the behaviour I want to bring into my own app.

**Acceptance Criteria:**

1. <a name="1.1"></a>WHEN a developer supplies a source app, a feature or investigation question, and a destination repository, the workflow SHALL start a focused investigation without requiring an app-specific workflow.  
2. <a name="1.2"></a>IF the requested behaviour or destination is unspecified, THEN the workflow SHALL resolve that missing input before creating product requirements, while allowing prerequisite checks and source research to proceed.  
3. <a name="1.3"></a>WHEN the destination already has a spec covering the requested capability, the workflow SHALL identify that spec and its current stage before proposing another spec.  

### 2. REA Access and Readiness

**User Story:** As a developer, I want to know what the available tools can inspect, so that missing access is addressed without inventing findings.

**Acceptance Criteria:**

1. <a name="2.1"></a>The workflow SHALL provide a repeatable local REA MCP setup for the supported local agent clients, with an explicitly selected release, preservation of unrelated configuration, and no registration changes on a converged rerun.  
2. <a name="2.2"></a>The workflow SHALL report MCP connection readiness separately from availability of the source input and the analysis capabilities needed for the requested investigation.  
3. <a name="2.3"></a>WHEN the connected REA tools support the requested inspection, the workflow SHALL use those available capabilities; a missing optional provider SHALL NOT block an inspection that does not need it.  
4. <a name="2.4"></a>IF input or capability is missing, THEN the workflow SHALL record the affected question, the missing prerequisite, and the next supported action; it SHALL retain any supported findings without presenting the blocked inspection as completed.  

### 3. Evidence for the Selected Feature

**User Story:** As a developer, I want findings tied to their sources and limits, so that a plausible explanation does not become an unsupported implementation assumption.

**Acceptance Criteria:**

1. <a name="3.1"></a>For each investigation, the workflow SHALL record the source app identity and available version/platform details, the selected feature, the inputs actually inspected, and the date of observation; unavailable identity fields SHALL remain explicitly unknown.  
2. <a name="3.2"></a>WHEN first recording a finding, the workflow SHALL include a source reference accessible at that time and distinguish observed facts, inferred explanations, and unresolved questions; REA findings SHALL retain their Evidence identity and reported limitations.  
3. <a name="3.3"></a>WHEN an Evidence reference depends on a live REA session, the workflow SHALL preserve the relevant Evidence outside that session or mark it as unavailable; later planning SHALL require the evidence to be recovered or the affected claim to be recorded as an unresolved assumption rather than a verified finding.  
4. <a name="3.4"></a>WHEN inspection stops or returns partial results, the workflow SHALL preserve the findings obtained, identify unanswered parts of the selected question, and avoid treating missing observations as proof that a capability is absent.  

### 4. Feature Adaptation and Starwave Handoff

**User Story:** As a developer, I want evidence translated into a feature that fits my app, so that the destination's needs determine what gets built.

**Acceptance Criteria:**

1. <a name="4.1"></a>The handoff SHALL identify the behaviour the developer wants to adopt, the evidence supporting it, the adaptations required by the destination, and the unresolved questions that affect feasibility or scope.  
2. <a name="4.2"></a>The workflow SHALL route a new feature through Starwave's existing scope assessment, requirements, design, and task-planning stages as applicable, preserving the approval gates of the selected route.  
3. <a name="4.3"></a>WHEN the work extends an existing destination spec, the workflow SHALL continue that spec in place, preserve existing requirement identifiers, and follow the destination's decision-log and downstream-document revision rules.  
4. <a name="4.4"></a>WHEN Starwave produces the implementation plan, its tasks SHALL remain parseable by `rune` and trace to destination requirements; validation SHALL distinguish source-observed behaviour from adaptations chosen for the destination.  
5. <a name="4.5"></a>IF an unresolved question prevents an implementation decision, THEN the handoff SHALL identify that dependency rather than represent the affected work as ready for implementation; unaffected planning MAY continue.  

### 5. Ownership and Continuation

**User Story:** As a developer, I want research and planning kept with the app that uses them, so that another session can continue without relying on this conversation.

**Acceptance Criteria:**

1. <a name="5.1"></a>The workflow SHALL keep reusable process instructions and MCP integration in `agentic-coding`, and app-specific research, decisions, requirements, and tasks in the destination repository.  
2. <a name="5.2"></a>Before completing a handoff, the workflow SHALL save the evidence references, selected destination spec or research location, unresolved prerequisites, next Starwave stage, and any approvals already received in destination-owned documents.  
3. <a name="5.3"></a>WHEN resuming an investigation, the workflow SHALL compare the available source identity and capabilities with the recorded investigation, identify evidence affected by a source change or unavailable reference, and retain unaffected findings.  

### 6. Codification and Validation

**User Story:** As a maintainer, I want this process callable through the existing agent tooling, so that future investigations follow the same evidence and planning rules.

**Acceptance Criteria:**

1. <a name="6.1"></a>The reusable workflow SHALL be discoverable through this repository's existing Agent Skills distribution for its supported local hosts, with instructions for invoking it and recovering from missing REA access.  
2. <a name="6.2"></a>The workflow documentation SHALL explain how REA analysis, MCP DevTools documentation/package research, and Starwave planning contribute to the investigation, without treating any one of them as proof that the others succeeded.  
3. <a name="6.3"></a>Validation SHALL cover an accessible app artifact, an installed-only mobile app with missing inspection input, and continuation of an existing destination spec with an expired-session reference; the examples SHALL verify evidence provenance, ownership, prerequisite handling, and Starwave routing.  

# Bugfix Report: good-bug

**Date:** 2026-07-03
**Status:** Fixed

## Description of the Issue

A well-documented bug.

## Investigation Summary

Traced the failure to the parser.

## Discovered Root Cause

Off-by-one in the tokenizer.

## Resolution for the Issue

Fixed the boundary condition.

## Regression Test

Added tests/test_tokenizer.py::test_boundary.

## Affected Files

- src/tokenizer.py

## Verification

Full suite green.

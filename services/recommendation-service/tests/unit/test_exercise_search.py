"""Unit tests for search_exercises() — CC0 dataset name filtering."""
from __future__ import annotations
import pytest
from src.services.exercise_search import search_exercises


def test_search_returns_matches():
    results = search_exercises("bench")
    assert len(results) > 0
    assert all("bench" in r["name"].lower() for r in results)


def test_search_case_insensitive():
    lower = search_exercises("squat")
    upper = search_exercises("SQUAT")
    mixed = search_exercises("Squat")
    assert len(lower) > 0
    assert {r["name"] for r in lower} == {r["name"] for r in upper} == {r["name"] for r in mixed}


def test_search_no_results():
    results = search_exercises("zzzzxxx")
    assert results == []


def test_search_limit_respected():
    results = search_exercises("press", limit=3)
    assert len(results) <= 3


def test_search_result_shape():
    results = search_exercises("deadlift", limit=1)
    assert len(results) >= 1
    r = results[0]
    assert "name" in r
    assert "primary_muscles" in r
    assert "secondary_muscles" in r
    assert "category" in r
    assert "equipment" in r
    assert "level" in r
    assert isinstance(r["primary_muscles"], list)
    assert isinstance(r["secondary_muscles"], list)

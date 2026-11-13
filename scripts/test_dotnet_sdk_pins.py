#!/usr/bin/env python3
"""Regression tests for SDK pin parsing in Docker image tags."""

from __future__ import annotations

import unittest

from check_dotnet_sdk_pins import docker_sdk_versions


class DockerSdkPinTests(unittest.TestCase):
    def test_distro_suffix_is_not_part_of_sdk_version(self) -> None:
        text = (
            "FROM mcr.microsoft.com/dotnet/sdk:10.0.404-resolute"
            "@sha256:0123456789abcdef AS build"
        )

        self.assertEqual(docker_sdk_versions(text), ["10.0.404"])

    def test_exact_tag_and_digest_are_parsed(self) -> None:
        text = "FROM mcr.microsoft.com/dotnet/sdk:10.0.404@sha256:abcdef"

        self.assertEqual(docker_sdk_versions(text), ["10.0.404"])

    def test_extended_numeric_version_is_not_truncated(self) -> None:
        text = "FROM mcr.microsoft.com/dotnet/sdk:10.0.4040-resolute"

        self.assertEqual(docker_sdk_versions(text), ["10.0.4040"])


if __name__ == "__main__":
    unittest.main()

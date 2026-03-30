import json
import os
import subprocess
from dataclasses import dataclass

PACKAGES = ["opencloud-desktop-bin"]


@dataclass
class PackageInfo:
    name: str
    latest_version: str
    desired_pkgrel: int
    current_pkgver: str
    current_pkgrel: int
    parallel_build: bool = True


def call_pkgupdate(package: str, command: str) -> str:
    res = subprocess.run(
        ["bash", "-lc", f"source ./PKGUPDATE && {command}"],
        check=True,
        capture_output=True,
        text=True,
        cwd=package,
    )
    return res.stdout.strip()


def get_package_info(package: str) -> PackageInfo:
    latest_version = call_pkgupdate(package, "fetch_latest_version")
    parallel_build = call_pkgupdate(package, "can_parallel_build") == "true"

    with open(f"{package}/PKGBUILD", "r") as f:
        pkgbuild = f.readlines()

    # Extract pkgver and pkgrel from PKGBUILD
    pkgver_line = next(line for line in pkgbuild if line.startswith("pkgver="))
    pkgrel_line = next(line for line in pkgbuild if line.startswith("pkgrel="))

    current_version = pkgver_line.split("=")[1].strip()
    current_pkgrel = int(pkgrel_line.split("=")[1].strip())

    return PackageInfo(
        name=package,
        latest_version=latest_version,
        desired_pkgrel=1 if latest_version != current_version else current_pkgrel + 1,
        current_pkgver=current_version,
        current_pkgrel=current_pkgrel,
        parallel_build=parallel_build,
    )


def main():
    force_update = os.environ.get("FORCE_UPDATE") == "true"

    print(f"Force update: {force_update}")

    to_update: list[PackageInfo] = []

    for package in PACKAGES:
        pkg = get_package_info(package)

        print(f"Package: {pkg.name}")
        print(f"  Latest version: {pkg.latest_version}")
        print(f"  Current version: {pkg.current_pkgver}")
        print(f"  Current pkgrel: {pkg.current_pkgrel}")
        print(f"  Desired pkgrel: {pkg.desired_pkgrel}")
        print(
            f"  Will update: {pkg.latest_version != pkg.current_pkgver or force_update}"
        )

        if pkg.latest_version != pkg.current_pkgver or force_update:
            to_update.append(pkg)

    job_matrix: dict[str, list[dict[str, str | int]]] = {
        "include": [
            {
                "name": pkg.name,
                "latest_version": pkg.latest_version,
                "desired_pkgrel": pkg.desired_pkgrel,
                "current_pkgrel": pkg.current_pkgrel,
                "current_version": pkg.current_pkgver,
                "parallel_build": pkg.parallel_build,
            }
            for pkg in to_update
        ]
    }

    if out := os.getenv("GITHUB_OUTPUT"):
        with open(out, "a") as f:
            print(f"is_empty={str(len(job_matrix['include']) == 0).lower()}", file=f)
            print(f"matrix={json.dumps(job_matrix)}", file=f)


if __name__ == "__main__":
    main()

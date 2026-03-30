import os
import json
import subprocess


def update_versions(package: str, version: str, pkgrel: int):
    """Update pkgver and pkgrel in the PKGBUILD file of the given package."""

    pkgbuild_path = os.path.join(package, "PKGBUILD")

    with open(pkgbuild_path, "r") as f:
        pkgbuild = f.readlines()

    found_pkgver = False
    found_pkgrel = False

    for i, line in enumerate(pkgbuild):
        if line.startswith("pkgver="):
            pkgbuild[i] = f"pkgver={version}\n"
            found_pkgver = True
        elif line.startswith("pkgrel="):
            pkgbuild[i] = f"pkgrel={pkgrel}\n"
            found_pkgrel = True

    if not found_pkgver or not found_pkgrel:
        raise ValueError(f"Could not find pkgver or pkgrel in {pkgbuild_path}")

    with open(pkgbuild_path, "w") as f:
        f.writelines(pkgbuild)


def run_updpkgsums(package: str):
    """Run updpkgsums in the given package directory to recalculate the sha256sums array based on the source array."""

    res = subprocess.run(["updpkgsums"], cwd=package, capture_output=True, text=True)

    if res.returncode != 0:
        raise RuntimeError(f"updpkgsums failed for {package}:\n{res.stderr}")


def update_pkgbuild(
    package: str,
    curr_version: str,
    curr_pkgrel: int,
    new_version: str,
    new_pkgrel: int,
):
    """Update the PKGBUILD file of the given package with the new version and pkgrel,
    and recalculate the sha256sums if the version has changed."""
    update_versions(package, new_version, new_pkgrel)

    # Only update SHA sums if the version has changed,
    # otherwise we might end up with incorrect sums if the source files haven't changed
    if curr_version != new_version:
        run_updpkgsums(package)


def main():
    matrix_mode = os.environ.get("MATRIX_MODE") == "true"

    if matrix_mode:
        packages = json.loads(os.environ["PACKAGE_MATRIX"])["include"]

        for pkg in packages:
            update_pkgbuild(
                pkg["name"],
                pkg["current_version"],
                pkg["current_pkgrel"],
                pkg["latest_version"],
                pkg["desired_pkgrel"],
            )
        return

    # Fallback to single package mode
    package = os.environ["PACKAGE_NAME"]
    version = os.environ["LATEST_VERSION"]
    curr_version = os.environ["CURRENT_VERSION"]
    pkgrel = int(os.environ["DESIRED_PKGREL"])
    curr_pkgrel = int(os.environ["CURRENT_PKGREL"])

    update_pkgbuild(package, curr_version, curr_pkgrel, version, pkgrel)


if __name__ == "__main__":
    main()

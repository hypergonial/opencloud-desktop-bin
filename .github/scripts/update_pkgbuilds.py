import os
import json


def update_pkgbuild(package: str, version: str, pkgrel: int):
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


def main():
    packages = json.loads(os.environ["PACKAGE_MATRIX"])["include"]

    for pkg in packages:
        update_pkgbuild(pkg["name"], pkg["latest_version"], pkg["desired_pkgrel"])


if __name__ == "__main__":
    main()

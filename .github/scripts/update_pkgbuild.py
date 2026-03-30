import os
import json
import subprocess


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


def run_updpkgsums(package: str):
    res = subprocess.run(["updpkgsums"], cwd=package, capture_output=True, text=True)

    if res.returncode != 0:
        raise RuntimeError(f"updpkgsums failed for {package}:\n{res.stderr}")


def main():
    matrix_mode = os.environ.get("MATRIX_MODE") == "true"

    if matrix_mode:
        packages = json.loads(os.environ["PACKAGE_MATRIX"])["include"]

        for pkg in packages:
            update_pkgbuild(pkg["name"], pkg["latest_version"], pkg["desired_pkgrel"])
            run_updpkgsums(pkg["name"])
        return

    # Fallback to single package mode
    package = os.environ["PACKAGE_NAME"]
    version = os.environ["LATEST_VERSION"]
    pkgrel = int(os.environ["DESIRED_PKGREL"])

    update_pkgbuild(package, version, pkgrel)
    run_updpkgsums(package)


if __name__ == "__main__":
    main()

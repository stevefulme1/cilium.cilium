"""Nox sessions for stevefulme1.cilium Ansible collection."""

import nox

PYTHON_VERSIONS = ["3.12", "3.13"]


@nox.session(python=PYTHON_VERSIONS)
def lint(session):
    """Run linting checks."""
    session.install("yamllint", "flake8", "ansible-lint", "ansible-core>=2.16")
    session.run("yamllint", "-c", ".yamllint", ".")
    session.run(
        "flake8", "plugins/",
        "--max-line-length=120",
        "--ignore=E402,W503",
    )
    session.run("ansible-lint", "--strict")


@nox.session(python=PYTHON_VERSIONS)
def unit(session):
    """Run unit tests with pytest."""
    session.install("pytest", "pytest-cov", "ansible-core>=2.16", "kubernetes", "grpcio")

    import os
    cwd = os.path.abspath(".")
    namespace_root = os.path.abspath(os.path.join(cwd, os.pardir, os.pardir, os.pardir))
    env = {}
    if os.path.isdir(os.path.join(namespace_root, "ansible_collections")):
        env["PYTHONPATH"] = namespace_root

    session.run(
        "pytest", "tests/unit/",
        "-v",
        "--tb=short",
        "--cov=plugins",
        "--cov-report=term-missing",
        env=env,
    )


@nox.session(python="3.12")
def sanity(session):
    """Run ansible-test sanity."""
    session.install("ansible-core>=2.16")
    session.run(
        "ansible-test", "sanity",
        "--python", "3.12",
        "--color", "yes",
        "-v",
    )

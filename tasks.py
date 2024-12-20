from invoke import task
import os


@task
def install_dependencies(c):
    """
    Install Python dependencies using Poetry.
    """
    c.run("poetry install", pty=True)


@task
def install_ansible_collection(c):
    """
    Build and install the Ansible Galaxy collection.
    """
    galaxy_file = "galaxy.yml"
    if not os.path.exists(galaxy_file):
        raise FileNotFoundError(
            f"{galaxy_file} not found. Ensure it exists in the root directory."
        )

    # Build the collection
    c.run("ansible-galaxy collection build", pty=True)

    # Get the collection tarball name dynamically
    tarball = next((f for f in os.listdir(".") if f.endswith(".tar.gz")), None)
    if not tarball:
        raise FileNotFoundError("No collection tarball (.tar.gz) found after build.")

    # Install the collection
    c.run(f"ansible-galaxy collection install {tarball}", pty=True)


@task(pre=[install_dependencies, install_ansible_collection])
def setup(c):
    """
    Perform full setup: install Python dependencies and Ansible Galaxy collection.
    """
    print("Setup complete. Ready to run tests.")

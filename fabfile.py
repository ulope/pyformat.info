import os

from fabric.colors import yellow, green
from fabric.context_managers import lcd, hide
from fabric.decorators import task, hosts
from pathlib import Path

from fabric.operations import local
from fabric.tasks import execute
from fabric.utils import puts, abort


HERE = Path().resolve()

INSTALL_IGNORE = {'live.txt'}

LEKTOR_PATH = Path("vendor/lektor")
LEKTOR_COMPILED_JS = LEKTOR_PATH.joinpath("/lektor/admin/static/gen/app.js")

PRE_COMMIT_PATH = Path(".git/hooks/pre-commit")
PRE_COMMIT_HASH = "138fd403232d2ddd5efb44317e38bf03"

LOCAL_DEPS = [
    "vendor/lektor"
]


def _pre_check():
    if 'VIRTUAL_ENV' not in os.environ:
        abort('No active virtualenv found. Please create / activate one before continuing.')
    try:
        import piptools  # noqa
    except ImportError:
        with hide('running', 'stdout'):
            puts(yellow("Installing 'pip-tools'"), show_prefix=True)
            local("pip install pip-tools")


def _post_check():
    with hide('running', 'stdout'):
        if (
            not PRE_COMMIT_PATH.exists()
            or PRE_COMMIT_HASH not in PRE_COMMIT_PATH.read_text()
        ):
            puts(yellow("Installing 'pre-commit' utility"), show_prefix=True)
            local("pre-commit install")
        if not LEKTOR_COMPILED_JS.exists():
            puts(yellow("Compiling lektor static assets"), show_prefix=True)
            with lcd(str(LEKTOR_PATH)):
                local("make build-js")


def _fix_local_deps():
    # Workaround for https://github.com/jazzband/pip-tools/issues/204
    generated_path = Path("requirements.txt")
    new_path = Path("requirements.txt.new")
    # Grml `with` doesn't support parens for line continuation
    # http://bugs.python.org/issue12782
    with generated_path.open("r", encoding="UTF-8") as generated, \
            new_path.open("w", encoding="UTF-8") as new:
        for line in generated:
            line = line.rstrip()
            for local_dep in LOCAL_DEPS:
                if local_dep in line:
                    dep_path = Path(
                        line.partition(" ")[2].replace("file://", ""))
                    line = f"-e ./{dep_path.relative_to(HERE)}"
            new.write(f"{line}\n")
    new_path.rename(generated_path)


@task()
@hosts('localhost')
def compile(upgrade=False):
    """Update list of requirements"""
    _pre_check()
    if upgrade:
        msg = "Upgrading requirements"
    else:
        msg = "Updating requirements"
    with lcd(str(HERE)):
        with hide('running', 'stdout'):
            puts(green(msg), show_prefix=True)
            if upgrade:
                upgrade = "--upgrade --rebuild"
            else:
                upgrade = ""
            local(f"pip-compile --no-index {upgrade} requirements.in")
        _fix_local_deps()


@task(default=True)
@hosts('localhost')
def sync():
    """Ensure installed packages match requirements"""
    _pre_check()
    with hide('running', 'stdout'), lcd(str(HERE)):
        puts(green("Syncing local packages to requirements"), show_prefix=True)
        local('pip-sync requirements.txt')
    _post_check()


@task
def upgrade():
    """Compile (with upgrade) then sync requirements"""
    execute(compile, True)
    execute(sync)

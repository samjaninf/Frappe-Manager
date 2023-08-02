import typer
from typing import Annotated, List, Optional, Set
from pathlib import Path
from fm.site_manager.manager import SiteManager
import os
import requests

app = typer.Typer()

# TODO configure this using config
#sites_dir = Path() / __name__.split(".")[0]

sites_dir= Path.home() / __name__.split('.')[0]
sites = SiteManager(sites_dir)

default_extension = [
    "ms-python.python",
    "ms-python.black-formatter",
    "esbenp.prettier-vscode",
    "visualstudioexptteam.vscodeintellicode",
]
def check_frappe_app_exists(appname:str,branchname:str | None = None):

    # check appname
    app_url = f'https://github.com/frappe/{appname}'
    app = requests.get(app_url).status_code

    if branchname:
        branch_url = f'https://github.com/frappe/{appname}/tree/{branchname}'
        # check branch
        branch = requests.get(branch_url).status_code
        return {'app': True if app == 200 else False,'branch': True if branch == 200 else False}

    return {'app': True if app == 200 else False}



def apps_validation(value: List[str] | None):
    # don't allow frappe the be included throw error
    if value:
        for app in value:
            appx = app.split(':')
            if appx == 'frappe':
                raise typer.BadParameter("Frappe should not be included here.")
            if len(appx) == 1:
                exists = check_frappe_app_exists(appx[0])
                if not exists['app']:
                    raise typer.BadParameter(f"{app} is not a valid FrappeVerse app!")
            if len(appx) == 2:
                exists = check_frappe_app_exists(appx[0],appx[1])
                if not exists['app']:
                    raise typer.BadParameter(f"{app} is not a valid FrappeVerse app!")
                if not exists['branch']:
                    raise typer.BadParameter(f"{appx[1]} is not a valid branch of {appx[0]}!")
            if len(appx) > 2:
                raise typer.BadParameter(f"App should be specified in format <appname>:<branch> or <appname> ")
    return value


@app.command()
def create(
    sitename: Annotated[str, typer.Argument(help="Name of the site")],
    apps: Annotated[
        Optional[List[str]], typer.Option("--apps", "-a", help="Frappe apps to install",callback=apps_validation)
    ] = None,
    developer_mode: Annotated[bool, typer.Option(help="Enable developer mode")] = True,
    frappe_branch: Annotated[
        str, typer.Option(help="Specify the branch name for frappe app")
    ] = "version-14",
    admin_pass: Annotated[
        str,
        typer.Option(
            help="Default Password for the standard 'Administrator' User. This will be used as the password for the Administrator User for all new sites"
        ),
    ] = "admin",
    enable_ssl: Annotated[bool, typer.Option(help="Enable https")] = False,
):
    """Create a new site."""

    sites.init(sitename,createdir=True)

    uid: int = os.getuid()
    gid: int = os.getgid()

    # apps list as appname:version-14
    # TODO add validation for branch name

    frappe_env: dict = {
        "USERID": uid,
        "USERGROUP": gid,
        "APPS_LIST": ",".join(apps) if apps else None,
        "FRAPPE_BRANCH": frappe_branch,
        "DEVELOPER_MODE": developer_mode,
        "ADMIN_PASS": admin_pass,
        "DB_NAME": sites.site.name.replace(".", "-"),
        "SITENAME": sites.site.name,
    }

    print(frappe_env)
    nginx_env: dict = {
        "ENABLE_SSL": enable_ssl,
        "SITENAME": sites.site.name,
    }

    extra_hosts: List[str] = [f"{sitename}:127.0.0.1"]

    template_inputs: dict = {
        "frappe_env": frappe_env,
        "nginx_env": nginx_env,
        "extra_hosts": extra_hosts,
    }
    # turn off all previous
    # start the docker compose
    sites.create_site(template_inputs)


@app.command()
def delete(sitename: Annotated[str, typer.Argument(help="Name of the site")]):
    """Delete a site."""
    sites.init(sitename)
    # turn off the site
    sites.remove_site()


@app.command()
def list():
    """Lists all of the available sites."""
    sites.init()
    sites.list_sites()
    # for site in sites.keys():
    # console.print(f"[bold green] {site} [/bold green] -> [bold cyan] {sites[site]}[/bold cyan]")


@app.command()
def start(sitename: Annotated[str, typer.Argument(help="Name of the site")]):
    """Start a site."""
    sites.init(sitename)
    sites.start_site()


@app.command()
def stop(sitename: Annotated[str, typer.Argument(help="Name of the site")]):
    """Stop a site."""
    sites.init(sitename)
    sites.stop_site()


def code_callback(extensions: List[str]) -> List[str]:
    extx = extensions + default_extension
    unique_ext: Set = set(extx)
    unique_ext_list: List[str] = [x for x in unique_ext]
    return unique_ext_list


@app.command()
def code(
    sitename: Annotated[str, typer.Argument(help="Name of the site.")],
    user: Annotated[str, typer.Option(help="Connect as this user.")] = "frappe",
    extensions: Annotated[
        Optional[List[str]],
        typer.Option(
            "--extension",
            "-e",
            help="List of extensions to install in vscode at startup.",
            callback=code_callback,
        ),
    ] = default_extension,
):
    """Open site in vscode."""
    # check if vscode is installed
    # Attach to container
    # cmd: -> code --folder-uri=vscode-remote://attached-container+(contianer name hex)+/workspace
    # LABELS can be added to container to support extensions and remote user
    # check if configuration can be given
    sites.init(sitename)
    sites.attach_to_site(user, extensions)
    # sites.attach_to_site()

@app.command()
def logs(
    sitename: Annotated[str, typer.Argument(help="Name of the site.")],
    service: Annotated[str, typer.Option(help="Specify Service")] = 'frappe',
):
    sites.init(sitename)
    sites.logs(service)

@app.command()
def shell(
    sitename: Annotated[str, typer.Argument(help="Name of the site.")],
    user: Annotated[str, typer.Option(help="Connect as this user.")] = None,
    service: Annotated[str, typer.Option(help="Specify Service")] = 'frappe',
):
    sites.init(sitename)
    sites.shell(service,user)

def config():
    pass
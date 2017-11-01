from __future__ import print_function

import logging

from harborclient import exceptions as exp
from harborclient.i18n import _
from harborclient import utils

logger = logging.getLogger(__name__)


# /login
@utils.arg(
    '--username',
    metavar='<username>',
    dest='username',
    required=True,
    help=_('Username.'), )
@utils.arg(
    '--password',
    metavar='<password>',
    dest='password',
    required=True,
    help=_('Password.'), )
def do_login(cs, args):
    """Login and return the session id. """
    resp = cs.users.login(args.username, args.password, cs.baseurl)
    if resp.status_code == 200:
        print("Successfully login, session id: %s" %
              resp.cookies.get('beegosessionID'))
    else:
        print("Failed to login! Please re-check your username and password")


@utils.arg(
    '--sortby',
    metavar='<sortby>',
    dest="sortby",
    default="user_id",
    help=_('Sort key.'))
# /users
def do_user_list(cs, args):
    """Print a list of available 'users'."""
    _, users = cs.users.list()
    fields = ['user_id', 'username', 'email', 'realname', 'comment']
    utils.print_list(users, fields, sortby=args.sortby)


@utils.arg('user', metavar='<user>', help=_('ID or name of user.'))
def do_user_show(cs, args):
    """Show details about the given user."""
    key = args.user
    if cs.users.is_id(key):
        id = key
    else:
        id = cs.users.get_id_by_name(key)
    _, user = cs.users.get(id)
    utils.print_dict(user)


@utils.arg(
    '--username',
    metavar='<username>',
    dest='username',
    required=True,
    help=_('Unique name of the new user'), )
@utils.arg(
    '--password',
    metavar='<password>',
    dest='password',
    required=True,
    help=_('Password of the new user'), )
@utils.arg(
    '--email',
    metavar='<email>',
    dest='email',
    required=True,
    help=_('Email of the new user'), )
@utils.arg(
    '--realname',
    metavar='<realname>',
    dest='realname',
    default=None,
    help=_('Email of the new user'), )
@utils.arg(
    '--comment',
    metavar='<comment>',
    dest='comment',
    default=None,
    help=_('Comment of the new user'), )
def do_user_create(cs, args):
    """Create a new User. """
    cs.users.create(args.username, args.password, args.email, args.realname,
                    args.comment)
    print("Create user '%s' successfully." % args.username)


@utils.arg('user', metavar='<user>', help=_('ID or name of user.'))
def do_user_delete(cs, args):
    """Delete an user """
    key = args.user
    if cs.users.is_id(key):
        id = key
    else:
        id = cs.users.get_id_by_name(key)
    cs.users.delete(id)
    print("Delete user '%s' sucessfully." % key)


# /projects
@utils.arg(
    '--sortby',
    metavar='<sortby>',
    dest="sortby",
    default="project_id",
    help=_('Sort key.'))
def do_project_list(cs, args):
    """Print a list of available 'projects'."""
    _, projects = cs.projects.list()
    fields = [
        'project_id',
        'name',
        'owner_id',
        'current_user_role_id',
        'repo_count',
        'creation_time',
        'public',
    ]
    utils.print_list(projects, fields, formatters={}, sortby=args.sortby)


@utils.arg('project', metavar='<project>', help=_('ID or name of project.'))
def do_project_show(cs, args):
    """Show details about the given project."""
    key = args.project
    if cs.projects.is_id(key):
        project_id = key
    else:
        project_id = cs.projects.get_id_by_name(key)
    _, projects = cs.projects.list()
    for project in projects:
        if str(project['project_id']) == str(project_id):
            utils.print_dict(project)
            return
    raise exp.ProjectNotFound("Project '%s' not found" % args.project)


@utils.arg('project', metavar='<project>', help=_('ID or name of project.'))
def do_project_delete(cs, args):
    """Delete the given project."""
    key = args.project
    if cs.projects.is_id(key):
        id = key
    else:
        id = cs.projects.get_id_by_name(key)
    cs.projects.delete(id)
    print("Delete Project '%s' successfully." % key)


def do_project_update(cs, args):
    """Update the given project. """
    raise NotImplementedError


@utils.arg(
    '--project-id',
    '-p',
    dest='project_id',
    metavar='<project_id>',
    default=None,
    help=_('ID of project.'))
@utils.arg(
    '--sortby',
    dest='sortby',
    metavar='<sortby>',
    default='Id',
    help=_('Sort key.'))
def do_list(cs, args):
    """Print a list of available 'repositories'."""
    data = []
    project_id = args.project_id
    if not project_id:
        project_id = cs.client.project
    _, repositories = cs.repositories.list(project_id)
    for repo in repositories:
        _, tags = cs.repositories.list_tags(repo['name'])
        for tag in tags:
            _, manifest = cs.repositories.get_manifests(repo['name'],
                                                        tag['name'])
            size = 0
            for layer in manifest['manifest']['layers']:
                size += layer['size']
            repo['size'] = size
            if tag['name'] != 'latest':
                repo['name'] = repo['name'] + ":" + tag['name']
            data.append(repo)
    fields = [
        "id", "name", 'project_id', 'size',
        "tags_count", "star_count", "pull_count",
        "update_time"
    ]
    utils.print_list(data, fields, sortby=args.sortby)


@utils.arg('repository', metavar='<repository>', help=_('Name of repository.'))
def do_list_tags(cs, args):
    """Get tags of a relevant repository."""
    resp, tags = cs.repositories.list_tags(args.repository)
    fields = ["name", 'author', 'architecture',
              'os', 'docker_version', 'created']
    utils.print_list(tags, fields, sortby="name")


@utils.arg(
    '--project-id',
    '-p',
    dest='project_id',
    metavar='<project_id>',
    default=None,
    help=_('ID of project.'))
@utils.arg(
    'repository',
    metavar='<repository>',
    help=_("Repository name, for example: int32bit/ubuntu:14.04."))
def do_show(cs, args):
    """Show details about the given repository. """
    project = args.project_id
    if not project:
        project = cs.client.project
    repo = args.repository
    tag_index = repo.find(':')
    if tag_index != -1:
        tag = repo[tag_index + 1:]
        repo = repo[:tag_index]
    else:
        tag = "latest"
    if repo.find('/') == -1:
        repo = "library/" + repo
    _, repos = cs.repositories.list(project)
    found_repo = None
    for r in repos:
        if r['name'] == repo:
            found_repo = r
            break
    if not found_repo:
        print("Image '%s' not found." % repo)
        return
    _, tags = cs.repositories.list_tags(found_repo['name'])
    found_tag = None
    for t in tags:
        if t['name'] == tag:
            found_tag = t
            break
    if not found_tag:
        print("Image '%s' with tag '%s' not found." % (repo, tag))
        return
    for key in found_tag:
        found_repo['tag_' + key] = found_tag[key]
    utils.print_dict(found_repo)


@utils.arg(
    '--count',
    '-c',
    metavar='<count>',
    dest='count',
    default=5,
    help=_('Count.'), )
def do_top(cs, args):
    """Get top accessed repositories. """
    resp, data = cs.repositories.get_top(args.count)
    utils.print_list(data,
                     ['name', 'pull_count', 'star_count'],
                     sortby='pull_count')


# /search
@utils.arg(
    'query',
    metavar='<query>',
    help=_('Search parameter for project and repository name..'))
def do_search(cs, args):
    """Search for projects and repositories """
    resp, data = cs.searcher.search(args.query)
    project_fields = ['id', 'name', 'public']
    print("Find %d Projects: " % len(data['project']))
    utils.print_list(
        data['project'], project_fields, formatters={}, sortby='id')
    repository_fields = [
        'repository_name', 'project_name', 'project_id', 'project_public'
    ]
    print("\n")
    print("Find %d Repositories: " % len(data['repository']))
    utils.print_list(
        data['repository'],
        repository_fields,
        formatters={},
        sortby='repository_name')


# /statistics
def do_info(cs, args):
    """Get statistics data. """
    _, data = cs.statistics.list()
    utils.print_dict(data)


# /logs
@utils.arg(
    '--sortby',
    dest='sortby',
    metavar='<sortby>',
    default='op_time',
    help=_('Sort key.'))
def do_logs(cs, args):
    """Get logs. """
    _, logs = cs.logs.list()
    for log in logs:
        repo = log['repo_name']
        tag = None
        if log['repo_tag'] != 'N/A':
            tag = log['repo_tag']
        if tag:
            repo += ":%s" % tag
        log['repository'] = repo
    fields = ['log_id', 'op_time', 'username',
              'project_id', 'operation', 'repository']
    utils.print_list(logs, fields, sortby=args.sortby)

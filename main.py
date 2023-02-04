import functions_framework
import requests
import re
import os
import hmac
import hashlib


TEMPLATE_ISSUE = """
|Field| Value |
|--|--|
| Build type | {build_type} |
| Pojav version | {pojav_version} |
| Minecraft version | {minecraft_version} |
| Renderer | {renderer} |
| Architecture | {architecture} |
| Java runtime | {java_runtime} |
| Java arguments | {java_arguments} |

"""

TEMPLATE_ERROR_HEADER = """
|Errors Found: |
|--|
"""

TEMPLATE_ERROR_ROW = "| {error} |\n"


def get_latestlog_file(comment_body: str) -> str:
    latestlog_link = re.search(r'https://github\.com/PojavLauncherTeam/PojavLauncher/files/.*?/latestlog\.txt', comment_body)
    if not latestlog_link:
        return ""
    log_file = requests.get(latestlog_link.group(0)).text
    return log_file


def validate_signature(request):
    """
        HTTP Cloud Function that declares a variable.
        Args:
            request (flask.Request): The request object.
            <https://flask.palletsprojects.com/en/latest/api/>
    """
    env_value = os.getenv('PRIVATE_HASH_KEY', '')
    if not env_value:
        print("Warning: no private key has been set, accepting all requests !")
        return True

    key = bytes(env_value, 'utf-8')
    expected_signature = hmac.new(key=key, msg=request.data, digestmod=hashlib.sha1).hexdigest()
    incoming_signature = request.headers.get('X-Hub-Signature').split('sha1=')[-1].strip()
    if not hmac.compare_digest(incoming_signature, expected_signature):
        return False
    return True


def build_info_comment(parsed_json: dict) -> str:
    pojav_version = parsed_json['version']
    mc_version = parsed_json['minecraft_version']
    java_runtime = parsed_json['java_runtime']
    return TEMPLATE_ISSUE.format(
        build_type=parsed_json['build_type'],
        pojav_version="{} - {} - {}".format(pojav_version['major_code'], pojav_version['commit_number'], pojav_version['branch']),
        minecraft_version="{} - {}".format(mc_version['name'], mc_version['type']),
        renderer="{}".format(parsed_json['renderer']),
        architecture='{}'.format(parsed_json['architecture']),
        java_runtime='{} - {} - {}'.format(java_runtime['source'], java_runtime['type'], java_runtime['version']),
        java_arguments=parsed_json['java_arguments']
    )


def build_error_comment(errors: list[str]) -> str:
    if not errors:
        return ""

    final_string = ""
    for error in errors:
        final_string += TEMPLATE_ERROR_ROW.format(error=error)

    return TEMPLATE_ERROR_HEADER + final_string


def build_response_comment(parsed_json: dict):
    return build_info_comment(parsed_json) + '\n' + build_error_comment(parsed_json['errors'])


@functions_framework.http
def handle_request(request):
    """
        HTTP Cloud Function that declares a variable.
        Args:
            request (flask.Request): The request object.
            <https://flask.palletsprojects.com/en/latest/api/>
        Returns:
            The response text, or any set of values that can be turned into a
            Response object using `make_response`
            <https://flask.palletsprojects.com/en/latest/api/>.
        """
    # Make sure the request came from Github
    if not validate_signature(request):
        return {}, 401

    data = request.json
    body = data['comment']['body']

    # get the log file
    log_content = get_latestlog_file(body)

    # Send it to the parser
    response_parser = requests.post('https://pojav-parser-function-3tx4ib7zya-uw.a.run.app', data=log_content)
    response_parser.raise_for_status()
    parser_json = response_parser.json()

    comment_json = {"body": build_response_comment(parser_json)}
    token = "Bearer {}".format(os.environ.get('TOKEN_GITHUB'))
    comment_response = requests.post(data['issue']['comments_url'], headers={'Authorization': token}, json=comment_json)
    comment_response.raise_for_status()

    return {}

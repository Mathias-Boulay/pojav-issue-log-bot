import functions_framework
import requests
import re
import os
import hmac
import hashlib


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


def build_response_comment(parsed_json: dict) -> str:
    comment_content = "**Pojav version:** {0}-{1}-{2}-{3}\n\r".format(
        parsed_json['version']['major_code'], parsed_json['version']['commit_number'],
        parsed_json['version']['commit_short'], parsed_json['version']['branch'])
    comment_content += "**Architecture:** {}\n\r".format(parsed_json.get('architecture'))
    comment_content += "**Renderer:** {}\n\r".format(parsed_json['renderer'])
    comment_content += "**Minecraft version:** {0} - Type:{1}\n\r".format(
        parsed_json['minecraft_version']['name'], parsed_json['minecraft_version']['type'])
    comment_content += "**Java version:** {0} {1} {2}\n\r".format(
        parsed_json['java_runtime']['source'], parsed_json['java_runtime']['type'],
        parsed_json['java_runtime']['version'])
    comment_content += "**Errors detected:** \n\r"
    for error in parsed_json['errors']:
        comment_content += "\t{0}\n\r".format(error)

    print(comment_content)
    return comment_content


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
